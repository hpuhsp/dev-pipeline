# Changelog

All notable changes to the dev-pipeline skill pack are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [SemVer](https://semver.org/).

## [1.1.0] - 2026-06-11

### Fixed
- Rebuilt `dev-pipeline.skill` package — the previous package was built before Rounds 2-5 of review fixes and shipped stale content; it also used Windows backslash path separators inside the zip, which broke extraction on Linux/macOS
- Unified commit subject length rule to 70 characters (English) / 35 (Chinese) — previously stated as both 70 and 50 in `commit-conventions.md`
- Removed a stray closing code fence in `commit-conventions.md` that broke Markdown rendering of all following sections
- SKILL.md Phase 3 type table now includes `ci` and `revert`; Phase 4 branch table now includes `test/` and aligns `ci`/`deps` under `chore/`
- Phase 0 now documents cleanup of `git add -N` intent-to-add entries when the pipeline is aborted
- Phase 5 sensitive-file handling no longer suggests `git rm --cached` for never-staged untracked files

### Added
- `LICENSE` file (MIT) — previously only claimed in the README badge
- `version` and `license` fields in SKILL.md frontmatter
- This CHANGELOG
- `evals/` — sample defect diffs (JS/TS, Python, Java) with expected findings, for verifying review behavior
- CI workflow: validates SKILL.md frontmatter, checks `.skill` package is in sync with source, rejects backslash paths in the package

### Changed
- `review-checklist.md` (the 1B serial fallback used by non-Claude-Code agents) rewritten bilingual, English primary
- `review-agents.md`, `commit-conventions.md`, `tooling.md` headers and key instructions now bilingual

## [1.0.0] - 2026-05-25

### Added
- Initial dev-pipeline skill pack: 5-phase pipeline (Code Review → Unit Test → Commit Message → Branch → Commit)
- Dual-mode review: 3-agent parallel (Claude Code) with in-skill serial fallback (other agents)
- Coding standards references: Alibaba P3C, PEP 8, Airbnb JS, Vue 3, uni-app UTS, Android Kotlin, WCAG
- Conventional Commits message generation, branch naming, sensitive-file guard, pre-commit hook failure recovery
- Five rounds of expert-review hardening (2026-05-19 → 2026-05-25)
