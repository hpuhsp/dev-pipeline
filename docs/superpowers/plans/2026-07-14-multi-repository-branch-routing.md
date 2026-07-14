# Implementation Plan: Multi-Repository Branch Routing

## Goal

Route Branch Selection to the repository that owns the reviewed changes and require a user choice when several repositories changed.

## Architecture

Environment Discovery records repository ownership; Branch Selection resolves one `target_repo` and scopes all Git commands with `git -C`.

## Technology

Markdown skill instructions, Python `unittest` repository contracts, Git CLI, ZIP-compatible `.skill` package.

## Tasks

### Task 1: Add failing repository-routing contracts

- Modify `tests/test_repository.py`.
- Assert target repository resolution, multi-repository stop behavior, subtree ownership, stash exclusion, and `git -C` branch commands.
- Run the test suite and confirm the new test fails against the current Branch Selection instructions.

### Task 2: Implement repository-aware Branch Selection

- Modify `.claude/skills/dev-pipeline/SKILL.md` Environment Discovery and Branch Selection sections.
- Record repository ownership without reading stash state.
- Select one target repository or stop for user selection.
- Scope branch inspection and creation commands to the selected repository.
- Run the targeted tests and confirm they pass.

### Task 3: Package and regression verification

- Rebuild `dev-pipeline.skill` from the updated skill source without a manifest.
- Run all repository tests and CI-equivalent package/frontmatter/Markdown checks.
- Review the final diff for unrelated changes and whitespace errors.
