#!/usr/bin/env python3
"""Dependency-free, change-aware test runner for the skill repository."""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import pathlib
import subprocess
import sys
import time
import unittest
from collections import defaultdict
from typing import Any, Iterable


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "tests" / "coverage_manifest.json"
DEFAULT_REPORT_DIR = ROOT / "artifacts" / "test-results"


@dataclasses.dataclass(frozen=True)
class TestDecision:
    tier: str
    run_unit: bool
    recommend_agent_eval: bool
    run_agent_eval: bool
    reasons: tuple[str, ...]
    changed_files: tuple[str, ...]


def normalize_paths(files: Iterable[str]) -> tuple[str, ...]:
    normalized: set[str] = set()
    for raw_path in files:
        if not raw_path:
            continue
        path = raw_path.replace("\\", "/")
        if path.startswith("./"):
            path = path[2:]
        normalized.add(path)
    return tuple(sorted(normalized))


def classify_changes(files: Iterable[str]) -> TestDecision:
    """Choose the cheapest safe test tier for the supplied working-tree changes."""
    changed = normalize_paths(files)
    if not changed:
        return TestDecision(
            tier="unit",
            run_unit=True,
            recommend_agent_eval=False,
            run_agent_eval=False,
            reasons=("no change list supplied; use the conservative unit-test default",),
            changed_files=changed,
        )

    review_sensitive = any(
        path.startswith("evals/")
        or path.endswith("references/review-agents.md")
        or path.endswith("references/review-checklist.md")
        for path in changed
    )
    if review_sensitive:
        return TestDecision(
            tier="agent-eval",
            run_unit=True,
            recommend_agent_eval=True,
            run_agent_eval=False,
            reasons=(
                "review behavior changed; run deterministic tests and recommend opt-in Agent evaluation",
            ),
            changed_files=changed,
        )

    docs_only = all(
        path.startswith("docs/")
        or path.startswith("README")
        or path in {"CHANGELOG.md", "LICENSE"}
        for path in changed
    )
    if docs_only:
        return TestDecision(
            tier="structural",
            run_unit=False,
            recommend_agent_eval=False,
            run_agent_eval=False,
            reasons=("documentation-only change; structural validation is sufficient",),
            changed_files=changed,
        )

    return TestDecision(
        tier="unit",
        run_unit=True,
        recommend_agent_eval=False,
        run_agent_eval=False,
        reasons=("skill, test, CI, package, or unknown behavior-affecting file changed",),
        changed_files=changed,
    )


def discover_changed_files() -> tuple[str, ...]:
    """Read index/working-tree changes only; Git stash is intentionally untouched."""
    base_sha = os.environ.get("TEST_BASE_SHA", "").strip()
    committed_range = f"{base_sha}...HEAD" if base_sha and set(base_sha) != {"0"} else "HEAD"
    committed = subprocess.run(
        ["git", "diff", committed_range, "--name-only"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    working_tree = []
    if committed_range != "HEAD":
        working_tree = subprocess.run(
            ["git", "diff", "HEAD", "--name-only"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    return normalize_paths([*committed, *working_tree, *untracked])


class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.passed_test_ids: list[str] = []

    def addSuccess(self, test: unittest.case.TestCase) -> None:  # noqa: N802
        super().addSuccess(test)
        self.passed_test_ids.append(test.id())


def run_unit_tests(verbosity: int = 2) -> dict[str, Any]:
    root_string = str(ROOT)
    if root_string not in sys.path:
        sys.path.insert(0, root_string)
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    started = time.perf_counter()
    runner = unittest.TextTestRunner(resultclass=RecordingResult, verbosity=verbosity)
    result = runner.run(suite)
    duration = time.perf_counter() - started
    failed = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    passed = result.testsRun - failed - errors - skipped
    return {
        "total": result.testsRun,
        "passed": passed,
        "failures": failed,
        "errors": errors,
        "skipped": skipped,
        "duration_seconds": round(duration, 3),
        "passed_test_ids": result.passed_test_ids,
    }


def _test_matches(passed_ids: Iterable[str], expected: str) -> bool:
    return any(test_id == expected or test_id.endswith(expected) for test_id in passed_ids)


def build_report(
    decision: TestDecision,
    test_results: dict[str, Any],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    total = int(test_results.get("total", 0))
    passed = int(test_results.get("passed", 0))
    failures = int(test_results.get("failures", 0))
    errors = int(test_results.get("errors", 0))
    skipped = int(test_results.get("skipped", 0))
    pass_rate = 100.0 if total == 0 else round(passed * 100 / total, 2)
    passed_ids = test_results.get("passed_test_ids", [])

    requirements = [
        requirement
        for requirement in manifest.get("requirements", [])
        if decision.tier in requirement.get("tiers", ["unit", "agent-eval"])
    ]
    covered_requirements = [
        requirement
        for requirement in requirements
        if requirement.get("tests")
        and all(_test_matches(passed_ids, test_id) for test_id in requirement["tests"])
    ]
    requirement_percent = (
        100.0
        if not requirements
        else round(len(covered_requirements) * 100 / len(requirements), 2)
    )

    dimensions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for requirement in requirements:
        dimensions[requirement["dimension"]].append(requirement)
    covered_ids = {item["id"] for item in covered_requirements}
    covered_dimensions = [
        dimension
        for dimension, items in dimensions.items()
        if all(item["id"] in covered_ids for item in items)
    ]
    scenario_percent = (
        100.0
        if not dimensions
        else round(len(covered_dimensions) * 100 / len(dimensions), 2)
    )

    return {
        "decision": {
            "tier": decision.tier,
            "run_unit": decision.run_unit,
            "recommend_agent_eval": decision.recommend_agent_eval,
            "run_agent_eval": decision.run_agent_eval,
            "reasons": list(decision.reasons),
            "changed_files": list(decision.changed_files),
        },
        "execution": {
            "total": total,
            "passed": passed,
            "failures": failures,
            "errors": errors,
            "skipped": skipped,
            "pass_rate_percent": pass_rate,
            "duration_seconds": test_results.get("duration_seconds", 0.0),
        },
        "coverage": {
            "model": "behavioral-requirements",
            "requirements_total": len(requirements),
            "requirements_covered": len(covered_requirements),
            "requirement_percent": requirement_percent,
            "scenarios_total": len(dimensions),
            "scenarios_covered": len(covered_dimensions),
            "scenario_percent": scenario_percent,
            "covered_requirement_ids": sorted(covered_ids),
        },
        "cost": {
            "agent_eval_executed": decision.run_agent_eval,
            "agent_eval_tokens_used": 0,
            "note": "Agent evaluation is opt-in; deterministic CI consumes no model tokens.",
        },
    }


def _markdown_report(report: dict[str, Any]) -> str:
    decision = report["decision"]
    execution = report["execution"]
    coverage = report["coverage"]
    cost = report["cost"]
    return "\n".join(
        [
            "# Test Report",
            "",
            f"- Decision tier: **{decision['tier']}**",
            f"- Unit tests: **{'run' if decision.get('run_unit') else 'skipped'}**",
            f"- Agent evaluation: **{'run' if cost.get('agent_eval_executed') else 'not run'}**",
            f"- Tests: **{execution.get('passed', 0)}/{execution.get('total', 0)} passed**",
            f"- Pass rate: **{execution.get('pass_rate_percent', 100.0)}%**",
            f"- Requirement coverage: **{coverage.get('requirement_percent', 100.0)}%**",
            f"- Scenario coverage: **{coverage.get('scenario_percent', 100.0)}%**",
            f"- Duration: **{execution.get('duration_seconds', 0.0)}s**",
            f"- Agent-eval tokens: **{cost.get('agent_eval_tokens_used', 0)}**",
            "",
        ]
    )


def write_reports(
    report: dict[str, Any], report_dir: pathlib.Path
) -> tuple[pathlib.Path, pathlib.Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "test-report.json"
    markdown_path = report_dir / "test-report.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    markdown = _markdown_report(report)
    markdown_path.write_text(markdown, encoding="utf-8")
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with pathlib.Path(summary_path).open("a", encoding="utf-8") as summary:
            summary.write(markdown)
    return json_path, markdown_path


def load_manifest(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--all", action="store_true", help="Run unit tests regardless of changes")
    parser.add_argument("--report-dir", type=pathlib.Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    changed_files = args.changed_file or discover_changed_files()
    decision = classify_changes(changed_files)
    if args.all and not decision.run_unit:
        decision = dataclasses.replace(
            decision,
            tier="unit",
            run_unit=True,
            reasons=(*decision.reasons, "--all forced deterministic unit tests"),
        )
    results = (
        run_unit_tests(verbosity=0 if args.quiet else 2)
        if decision.run_unit
        else {
            "total": 0,
            "passed": 0,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "duration_seconds": 0.0,
            "passed_test_ids": [],
        }
    )
    report = build_report(decision, results, load_manifest(args.manifest))
    json_path, markdown_path = write_reports(report, args.report_dir)
    print(_markdown_report(report), end="")
    print(f"Reports: {json_path} | {markdown_path}")
    return 1 if results["failures"] or results["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
