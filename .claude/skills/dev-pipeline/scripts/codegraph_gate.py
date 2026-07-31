#!/usr/bin/env python3
"""Emit read-only, repository-scoped CodeGraph gate evidence as JSON."""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
from typing import Any


def command_text(command: list[str]) -> str:
    return subprocess.list2cmdline(command)


def run(
    command: list[str], root: pathlib.Path, input_text: str | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=root,
        input=input_text,
        capture_output=True,
        text=True,
        check=False,
    )


def execution_record(
    command: list[str], result: subprocess.CompletedProcess[str]
) -> dict[str, Any]:
    return {
        "command": command_text(command),
        "exit_code": result.returncode,
        "stderr": result.stderr.strip(),
    }


def find_backend(value: Any) -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() == "backend" and isinstance(child, str):
                return child.lower()
            backend = find_backend(child)
            if backend:
                return backend
    if isinstance(value, list):
        for child in value:
            backend = find_backend(child)
            if backend:
                return backend
    return None


def extract_paths(value: Any) -> list[str]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    if isinstance(value, dict):
        for key in ("tests", "files", "affected", "results"):
            paths = extract_paths(value.get(key))
            if paths:
                return paths
    return []


def status_gate(root: pathlib.Path) -> tuple[dict[str, Any], str | None]:
    record: dict[str, Any] = {
        "repository": str(root),
        "index_root": str(root / ".codegraph"),
        "available": False,
        "reason": None,
        "backend": None,
        "warnings": [],
    }
    index = root / ".codegraph" / "codegraph.db"
    if not index.is_file():
        record["reason"] = "index-missing"
        return record, None

    executable = shutil.which("codegraph")
    if not executable:
        record["reason"] = "cli-missing"
        return record, None

    command = [executable, "status", "--json"]
    result = run(command, root)
    record["status"] = execution_record(command, result)
    if result.returncode != 0:
        record["reason"] = "status-unhealthy"
        return record, executable
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        record["reason"] = "status-unhealthy"
        return record, executable

    backend = find_backend(payload)
    record["available"] = True
    record["reason"] = "available"
    record["backend"] = backend
    if backend == "wasm":
        record["warnings"].append("wasm-backend")
    return record, executable


def affected_gate(
    root: pathlib.Path,
    executable: str,
    filter_pattern: str | None,
    depth: int | None,
) -> dict[str, Any]:
    diff_command = ["git", "diff", "HEAD", "--name-only"]
    diff = run(diff_command, root)
    evidence: dict[str, Any] = {
        "state": "pending",
        "cwd": str(root),
        "diff": execution_record(diff_command, diff),
        "affected": None,
        "tests": [],
    }
    if diff.returncode != 0:
        evidence["state"] = "failed"
        evidence["reason"] = "git-diff-failed"
        return evidence

    changed = [line for line in diff.stdout.splitlines() if line]
    evidence["changed_file_count"] = len(changed)
    if not changed:
        evidence["state"] = "empty"
        evidence["reason"] = "no-changed-files"
        return evidence

    command = [executable, "affected", "--stdin", "--json"]
    if filter_pattern:
        command.extend(["--filter", filter_pattern])
    if depth is not None:
        command.extend(["--depth", str(depth)])
    affected = run(command, root, "\n".join(changed) + "\n")
    evidence["affected"] = execution_record(command, affected)
    if affected.returncode != 0:
        evidence["state"] = "failed"
        evidence["reason"] = "affected-failed"
        return evidence
    try:
        payload = json.loads(affected.stdout)
    except json.JSONDecodeError:
        evidence["state"] = "failed"
        evidence["reason"] = "affected-invalid-json"
        return evidence

    evidence["tests"] = extract_paths(payload)
    evidence["state"] = "executed" if evidence["tests"] else "empty"
    evidence["reason"] = "affected-tests" if evidence["tests"] else "no-affected-tests"
    return evidence


def build_report(
    repository: pathlib.Path,
    status_only: bool = False,
    filter_pattern: str | None = None,
    depth: int | None = None,
) -> dict[str, Any]:
    root = repository.resolve()
    codegraph, executable = status_gate(root)
    report: dict[str, Any] = {"repository": str(root), "codegraph": codegraph}
    if status_only:
        report["affected"] = {"state": "not-required", "tests": []}
    elif executable and codegraph["available"]:
        report["affected"] = affected_gate(root, executable, filter_pattern, depth)
    else:
        report["affected"] = {"state": "not-required", "tests": []}
    report["evidence_complete"] = report["affected"]["state"] in {
        "executed",
        "empty",
        "not-required",
        "failed",
    }
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=pathlib.Path, default=pathlib.Path.cwd())
    parser.add_argument("--status-only", action="store_true")
    parser.add_argument("--filter")
    parser.add_argument("--depth", type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(
        json.dumps(
            build_report(
                args.repository,
                status_only=args.status_only,
                filter_pattern=args.filter,
                depth=args.depth,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
