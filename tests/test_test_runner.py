import json
import os
import pathlib
import tempfile
import unittest
from unittest import mock

from scripts.test_runner import (
    TestDecision,
    build_report,
    classify_changes,
    discover_changed_files,
    normalize_paths,
    write_reports,
)


class ChangeClassificationTests(unittest.TestCase):
    def test_hidden_directory_prefixes_are_preserved(self):
        paths = normalize_paths(["./.claude/skills/demo/SKILL.md", ".github/workflows/ci.yml"])

        self.assertEqual(
            (".claude/skills/demo/SKILL.md", ".github/workflows/ci.yml"), paths
        )

    def test_documentation_only_change_skips_unit_tests(self):
        decision = classify_changes(["README.md", "docs/guide.md", "CHANGELOG.md"])

        self.assertEqual("structural", decision.tier)
        self.assertFalse(decision.run_unit)
        self.assertFalse(decision.recommend_agent_eval)

    def test_skill_source_change_runs_unit_tests(self):
        decision = classify_changes([".claude/skills/dev-pipeline/SKILL.md"])

        self.assertEqual("unit", decision.tier)
        self.assertTrue(decision.run_unit)

    def test_review_rule_change_recommends_agent_eval_without_enabling_it(self):
        decision = classify_changes(
            [".claude/skills/dev-pipeline/references/review-checklist.md"]
        )

        self.assertEqual("agent-eval", decision.tier)
        self.assertTrue(decision.run_unit)
        self.assertTrue(decision.recommend_agent_eval)
        self.assertFalse(decision.run_agent_eval)

    def test_unknown_change_defaults_to_unit_tests(self):
        decision = classify_changes(["new-tooling.conf"])

        self.assertEqual("unit", decision.tier)
        self.assertTrue(decision.run_unit)

    def test_ci_base_sha_is_used_for_committed_pull_request_changes(self):
        completed = [
            mock.Mock(stdout="README.md\n"),
            mock.Mock(stdout=""),
            mock.Mock(stdout=""),
        ]
        with mock.patch.dict(os.environ, {"TEST_BASE_SHA": "base123"}), mock.patch(
            "scripts.test_runner.subprocess.run", side_effect=completed
        ) as run:
            changed = discover_changed_files()

        self.assertEqual(("README.md",), changed)
        self.assertEqual(
            ["git", "diff", "base123...HEAD", "--name-only"],
            run.call_args_list[0].args[0],
        )


class ReportTests(unittest.TestCase):
    def test_report_contains_execution_coverage_cost_and_decision_dimensions(self):
        decision = TestDecision(
            tier="unit",
            run_unit=True,
            recommend_agent_eval=False,
            run_agent_eval=False,
            reasons=("skill source changed",),
            changed_files=(".claude/skills/dev-pipeline/SKILL.md",),
        )
        report = build_report(
            decision=decision,
            test_results={
                "total": 4,
                "passed": 4,
                "failures": 0,
                "errors": 0,
                "skipped": 0,
                "duration_seconds": 0.1,
                "passed_test_ids": ["tests.test_repository.example"],
            },
            manifest={
                "requirements": [
                    {
                        "id": "repo-routing",
                        "dimension": "repository-routing",
                        "tests": ["tests.test_repository.example"],
                    }
                ]
            },
        )

        self.assertEqual(100.0, report["execution"]["pass_rate_percent"])
        self.assertEqual(100.0, report["coverage"]["requirement_percent"])
        self.assertEqual(100.0, report["coverage"]["scenario_percent"])
        self.assertEqual(0, report["cost"]["agent_eval_tokens_used"])
        self.assertEqual("unit", report["decision"]["tier"])

    def test_report_writers_create_json_and_markdown(self):
        report = {
            "decision": {"tier": "structural"},
            "execution": {"total": 0, "passed": 0, "pass_rate_percent": 100.0},
            "coverage": {"requirement_percent": 100.0, "scenario_percent": 100.0},
            "cost": {"agent_eval_tokens_used": 0},
        }

        with tempfile.TemporaryDirectory() as directory:
            json_path, markdown_path = write_reports(report, pathlib.Path(directory))

            self.assertEqual(report, json.loads(json_path.read_text(encoding="utf-8")))
            markdown = markdown_path.read_text(encoding="utf-8")
            self.assertIn("Test Report", markdown)
            self.assertIn("Requirement coverage", markdown)


if __name__ == "__main__":
    unittest.main()
