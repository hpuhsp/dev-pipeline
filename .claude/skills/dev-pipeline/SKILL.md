---
name: dev-pipeline
description: >
  Multi-step code delivery pipeline: Code Review → Unit Test → Commit Message → Branch → Commit.
  Use this skill whenever the user has finished coding and needs to commit/ship their changes —
  it handles the full pipeline from review through commit. Proactively invoke when the user says
  they've completed code changes ("done coding", "ready to commit", "改完了", "提交代码") even
  if they don't explicitly ask for review or testing. Also invoke for any single step: code review
  against authoritative standards (Alibaba P3C, PEP 8, Airbnb JS, Vue, uni-app UTS), unit test
  generation with auto-detected frameworks, Conventional Commits messages, branch naming, or the
  complete delivery workflow. Triggers include: "commit my changes", "review my code", "ship it",
  "done coding", "ready to push", "提交代码", "review我的改动", "做code review". Especially
  valuable for multi-file changes that need systematic review, proper testing, and standardized
  commit history.
---

# Dev Pipeline · 开发流水线

All-in-one daily development workflow. In Claude Code: 3-agent parallel review. In other AI agents: in-skill serial review (auto-fallback). Subsequent phases always run serially.

一站式日常开发工作流。Claude Code 环境 3-agent 并行审查，其他环境自动退化为 Skill 内串行审查。

## Workflow Overview · 工作流概览

```
git diff/staged
  │
  ├─ ① Code Review — Claude Code: 3-Agent Parallel
  │                  Other agents: In-Skill Serial
  │
  ├─ ② Unit Test Generation
  ├─ ③ Commit Message / Changelog
  ├─ ④ Branch Selection
  └─ ⑤ Commit Execution
```

Each phase's output feeds the next. If any phase fails or the user rejects, pause and fix before continuing.
每一步输出是下一步的输入。遇到失败或用户否定，暂停管道，修复后继续。

---

## Phase 0: Environment Discovery · 环境感知

Before anything else, understand the project state:

1. Run `git status` — scope: staged / working tree / untracked
2. Run `git diff` and `git diff --staged` — full diff
3. **Guard: empty diff** — if both `git diff` and `git diff --staged` are empty, abort:
   > "No changes detected. Stage your changes first (`git add <files>`), then re-run the pipeline."
4. **Guard: merge conflict** — if `git status` shows `both modified:` entries (merge conflict in progress), abort:
   > "Merge conflict detected. Resolve all conflicts first, then re-run the pipeline."
5. **Guard: non-git repository** — if `git status` fails with "not a git repository", abort:
   > "Not a git repository. Run `git init` or navigate to a git project first."
6. Detect the tech stack:
   - If `Glob` tool is available, use it to check for key files: `package.json`, `pyproject.toml`, `pom.xml`, `build.gradle`, etc.
   - **Fallback (no Glob tool)**: Use shell: `find . -maxdepth 3 \( -name "package.json" -o -name "pyproject.toml" -o -name "pom.xml" -o -name "build.gradle" -o -name "build.gradle.kts" \) 2>/dev/null`
   - Key file → stack mapping:
     - `package.json`, `tsconfig.json` → JS/TS project
     - `pyproject.toml`, `setup.py`, `requirements*.txt` → Python project
     - `pom.xml`, `build.gradle`, `build.gradle.kts` → Java/Kotlin project
     - `.editorconfig`, `.eslintrc.*`, `.prettierrc*` → code style tools
     - Check `vue`, `react`, `next`, `uni-app` deps to confirm frontend framework
7. **Guard: binary files** — if diff contains "Binary files differ" entries, note them but exclude from review (they're non-text, un-reviewable).
8. **Guard: large diff** — if diff > 500 lines, warn: "Large diff detected (N lines). Review quality may degrade. Consider splitting into smaller commits."

Summarize: how many files changed, what type of change, impact scope.
汇总告知用户：涉及几个文件、什么类型的变化、影响范围。

### Phase 0.5: Scope Drift Detection (optional) · 范围漂移检测

**Lightweight check** (always): If more than 5 files changed, ask "Are all these changes related? Or should they be split into separate commits?"

**Deep check** (if `TODOS.md` or `.plan` exists in project root):

1. `TODOS.md`: do diff files match TODO items?
2. Git log: any unrelated files changed ("while I was in there...")?
3. Output format:
   ```
   Scope Check: CLEAN | DRIFT DETECTED | NEEDS REVIEW
   Intent: <1-line summary of what was intended>
   Delivered: <1-line summary of what the diff actually does>
   ```
4. If DRIFT DETECTED: flag out-of-scope files, ask whether to split commits
5. If CLEAN or no TODOS.md/.plan: proceed to Phase 1

---

## Phase 1: Code Review · 代码审查 (Dual Mode)

### Mode Detection · 模式检测

Check if you have the **Agent tool** (look for `Agent` in your tool list).

- **Agent tool available + diff > 50 lines** → [1A: Parallel Agent Review]
- **Agent tool available + diff ≤ 50 lines** → [1B: In-Skill Serial Review] (small diff — parallel overhead not justified)
- **No Agent tool** → [1B: In-Skill Serial Review]

---

### 1A: Parallel Agent Review · 并行 Agent 审查 (Claude Code)

**Core principle**: Launch all 3 agents in a single message. Each agent has isolated context and reviews the same diff from a different angle.

#### Preparation

Read `references/review-agents.md` for the complete agent prompts.

#### Launch

**Must launch all 3 agents in ONE message** (serial launching wastes time). Use the Agent tool with these parameters:

| Parameter | Agent 1 | Agent 2 | Agent 3 |
|-----------|---------|---------|---------|
| `subagent_type` | `"general-purpose"` | `"general-purpose"` | `"general-purpose"` |
| `description` | `"Security+Correctness review"` | `"Performance+Efficiency review"` | `"Maintainability+Style review"` |
| `prompt` | Agent 1 template + diff | Agent 2 template + diff | Agent 3 template + diff |

Each agent's `prompt` = the corresponding full template from `references/review-agents.md`, with `{git_diff}` replaced by the actual diff output and `{detected_language_framework}` replaced by the detected tech stack string (e.g. "TypeScript React project with Jest").

**Partial failure handling**: If one or two agents fail to return results (timeout, error), proceed with partial results. Note the missing perspective in output: "Agent N unavailable — {dimension} not covered."

**Launch syntax note**: In Claude Code, invoke the `Agent` tool 3 times in a single message. The pseudo-code above describes parameter mapping; construct actual tool calls per your platform's API.

#### Aggregate Results + Fix-First Classification · 聚合 + 修复分类

After all 3 agents return, classify each finding and aggregate.

**Fix-First rules**:
- `AUTO`: Mechanical fixes (renaming, extract constant, add null check, formatting) → auto-apply, output `[AUTO-FIXED]`
- `ASK`: Needs user decision (architecture changes, API changes, breaking changes) → batch into decision list
- If agent didn't label fix: naming/format/null-check → AUTO; logic/architecture/security/performance → ASK

**Confidence gating** (applied by aggregator, not by individual agents — agents should report ALL findings):
- Confidence ≥ 7 → show in main report
- Confidence 5-6 → show with "Medium confidence, verify" caveat
- Confidence 3-4 → move to appendix (don't block pipeline)
- Confidence 1-2 → suppress entirely

**Aggregate output format**:

```
## Code Review Results (Parallel 3-Agent)

### 🔴 Blockers (must fix)
- [ ] [AUTO-FIXED] file:line — problem → auto-fixed (Agent N, conf: X/10)
- [ ] [NEEDS DECISION] file:line — problem → recommended fix (Agent N, conf: X/10)
  ...

### 🟡 Warnings (should fix)
- [ ] [AUTO-FIXED] file:line — problem → auto-fixed (Agent N, conf: X/10)
- [ ] file:line — problem → fix suggestion (Agent N, conf: X/10)
  ...

### 🟢 Passing
- No security issues (Agent 1 ✅)
- Performance is fine (Agent 2 ✅)
- Code style compliant (Agent 3 ✅) [Standard: {matched}]

### Appendix — Low-Confidence Findings
- (conf: 4/10) file:line — description (Agent N)

### Overall Score: X/10
  - Security+Correctness: X/10 (Agent 1)
  - Performance+Efficiency: X/10 (Agent 2)
  - Maintainability+Standards: X/10 (Agent 3)
  - Coding Standards Compliance: X/10 (Agent 3, per coding-standards.md)
```

**Dedup**: Same issue from multiple agents → merge into one entry, cite all sources, use highest confidence.

**Conflicts**: Agents disagree → flag the conflict, give your judgment, ask the user to decide.

---

### 1B: In-Skill Serial Review · Skill 内串行审查 (Other AI Agents)

When the Agent tool is unavailable, perform review yourself. Read `references/review-checklist.md`.

Review dimensions in order: Correctness → Security → Performance → Maintainability → Consistency. Output format matches 1A, but source labeled "In-Skill Review".

---

### Post-Review Decision · 审查后决策

- 🔴 Blockers → ask user whether to fix before continuing
  - If user says yes: apply fixes → re-run Phase 1 review (verify fixes don't introduce new issues) → repeat until green
  - If user opts to defer blockers: note in commit message body that known issues are deferred
- 🟡 Warnings only → note and continue; user decides
- All 🟢 → proceed directly to Phase 2

---

## Phase 2: Unit Test Generation · 单元测试生成

Generate unit tests based on the changed code. Read `references/test-generation.md` for language-specific guides.

### Principles

- **Prioritize Phase 1 findings**: Focus test coverage on code paths flagged by review (null handling gaps, edge cases, error paths in correctness findings)
- **Don't test third-party code**: Test your logic, not framework/library behavior
- **Cover boundaries**: Happy path + edge cases + error paths
- **One test, one behavior**: Each test verifies exactly one thing
- **Use existing framework**: Never introduce a new test framework; auto-detect from project config

### Framework Detection

Check in priority order:
1. `package.json` devDeps: `jest`, `vitest`, `mocha`
2. `pyproject.toml` / `setup.cfg`: `pytest`, `unittest`
3. `pom.xml` / `build.gradle`: `junit`, `testng`, `mockito`
4. Config files: `jest.config.*`, `vitest.config.*`, `pytest.ini`

**Fallback**: If no framework found, ask: "No test framework detected. Which framework do you use? (or skip test generation)"

### Output Placement

- JS/TS: `__tests__/` or co-located `*.test.ts`
- Python: `tests/` directory, `test_*.py`
- Java/Kotlin: `src/test/java/`, matching package path

Run affected tests after generation to confirm no regressions. **Scoping**: Run only tests in the changed module/package (e.g. `pytest tests/auth/`, `npm test -- --testPathPattern auth`), not the full suite. Abort and report if test suite exceeds 2-minute runtime.

---

## Phase 3: Commit Message / Changelog · 变更日志

Generate Conventional Commits messages. Read `references/commit-conventions.md`.

### Auto Type Inference

| Change Pattern | Type | Example |
|---------|------|------|
| New file/function/component/API | `feat` | `feat(auth): add JWT token refresh` |
| Fixed logic/behavior | `fix` | `fix(api): handle null response body` |
| Docs/comments only | `docs` | `docs(readme): update install guide` |
| Dependency version bumps | `deps` | `deps: bump axios to 1.7.0` |
| Formatting/quotes/semicolons | `style` | `style: format with prettier` |
| Refactor (no behavior change) | `refactor` | `refactor(db): extract query builder` |
| Performance optimization | `perf` | `perf(list): add virtual scrolling` |
| Test additions/changes | `test` | `test(auth): add 2FA coverage` |
| Build/config/misc | `build` / `chore` | `chore: update .gitignore` |

### Scope Inference

- From file path: `src/auth/login.ts` → `auth`
- Multi-file changes → common top-level module
- Too broad → omit scope

### Breaking Changes

If detecting API signature changes, config renames, or return type changes, add `BREAKING CHANGE:` footer.

### Output Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

Present to user for confirmation; user can edit directly.

---

## Phase 4: Branch Selection · 分支选择

| Type | Branch Prefix | Example |
|------|---------|------|
| `feat` | `feature/` | `feature/jwt-token-refresh` |
| `fix` | `fix/` | `fix/null-response-handling` |
| `refactor` | `refactor/` | `refactor/query-builder` |
| `docs` | `docs/` | `docs/install-guide` |
| `perf` | `perf/` | `perf/virtual-scroll` |
| `chore` / `build` | `chore/` | `chore/update-deps` |

### Steps

1. Check current branch (`git branch --show-current`)
2. **Guard: detached HEAD** — if result is empty, warn: "HEAD is detached. Creating a branch from a detached state may lose work. Create a branch from the current commit first?" Proceed only if user confirms.
3. If already on `feature/*` or `fix/*` matching the change → commit directly
4. **Guard: type mismatch** — if on `feature/*` branch but change type is `fix` (or vice versa), ask: "You're on a feature branch but this looks like a fix. Create a new branch or commit to the current one?"
5. If on `main`/`master`/`develop` → recommend creating a new branch
6. Mixed-type changes (e.g. feat+docs):
   - Branch prefix follows the primary change type (usually `feat`)
   - Inform user that docs/chore changes can follow the main branch or be split into a separate PR
7. **Guard: branch exists** — before creating, check if branch name already exists (`git branch --list <name>`). If it does, append a numeric suffix: `feature/jwt-refresh-2`
8. Show recommended branch name, ask for confirmation
9. `git checkout -b <branch-name>` (after confirmation)

---

## Phase 5: Commit Execution · 执行提交

### Pre-Commit Checklist

- [ ] Code Review: no blockers
- [ ] Tests generated and existing tests pass
- [ ] Commit message confirmed by user
- [ ] Branch selected/created
- [ ] No sensitive files (`.env`, `.pem`, credentials, etc.)

**Sensitive file check**: Scan staged file names AND diff content for: `.env` (unless `.env.example`), `*.pem`, `*.p12`, `*.pfx`, `credentials*`, `*secret*`, `*password*`, `BEGIN RSA PRIVATE KEY`, `BEGIN OPENSSH PRIVATE KEY`. If found → block commit, warn user, remove from staging with `git rm --cached <file>`.

### Commit Steps

1. **Selective staging**: Run `git diff --name-only` to get changed files, then `git add <files>` individually (never `git add -A` or `git add .`). Exclude binary files, generated files, and sensitive files.
2. Show the file list AND the final commit message, ask for final confirmation (both files AND message together)
3. `git commit -m "<generated message>"`
4. Show result

### Pre-Commit Hook Failure · 预提交钩子失败

If `git commit` fails due to pre-commit hooks (linter, formatter, tests):

1. **Read the hook error output** — parse what failed and why
2. **Classify the failure**:
   - **Auto-fixable**: linter/format errors with auto-fix available → run the auto-fix command (e.g. `npx biome check --write .`, `ruff check --fix .`, `ktlint -F`), then re-add and retry commit
   - **Manual**: test failures, complex lint rules → show the error output, suggest fixes, ask user to resolve
   - **Infrastructure**: hook script errors, missing binaries → report the issue, don't attempt auto-fix
3. **Retry**: After fixing, `git add <fixed-files>` and `git commit` again (max 3 retries)
4. **Give up gracefully**: If hooks keep failing after 3 attempts, report: "Pre-commit hooks still failing after 3 fix attempts. Please resolve manually: <error output>. Re-run pipeline after fixing."

```
✅ Commit successful
   Branch: feature/jwt-refresh
   Commit: a1b2c3d feat(auth): add JWT token refresh

   Next:
   - git push origin feature/jwt-refresh
   - Or let me create a PR
```

---

## Mode Quick Reference · 模式速查

| Mode | Triggers | Behavior |
|------|--------|------|
| **Full Pipeline** | "commit my changes", "ship it", "提交代码" | Phase 0→1→2→3→4→5 |
| **Quick Mode** | "quick commit", "skip review", "快速提交" | Phase 0→3→4→5 only |
| **Review Only** | "review my changes", "code review" | Phase 1 only |
| **Test Only** | "generate tests", "生成测试" | Phase 2 only |
| **Message Only** | "write commit message", "生成commit message" | Phase 3 only |

---

## Reference Files · 参考文件

- `references/review-agents.md` — 3 parallel agent prompts + coding standards checks (Claude Code)
- `references/review-checklist.md` — In-skill serial review checklist (universal fallback)
- `references/coding-standards.md` — **Authoritative coding standards**: Alibaba P3C, PEP 8, Airbnb JS, Vue 3, uni-app UTS, Android Kotlin, WCAG, Java 17+
- `references/tooling.md` — **Recommended static analysis toolchain**: ESLint, Ruff, Checkstyle, detekt, Biome, and more
- `references/test-generation.md` — Test generation guides for JS/TS/Python/Java/Kotlin
- `references/commit-conventions.md` — Conventional Commits spec with dual-style branch naming
