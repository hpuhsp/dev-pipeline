# Dev Pipeline

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.5.0-blue.svg)](CHANGELOG.md)
[![Validation](https://github.com/hpuhsp/dev-pipeline/actions/workflows/validate.yml/badge.svg)](https://github.com/hpuhsp/dev-pipeline/actions/workflows/validate.yml)

[中文说明](README_zh.md)

Dev Pipeline is an intent-routed delivery Skill for Claude Code, Codex, and other AI coding agents. It provides composable nodes for code review, unit testing, commit messages, branch selection, and commit execution without forcing every request through an end-to-end workflow.

## Why Dev Pipeline

Traditional delivery prompts often trigger more work than the user requested. Dev Pipeline analyzes the prompt first, selects the smallest sufficient node set, and stops when those nodes are complete.

```text
User prompt
    |
    v
Intent Router
    |
    +-- Review
    +-- Test
    +-- Message
    +-- Branch
    +-- Commit
    `-- Explicit combinations or Full Pipeline
```

Only explicit end-to-end intent selects the full sequence:

```text
Review -> Test -> Message -> Branch -> Commit
```

## Routing Examples

| Prompt | Selected route | What does not run |
|---|---|---|
| `review my changes` | Review | Test, Message, Branch, Commit |
| `generate tests and coverage report` | Test | Review, Branch, Commit |
| `write a commit message` | Message | Review, Test, Branch, Commit |
| `create a feature branch` | Branch | Review, Test, Commit |
| `commit my changes` | Commit + minimum safety checks | Review, Test, Branch unless required |
| `review and test these changes` | Review + Test | Message, Branch, Commit |
| `run the complete delivery pipeline` | Full Pipeline | Nothing |

Explicit exclusions always win. For example, `commit and push, do not review` never enters the Review or Test nodes.

## Core Capabilities

### Intent-routed workflow

- Produces target, supporting, and excluded node decisions from the user prompt.
- Prevents implicit fall-through from one numbered phase to the next.
- Loads environment context and reference files only when selected nodes need them.
- Treats push and pull-request creation as explicit extension actions, not automatic pipeline phases.

### Code review

- Uses three parallel review perspectives when an agent tool is available and the diff is large enough.
- Falls back to an in-skill serial review for small diffs or environments without sub-agents.
- Covers correctness, security, performance, maintainability, and project consistency.
- Supports Alibaba P3C, PEP 8, Airbnb JavaScript, Vue 3, uni-app UTS, Android Kotlin, Swift API Design Guidelines, and WCAG guidance.
- Applies confidence gating and separates mechanical auto-fixes from decisions that need user approval.

### Change-aware testing

The dependency-free test runner classifies changes into the cheapest safe tier:

| Tier | Typical changes | Behavior |
|---|---|---|
| `structural` | README, changelog, license, or `docs/` only | Skip unit tests; keep structural validation |
| `unit` | Skill source, scripts, tests, CI, package, or unknown files | Run deterministic affected tests |
| `agent-eval` | Review prompts, checklists, or evaluation fixtures | Run deterministic tests and recommend opt-in Agent evaluation |

Reports are emitted as JSON and Markdown and include:

- total, passed, failed, errors, skipped, pass rate, and duration;
- behavioral requirement coverage and scenario coverage;
- failed requirement or scenario identifiers;
- Agent evaluation status, token budget, and actual token usage.

Ordinary deterministic validation consumes zero Agent-evaluation tokens.

### Repository-aware Git operations

- Resolves the Git worktree that owns each changed path.
- Treats Git submodules as independent repositories.
- Treats a Git subtree without independent `.git` metadata as part of its parent repository.
- Stops for user selection when selected changes span multiple repositories.
- Scopes branch and commit commands with `git -C <target_repo>`.
- Never runs `git stash`, reads `refs/stash`, or analyzes stashed content.

### Repository-scoped CodeGraph

- Detects CodeGraph independently for every changed Git worktree; no pipeline-global availability flag is used.
- Requires a local index, executable CLI, and healthy status response before it runs affected-test analysis.
- Runs the diff, CodeGraph query, and test command from the same repository root.
- Requires each Git submodule to have its own CodeGraph index; a true Git subtree uses its parent repository index.
- Falls back only for the unavailable repository and reports a per-repository reason.

### Safe commit delivery

- Generates Conventional Commit messages from the actual change type and scope.
- Detects Git-Flow and conventional branch naming styles.
- Uses selective staging instead of `git add .` or `git add -A`.
- Blocks common credential, private-key, and sensitive-file patterns.
- Handles pre-commit hook failures by separating auto-fixable, manual, and infrastructure errors.

## Installation

### Install from GitHub

```bash
npx skills add hpuhsp/dev-pipeline -g
```

### Install manually

Project-level installation:

```bash
git clone https://github.com/hpuhsp/dev-pipeline.git
cp -r dev-pipeline/.claude/skills/dev-pipeline <your-project>/.claude/skills/dev-pipeline
```

User-level installation:

```bash
cp -r .claude/skills/dev-pipeline ~/.claude/skills/dev-pipeline
```

The repository also contains `dev-pipeline.skill`, a portable packaged artifact kept in sync with the source by validation. Run `python scripts/sync_skill.py` after changing the Skill to rebuild the package and synchronize the configured local copy; use `--check` to verify both artifacts without writing.

## Usage

Ask for exactly the action you want:

```text
Review my current changes for correctness and security.
Generate unit tests and a coverage report for this change.
Write a Conventional Commit message for the staged files.
Create an appropriate branch in the repository that owns these changes.
Commit the current changes, but do not run review or tests.
Run the complete pipeline and stop if any validation fails.
```

The Skill infers the route from the prompt. No slash command is required.

## Validation

Run the complete deterministic suite:

```bash
python scripts/test_runner.py --all
```

Run change-aware validation for the current working tree:

```bash
python scripts/test_runner.py --report-dir artifacts/test-results
```

GitHub Actions runs the same change-aware validation and uploads the JSON and Markdown reports.

## Project Structure

```text
.
|-- .claude/skills/dev-pipeline/
|   |-- SKILL.md
|   `-- references/
|       |-- coding-standards.md
|       |-- commit-conventions.md
|       |-- review-agents.md
|       |-- review-checklist.md
|       |-- test-generation.md
|       `-- tooling.md
|-- scripts/
|   `-- test_runner.py
|   `-- sync_skill.py
|-- tests/
|   |-- coverage_manifest.json
|   |-- test_repository.py
|   `-- test_test_runner.py
|-- docs/superpowers/
|-- dev-pipeline.skill
|-- CHANGELOG.md
`-- LICENSE
```

## Design Principles

- Explicit user intent has priority over keyword heuristics.
- Use the smallest safe route and avoid unnecessary context loading.
- Prefer deterministic validation over model-based evaluation in ordinary CI.
- Preserve repository boundaries and never inspect stashed work.
- Require fresh evidence before reporting success.

## License

[MIT](LICENSE)
