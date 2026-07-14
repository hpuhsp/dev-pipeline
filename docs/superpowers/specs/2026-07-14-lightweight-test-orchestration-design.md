# Lightweight Test Orchestration Design

## Goal

Add change-aware test selection and multi-dimensional reports without adding runtime dependencies or running token-expensive Agent evaluations by default.

## Test tiers

- `structural`: documentation-only changes skip Python unit tests; existing frontmatter, Markdown and package checks still run.
- `unit`: skill source, scripts, tests, CI, package or unknown files run deterministic Python tests.
- `agent-eval`: review prompts/checklists or seeded eval fixtures run deterministic tests and recommend Agent evaluation. Agent evaluation remains opt-in or scheduled.

Change discovery uses the working tree and index (`git diff HEAD` plus untracked files). It never reads Git stash state.

## Coverage model

Because the product is primarily instructional Markdown, source-line coverage would be misleading. Reports use:

- requirement coverage: declared behavioral requirements backed by passing tests;
- scenario coverage: coverage grouped by repository routing, change policy, packaging, review behavior and reporting;
- execution metrics: total, passed, failed, errors, skipped, pass rate and duration;
- cost metrics: whether Agent evaluation ran and its token budget/usage when available.

## Outputs

- machine-readable JSON;
- concise Markdown report;
- GitHub Actions step summary when `GITHUB_STEP_SUMMARY` is available.

The runner uses Python's standard library only. Reports are uploaded as CI artifacts. No Agent call occurs in pull-request CI unless explicitly enabled.
