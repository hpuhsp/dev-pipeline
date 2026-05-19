# Dev Pipeline

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/hpuhsp/dev-pipeline.svg)](https://github.com/hpuhsp/dev-pipeline/stargazers)

[中文版](README_zh.md) | English

---

Multi-step code delivery skill pack for Claude Code and other AI Agents.

## Pipeline

```
git diff → ① Code Review → ② Unit Test → ③ Commit Message → ④ Branch → ⑤ Commit
```

## Features

- **Dual-mode Review**: 3-agent parallel review (Claude Code) / in-skill serial fallback (other agents)
- **6 Coding Standards**: Alibaba P3C, PEP 8, Airbnb JS, Vue 3, uni-app UTS, Android Kotlin
- **Auto-detection**: test framework, project tech stack, commit type
- **Conventional Commits**: auto type/scope inference, `deps` type, 70-char subject
- **Portable**: pure Markdown, zero external dependencies
- **Fix-First Review**: AUTO-FIX for mechanical issues, ASK for architectural decisions

## Install

```bash
cp -r .claude/skills/dev-pipeline ~/.claude/skills/dev-pipeline   # user-level
npx skills add hpuhsp/dev-pipeline -g                              # or via npm
```

## Usage

| Mode | Triggers |
|------|----------|
| Full Pipeline | `commit my changes`, `ship it`, `done coding` |
| Code Review | `review my code`, `code review` |
| Test Generation | `generate tests` |
| Commit Message | `write commit message` |
| Quick Mode | `quick commit`, `skip review` |

## File Structure

```
dev-pipeline/
├── SKILL.md                         # Pipeline orchestrator
└── references/
    ├── review-agents.md             # 3-agent parallel review prompts
    ├── review-checklist.md          # In-skill serial review fallback
    ├── coding-standards.md          # Authoritative coding standards
    ├── test-generation.md           # Test generation guides
    ├── tooling.md                   # Static analysis toolchain
    └── commit-conventions.md        # Conventional Commits spec
```

## License

MIT
