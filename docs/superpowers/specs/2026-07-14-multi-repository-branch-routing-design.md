# Multi-Repository Branch Routing Design

## Goal

Ensure Branch Selection creates a branch in the Git repository that owns the selected changes instead of implicitly using the pipeline's launch directory.

## Repository semantics

- The current repository and each initialized recursive Git submodule are candidate repositories.
- A Git subtree without its own `.git` metadata belongs to the parent repository and is routed to the parent.
- An independently nested Git repository is treated like a submodule once it is explicitly present in the pipeline's reviewed repository scope.
- Stash entries are never queried, applied, popped, or included in change detection.

## Selection behavior

1. Carry the repository root associated with reviewed changes from Environment Discovery into Branch Selection.
2. Determine repository ownership with `git -C <path> rev-parse --show-toplevel` and run status checks with `git -C <repo-root> status --porcelain`.
3. Ignore parent-repository gitlink-only dirtiness when the actual code changes are inside a submodule.
4. If exactly one repository owns the selected changes, use it as `target_repo`.
5. If multiple repositories own selected changes, stop and list them for the user to choose. Never create branches in several repositories automatically.
6. Run every branch query and mutation through `git -C "<target_repo>" ...`.

## Safety constraints

- Never inspect `git stash`, `refs/stash`, or stash reflogs.
- Do not infer that a subtree is an independent repository from its directory name.
- Preserve detached-HEAD, branch-exists, base-branch, and confirmation guards in the selected repository.
- Repeat the target repository in the final confirmation before branch creation.

## Verification

Repository contract tests assert that Branch Selection documents repository resolution, multi-repository ambiguity handling, subtree semantics, stash exclusion, and repository-scoped Git commands.
