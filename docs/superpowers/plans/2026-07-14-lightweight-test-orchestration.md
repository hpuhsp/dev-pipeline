# Implementation Plan: Lightweight Test Orchestration

## Goal

Implement change-aware test selection and coverage/report generation with zero third-party runtime dependencies.

## Architecture

A Python runner classifies changed files, executes `unittest` when needed, maps passing tests to a requirement manifest, and writes JSON/Markdown reports. CI calls the runner before structural package checks.

## Technology

Python standard library, `unittest`, JSON, Markdown, GitHub Actions.

## Tasks

### Task 1: Define failing policy and report tests

- Add `tests/test_test_runner.py`.
- Test documentation-only skips, skill changes, Agent-eval recommendations, stash exclusion contract and report dimensions.
- Run tests and confirm failure because the runner does not exist.

### Task 2: Implement runner and coverage manifest

- Add `scripts/test_runner.py` and `tests/coverage_manifest.json`.
- Implement Git change discovery, tier selection, unittest result collection, coverage aggregation and report writers.
- Run focused and full unit tests.

### Task 3: Integrate CI and skill guidance

- Replace direct unittest invocation in CI with the runner and upload reports.
- Update the skill's test necessity/report rules and changelog.
- Rebuild `dev-pipeline.skill`.

### Task 4: Verify completion

- Exercise structural, unit and Agent-eval decisions with explicit file lists.
- Run complete CI-equivalent checks and inspect generated reports.
