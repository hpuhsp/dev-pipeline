#!/usr/bin/env python3
"""Validate, commit, push main, and fast-forward the configured master branch."""

from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_MESSAGE = "chore: sync dev-pipeline updates"


def run(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        capture_output=capture,
        text=True,
    )


def output(command: list[str]) -> str:
    return run(command, capture=True).stdout.strip()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def branch_exists(branch: str) -> bool:
    return subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
        cwd=ROOT,
        check=False,
    ).returncode == 0


def ensure_fast_forward(remote_ref: str) -> None:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", remote_ref, "HEAD"],
        cwd=ROOT,
        check=False,
    )
    require(
        result.returncode == 0,
        f"{remote_ref} is not an ancestor of HEAD; fetch/reconcile manually before publishing.",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--message", default=DEFAULT_MESSAGE)
    parser.add_argument("--main-remote", default="origin2")
    parser.add_argument("--master-remote", default="origin")
    parser.add_argument("--main-branch", default="main")
    parser.add_argument("--master-branch", default="master")
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--skip-user-skill-sync", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    current_branch = output(["git", "branch", "--show-current"])
    require(
        current_branch == args.main_branch,
        f"Run from {args.main_branch!r}; current branch is {current_branch!r}.",
    )

    if args.dry_run:
        print(
            "Dry run: would sync the skill, validate, commit current changes, push "
            f"{args.main_remote}/{args.main_branch}, and fast-forward "
            f"{args.master_remote}/{args.master_branch}."
        )
        return 0

    sync_command = [sys.executable, "scripts/sync_skill.py"]
    if args.skip_user_skill_sync:
        sync_command.append("--skip-installed")
    run(sync_command)
    if not args.skip_tests:
        run([sys.executable, "scripts/test_runner.py", "--all", "--quiet"])

    run(["git", "fetch", args.main_remote, args.main_branch])
    run(["git", "fetch", args.master_remote, args.master_branch])
    ensure_fast_forward(f"{args.main_remote}/{args.main_branch}")
    ensure_fast_forward(f"{args.master_remote}/{args.master_branch}")

    run(["git", "add", "--all"])
    run(["git", "diff", "--cached", "--check"])
    if not output(["git", "diff", "--cached", "--name-only"]):
        print("No changes to publish.")
        return 0

    run(["git", "commit", "-m", args.message])
    run(["git", "push", args.main_remote, args.main_branch])
    run(["git", "push", args.master_remote, f"HEAD:{args.master_branch}"])

    if branch_exists(args.master_branch):
        run(["git", "branch", "-f", args.master_branch, "HEAD"])
    else:
        run(["git", "branch", "--track", args.master_branch, f"{args.master_remote}/{args.master_branch}"])
    run(
        [
            "git",
            "branch",
            "--set-upstream-to",
            f"{args.master_remote}/{args.master_branch}",
            args.master_branch,
        ]
    )
    print(
        f"Published {output(['git', 'rev-parse', '--short', 'HEAD'])}: "
        f"{args.main_remote}/{args.main_branch} and "
        f"{args.master_remote}/{args.master_branch} are synchronized."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Publish aborted: {error}", file=sys.stderr)
        raise SystemExit(1)
