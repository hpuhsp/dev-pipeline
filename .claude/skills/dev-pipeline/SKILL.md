---
name: dev-pipeline
description: >
  Intent-routed code delivery nodes for review, unit tests, commit messages, branch selection,
  and commit execution. Use for any one of these actions, any explicit combination, or an
  explicitly requested end-to-end delivery pipeline. Analyze the user's prompt first and execute
  only the smallest sufficient node set; requests such as "review my code", "generate tests",
  "write a commit message", "create a branch", or "commit my changes" must not automatically run
  unrelated earlier or later phases. Supports authoritative review standards, framework-aware
  tests, Conventional Commits, and repository-aware Git operations including submodules.
---

# Dev Pipeline · 开发流水线

Composable daily development workflow. First route the user's prompt to the smallest sufficient set of nodes. In Claude Code, review may use 3 parallel agents; other environments use the in-skill serial fallback.

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

In Full Pipeline mode, each phase's output feeds the next. In every other mode, execute only the selected target nodes and their minimum safety dependencies. If any selected node fails or the user rejects its output, pause and fix before continuing.
每一步输出是下一步的输入。遇到失败或用户否定，暂停管道，修复后继续。

---

## Intent Router · 意图路由

Route before repository discovery or phase execution. Treat the workflow as composable nodes, not a mandatory sequence.

### Routing rules

1. **Explicit user intent wins.** Direct requests, exclusions, and named nodes override trigger keywords and defaults. For example, “commit and push, do not review” must not enter Review or Test.
2. Infer the user's **action**, not merely the presence of Git words. Produce an internal `route_plan` with:
   - `target_nodes`: nodes that directly satisfy the request;
   - `supporting_nodes`: only the minimum discovery, validation, or safety nodes required by those targets;
   - `excluded_nodes`: explicitly rejected or irrelevant nodes;
   - `reason`: one sentence grounded in the user's prompt.
3. **Do not fall through** from one completed node to the next phase. Return after all `target_nodes` and `supporting_nodes` complete.
4. Only explicit full-pipeline intent may select **Full Pipeline**. Never infer it solely from “done coding”, “ready”, “commit”, or a dirty worktree.
5. If the prompt contains multiple clear actions, select their union and preserve the user's order when dependencies allow it. Example: “review and generate tests” routes to Review + Test, not Commit.
6. If intent is genuinely ambiguous and different routes would cause materially different mutations, ask one concise question. Otherwise choose the smallest safe route.
7. References are lazy-loaded: read only the reference files required by selected nodes.

### Prompt-to-node routing table

| Route | Typical prompt intent | `target_nodes` | Minimum `supporting_nodes` |
|------|------------------------|----------------|----------------------------|
| **Full Pipeline** | “run the complete pipeline”, “review, test, branch and commit everything” | Review → Test → Message → Branch → Commit | Full Phase 0 |
| **Review Only** | review, audit, inspect problems, code quality | Review | Lightweight Phase 0 + repository contexts; activate optional tools only when eligible |
| **Test Only** | generate/run unit tests, coverage, test report | Test | Lightweight Phase 0 + per-repository framework detection; activate optional tools only when eligible |
| **Message Only** | write/improve a commit message or changelog | Message | Changed-file summary; diff only when needed |
| **Branch Only** | create/name/switch a branch | Branch | Repository ownership + current/base branch discovery |
| **Commit Only** | stage/commit current changes | Commit | Repository ownership + safety checks + Message when no message was supplied |
| **Combined Nodes** | two or more explicitly named actions | Named nodes only | Union of their minimum dependencies |

“Push”, “create PR”, or other actions outside the defined nodes must not silently trigger Full Pipeline. Perform them only if the environment supports the action and the user explicitly requests it; otherwise state the boundary.

Before acting, briefly state the selected route when useful, but do not ask for confirmation for a read-only route or safe, explicitly requested action.

---

## Phase 0: Environment Discovery · 环境感知

> **Route check first**: Apply the [Intent Router](#intent-router--意图路由) before discovery. Run full discovery only for Full Pipeline. For a targeted route, execute only the minimum discovery listed in the routing table. Review and Test always require repository contexts; Test detects the framework for each context. Defer optional-tool detection until an explicit eligibility rule selects it. Do not inspect branches or commit state unless the selected node needs them.

Before anything else, understand the project state:

1. Run `git status` — scope: staged / working tree / untracked
2. Run `git diff` and `git diff --staged` — full diff of tracked files
3. **Untracked files**: If `git status` shows untracked files, run `git add -N <untracked-files>` (intent-to-add, does NOT stage content, only makes the files visible to `git diff`). This ensures new files are included in code review without being committed accidentally. **Cleanup**: If the pipeline is aborted before Phase 5, remove the intent-to-add entries with `git reset -- <those-files>` so the index is left exactly as found.
4. **Guard: empty diff** — if both `git diff` and `git diff --staged` are empty AND `git status` shows no untracked files, abort:
   > "No changes detected. Stage your changes first (`git add <files>`), then re-run the pipeline."
5. **Guard: merge conflict** — run `git ls-files -u` (lists unmerged files, locale-independent). If output is non-empty (merge conflict in progress), abort:
   > "Merge conflict detected. Resolve all conflicts first, then re-run the pipeline."
6. **Guard: non-git repository** — if `git status` fails with "not a git repository", abort:
   > "Not a git repository. Run `git init` or navigate to a git project first."
7. Detect the tech stack:
   - If `Glob` tool is available, use it to check for key files: `package.json`, `pyproject.toml`, `pom.xml`, `build.gradle`, `*.xcodeproj`, `Package.swift`, `Podfile`, etc.
   - **Fallback (no Glob tool)**: Use shell. POSIX (Linux/macOS/Git Bash): `find . -maxdepth 3 \( -name "package.json" -o -name "pyproject.toml" -o -name "pom.xml" -o -name "build.gradle" -o -name "build.gradle.kts" -o -name "*.xcodeproj" -o -name "Package.swift" -o -name "Podfile" \) 2>/dev/null`. PowerShell (Windows): `Get-ChildItem -Recurse -Depth 3 -Include "package.json","pyproject.toml","pom.xml","build.gradle","build.gradle.kts","*.xcodeproj","Package.swift","Podfile" -Name -ErrorAction SilentlyContinue`. If neither works, fall back to checking files individually.
   - Key file → stack mapping:
     - `package.json`, `tsconfig.json` → JS/TS project
     - `pyproject.toml`, `setup.py`, `requirements*.txt` → Python project
     - `pom.xml`, `build.gradle`, `build.gradle.kts` → Java/Kotlin project
     - `*.xcodeproj`, `*.xcworkspace`, `Package.swift` → iOS/Swift project
     - `Podfile` → CocoaPods dependency management (iOS)
     - `.editorconfig`, `.eslintrc.*`, `.prettierrc*` → code style tools
     - Check `vue`, `react`, `next`, `uni-app` deps to confirm frontend framework
8. **Guard: binary files** — if diff contains "Binary files differ" entries, note them and ask user: "Binary files detected (e.g. images, PDFs). Exclude from review? (they're non-text, un-reviewable)". If user wants them committed, include them in Phase 5 staging but skip review. Never auto-exclude without user confirmation.
9. **Guard: large diff** — if combined diff output exceeds 500 lines (count with `(git diff; git diff --staged) | wc -l` on POSIX, or `(git diff; git diff --staged).Count` on PowerShell):
   - Warn: "Large diff detected (N lines). Review quality may degrade."
   - **Auto-fallback**: Force 1B serial review mode (even if Agent tool is available) — serial review is more token-efficient for large diffs and avoids 3× context duplication.
   - If diff > 1000 lines: additionally suggest file-by-file chunked review ("Review 5 files at a time?")
10. **Guard: submodules** — if `git submodule status` shows submodules, inspect each initialized submodule recursively with repository-scoped commands. A dirty gitlink in the parent is metadata, not a direct parent-code change when the actual edits are inside that submodule.
11. **Build repository contexts before tool detection** — resolve every changed path to its owning worktree with `git -C "<containing-directory>" rev-parse --show-toplevel`; for each initialized submodule, also enumerate its own staged, unstaged, and untracked changes. Deduplicate roots and record one `repository_context` per root:
    - `root`: absolute worktree root; `kind`: `parent`, `submodule`, or `subtree`.
    - `changed_paths`: paths relative to that root only; `framework`: detected per repository when Test is selected.
    - `codegraph`: `{ eligible, eligibility_reason, available, reason, index_root, backend, warnings, affected }`; initialise as `eligible: false`, `eligibility_reason: not-needed`, `available: unknown`, and an empty affected result. Do not check for CodeGraph here.
    - A Git submodule is always an independent context. A Git subtree without independent `.git` metadata is part of the parent context; do not create a false child context for it.
    - Derive `changed_repositories` from `repository_contexts` for Branch and Commit compatibility. Do not run `git stash`, inspect `refs/stash`, or include stashed content in any context.
12. **Guard: CLI quoting** — when running git commands on individual files, always quote paths: `git add "path/to/file.ts"`. For robust file iteration: use `git diff --name-only -z` on POSIX (null-separated, handles spaces/newlines in filenames). On PowerShell, skip `-z` (PowerShell's pipeline doesn't handle null bytes well); use `git status --porcelain` piped to `ForEach-Object` instead.
13. **Guard: Windows long paths** — on Windows, if `git add` silently fails on a valid file, check `git config core.longpaths`. If `false`, suggest: `git config core.longpaths true`.
14. **CodeGraph activation (optional, per repository)** · CodeGraph 按需启用（可选，按仓库）— never use a pipeline-global `codegraph_available` flag or detect CodeGraph merely because `.codegraph/` may exist. Set `repository_context.codegraph.eligible = true` only when one of these conditions applies: the user explicitly requests CodeGraph/affected tests/impact analysis; the selected review concerns a cross-module change, public API, route, core service, or unknown bug call chain; or a regression test selection would otherwise be broad, slow, or cross-package. Record the specific `eligibility_reason`.
    - For ordinary local changes, test-file-only changes, documentation/configuration-only changes, and narrow module tests, keep `eligible: false`; do not run `status`, `affected`, graph exploration, or the gate script.
    - Once eligible, run the gate below for that repository only. It sets `repository_context.codegraph.available = true` only when all three checks pass: an existing index, an executable CLI, and a healthy status response.
    1. **Index exists** · 索引存在:
       - POSIX: `test -f "<repository.root>/.codegraph/codegraph.db"`
       - PowerShell: `Test-Path (Join-Path "<repository.root>" ".codegraph/codegraph.db")`
    2. **CLI is executable** · CLI 可执行:
       - POSIX: `command -v codegraph >/dev/null 2>&1`
       - PowerShell: `$null -ne (Get-Command codegraph -ErrorAction SilentlyContinue)`
    3. **Index status is healthy** · 索引状态健康:
       - Run from the repository root, not the pipeline launch directory. POSIX: `(cd "<repository.root>" && codegraph status --json)`; PowerShell: `Push-Location "<repository.root>"; try { codegraph status --json } finally { Pop-Location }`.
       - Require exit code `0`, parseable JSON, and a usable index state. Record the reported backend. `native` is preferred; `wasm` remains usable but record the `wasm-backend` performance warning instead of disabling CodeGraph.
       - Treat command errors, invalid JSON, locked/corrupt state, or reported stale/pending data as unavailable.
    - Set `repository_context.codegraph.available = true` only if **all three checks pass**. Otherwise record `repository_context.codegraph.reason` as `index-missing`, `cli-missing`, or `status-unhealthy`, and use normal module/package test scoping for that repository.
    - Never use a parent repository's `.codegraph` index for a submodule. A submodule must have its own healthy index. A subtree uses its parent context and therefore its parent index.
    - **Do not install, initialize, or rebuild CodeGraph**. Do not run `codegraph install`, `codegraph init`, `codegraph index`, or `codegraph sync` automatically; availability detection must never modify the target repository or its CodeGraph state.
    - **Never fail the pipeline due to CodeGraph unavailability** — all downstream usage is conditional with fallback. · CodeGraph 不可用时管道不受影响。

Summarize: how many files changed, what type of change, impact scope, and CodeGraph activation only for eligible contexts (`not-needed`, `available`, `index-missing`, `cli-missing`, or `status-unhealthy`).
汇总告知用户：涉及几个文件、什么类型的变化、影响范围，以及 CodeGraph 的明确状态和不可用原因。
### CodeGraph Execution Gate · CodeGraph 执行门禁

For every Review or Test route, first apply the activation rule above. Only an eligible `repository_context` runs the bundled read-only gate **before** review prompts, review output, or regression-test selection. Run `python "<skill-dir>/scripts/codegraph_gate.py" --repository "<repository.root>"`; it records status, backend, the `git diff HEAD --name-only` input, `codegraph affected --stdin --json` result, exit code, and affected tests.

- Persist the result in `repository_context.codegraph.affected` with state `executed`, `empty`, or `failed`. `empty` is a successful execution with no selected tests; `failed` requires repository-local fallback plus its recorded error.
- If the context is not eligible, persist `affected.state = not-required` and continue with normal review or module-level testing. This is a complete lightweight path, not a degraded result.
- If the script cannot run, execute the repository-scoped `affected` command directly and record equivalent `cwd`, command, exit code, and test count. Never infer an empty result without executing it.
- **Completion invariant**: an eligible context that resolves to `available = true` with missing or `pending` evidence means Review/Test is incomplete. Do not launch review agents, report a completed review, or report a completed test run until every such context has `executed`, `empty`, or documented `failed` evidence.
- Re-run the gate after any review fix changes a repository before selecting its regression tests. Read `references/tooling.md` for exploration triggers, command selection, and the evidence schema.

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

**Note**: If Phase 0 forced 1B mode (large diff >500 lines), skip mode detection — go directly to 1B regardless of Agent tool availability.

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

**Optional CodeGraph gate before review**: First apply the activation rule. For each eligible context, satisfy the CodeGraph Execution Gate before constructing prompts. Append its root-labelled evidence and affected-test list to each prompt per Step 5 in `references/review-agents.md`. For a complex change, also run the context or impact exploration selected in `references/tooling.md` before reading broadly; append only its relevant findings. For an ineligible context, use normal lightweight review without CodeGraph.

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

Before starting the review, apply the activation rule. For each eligible context, satisfy the CodeGraph Execution Gate and use its root-labelled evidence block plus impacted-test list as reference context (see `references/review-checklist.md`). For an ineligible context, use normal lightweight review. For a complex change, use the context or impact exploration selected in `references/tooling.md` before broad file reads. A failure in one repository must not disable another repository's CodeGraph context.

---

### Post-Review Decision · 审查后决策

- 🔴 Blockers → ask user whether to fix before continuing
  - If user says yes: apply fixes → re-run Phase 1 review (verify fixes don't introduce new issues) → repeat until green
  - **Max 3 review cycles** — if blockers persist after 3 rounds, present remaining issues to user for manual decision (don't loop indefinitely)
- 🟡 Warnings only → note and continue; user decides
- All 🟢 → proceed directly to Phase 2

---

## Phase 2: Unit Test Generation · 单元测试生成

Generate unit tests based on the changed code. Read `references/test-generation.md` for language-specific guides.

### Test Necessity Check · 测试必要性判定

Before generating or running tests, produce a `test_decision` from staged, unstaged, and untracked files. Never inspect Git stash. Use the cheapest safe tier · 生成或运行测试前，根据已暂存、未暂存和未跟踪文件生成 `test_decision`，禁止读取 stash，并选择最低成本的安全层级：

| Tier | Change pattern | Required action |
|------|----------------|-----------------|
| `structural` | README, changelog, license, or `docs/` only | Skip unit tests; still run frontmatter, Markdown, link, and package validation |
| `unit` | Skill source, scripts, tests, CI, package, or unknown files | Run deterministic affected tests; generate tests for changed logic when needed |
| `agent-eval` | Review prompts/checklists or seeded eval fixtures | Run deterministic tests and recommend Agent evaluation; do not run it automatically in ordinary CI |

Rules:
1. Treat `.claude/skills/**/*.md` as product source, not documentation.
2. Default unknown files to `unit`; false negatives cost more than a small deterministic test run.
3. Run Agent evaluation only when explicitly requested, on a scheduled evaluation, or before a release. Record its token budget and actual token use.
4. If Phase 1 found a correctness/security issue or logic changed, generate targeted tests using the existing framework.
5. Even when generation is skipped, run affected regression tests when CodeGraph identifies them, independently for each repository context.

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
4. `*.xcodeproj` / `Package.swift`: XCTest (built-in), Quick/Nimble
5. Config files: `jest.config.*`, `vitest.config.*`, `pytest.ini`

**Fallback**: If no framework found, ask: "No test framework detected. Which framework do you use? (or skip test generation)"

### Output Placement

- JS/TS: `__tests__/` or co-located `*.test.ts`
- Python: `tests/` directory, `test_*.py`
- Java/Kotlin: `src/test/java/`, matching package path
- iOS/Swift: `*Tests.swift` in test target, matching source structure

**Pre-check**: In each repository context, check whether any tests exist: `git -C "<repository.root>" ls-files '*test*' '*spec*' '*__tests__*'` (cover JS/TS/Python/Java patterns). If that repository has zero existing tests, skip its regression check but still run any newly generated test file to verify it passes.

**Optional CodeGraph regression targeting (per repository)**: Before selecting regression tests, apply the activation rule. For each eligible context, satisfy the CodeGraph Execution Gate; re-run it if any files changed after review. Run each context's `affected.tests` with its detected framework from the same root instead of broader module scoping. `empty` means no graph-selected existing tests; `failed` or unavailable means fall back only for that context. Ineligible contexts use normal module scoping without CodeGraph. Include gate evidence only when the gate ran. See `references/test-generation.md` for details.

Run affected tests after generation to confirm no regressions AND verify the newly generated tests pass. **Scoping**: Run only tests in the changed module/package (e.g. `pytest tests/auth/`, `npm test -- --testPathPattern auth`), not the full suite. Abort and report if test suite exceeds 2-minute runtime.

### Test Result Report · 测试结果报告

Always report the following dimensions, including when unit tests are skipped:

- `test_decision`: selected tier, changed files, reasons, and whether unit/Agent evaluation ran;
- execution: total, passed, failed, errors, skipped, pass rate, and duration;
- coverage: requirement coverage and scenario coverage. For instruction-only skills, prefer behavioral coverage over misleading Markdown line coverage;
- quality: failed requirement/scenario identifiers and report artifact locations;
- cost: Agent evaluation status, token budget, and actual token usage (zero for deterministic-only runs).

Emit a concise console summary plus machine-readable JSON and human-readable Markdown reports. In CI, publish the Markdown to the step summary and upload both report files as artifacts.

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
| CI/CD config changes | `ci` | `ci: add node 22 to test matrix` |
| Reverting a previous commit | `revert` | `revert: feat(auth): add JWT token refresh` |
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

| Type | Branch Prefix | Base Branch | Example |
|------|---------|------|------|
| `feat` | `feature/` | `develop` | `feature/oauth2-integration` |
| `fix` | `bugfix/` | `develop` | `bugfix/order-discount-calculation` |
| Urgent production fix | `hotfix/` | `main`/`master` | `hotfix/crash-on-startup` |
| Release preparation | `release/` | `develop` | `release/v1.2.0` |
| `refactor` | `refactor/` | `develop` | `refactor/query-builder` |
| `docs` | `docs/` | `develop` | `docs/api-guide` |
| `perf` | `perf/` | `develop` | `perf/list-virtual-scroll` |
| `test` | `test/` | `develop` | `test/auth-coverage` |
| `chore` / `build` / `ci` / `deps` | `chore/` | `develop` | `chore/update-deps` |

### Steps

1. **Resolve the target repository before inspecting branches**:
   - Start from the `repository_contexts` recorded in Phase 0 and retain only contexts that own changes selected for this commit.
   - A Git submodule is an independent repository. A Git subtree without its own `.git` metadata belongs to the parent repository.
   - Do not run `git stash`, read `refs/stash`, or use stashed content to select a repository.
   - If exactly one repository remains, assign its absolute worktree root to `target_repo`.
   - If changes belong to multiple repositories, stop and ask the user to select one repository; list each repository and its changed paths. Never create branches in multiple repositories automatically.
2. **Scope every branch command** — from this point onward, every Git query or mutation in this phase must use `git -C "<target_repo>" ...`. Never rely on the pipeline launch directory.
3. Check current branch with `git -C "<target_repo>" rev-parse --abbrev-ref HEAD` (compatible back to Git 1.6; avoid `git branch --show-current`, which requires Git 2.22+).
4. **Guard: detached HEAD** — if the result is `HEAD`, warn: "HEAD is detached in <target_repo>. Creating a branch from a detached state may lose work. Create a branch from the current commit first?" Proceed only if the user confirms.
5. **Auto-detect branch convention**: run `git -C "<target_repo>" branch --list 'feature/*' 'bugfix/*' 'hotfix/*' 'fix/*'` to determine whether the selected repository uses Git-Flow or the conventional `fix/` style. Respect its existing convention and inform the user. · 自动检测并遵循目标仓库已有的 Git-Flow 或 `fix/` 分支命名规范
6. **Determine base branch** based on change type in `target_repo` · 根据目标仓库中的变更类型确定基准分支：
   - `hotfix/` → branch from `main` or `master` (urgent production fix)
   - `release/` → branch from `develop`
   - All others → branch from `develop` (or `main`/`master` if no `develop` branch exists)
7. If already on a matching branch (e.g. `feature/*` for a `feat` change) → commit directly.
8. **Guard: type mismatch** — if on `feature/*` but the change type is `fix`, suggest creating a `bugfix/` branch.
9. If on `main`/`master`/`develop` → recommend creating a new branch from the appropriate base.
10. **Hotfix detection**: if the current branch is `main`/`master` and the change type is `fix`, suggest `hotfix/` instead of `bugfix/` · 在 main/master 上修复 bug 时建议用 hotfix/
11. Mixed-type changes (e.g. feat+docs):
   - Branch prefix follows the primary change type (usually `feat`)
   - Inform user that docs/chore changes can follow the main branch or be split into a separate PR
12. **Guard: branch exists** — check with `git -C "<target_repo>" branch --list <branch-name>`. If it exists, append a numeric suffix such as `feature/jwt-refresh-2`.
13. Show `target_repo`, the recommended branch name, and the base branch together; ask for confirmation.
14. Run `git -C "<target_repo>" checkout -b <branch-name>` only after confirmation.

---

## Phase 5: Commit Execution · 执行提交

Phase 5 must inherit `target_repo` from Phase 4 when Branch is selected. In Commit Only mode, resolve `target_repo` directly from the matching Phase 0 `repository_context` before any mutation. If multiple repositories own selected changes, stop and ask the user to choose one. Every Git command in this phase must use the `git -C "<target_repo>" ...` form, including status, diff, staging, unstaging, and commit operations. Never fall back to the pipeline launch directory.

### Pre-Commit Checklist

- [ ] Code Review: no blockers, only when Review is selected or explicitly required
- [ ] Tests pass, only when Test is selected, generated tests changed, or an existing repository hook requires them
- [ ] Commit message confirmed by user
- [ ] Target repository resolved; branch selected/created only when Branch is selected
- [ ] No sensitive files (`.env`, `.pem`, credentials, etc.)

Do not add Review, Test, or Branch to `supporting_nodes` merely to satisfy this checklist. Commit Only intentionally skips them unless one of the conditions above applies.

**Sensitive file check**: Scan files to be committed (from `git -C "<target_repo>" status --short`) AND their diff content for: `.env` (unless `.env.example`), `*.pem`, `*.p12`, `*.pfx`, `credentials*`, `*secret*`, `*password*`, `BEGIN RSA PRIVATE KEY`, `BEGIN OPENSSH PRIVATE KEY`. If found → block commit, warn user, and unstage with `git -C "<target_repo>" rm --cached <file>` for already-staged files; for untracked files that were never staged, exclude them from `git -C "<target_repo>" add` and clear any intent-to-add entry with `git -C "<target_repo>" reset -- <file>`.

### Commit Steps

1. **Selective staging**: Run `git -C "<target_repo>" status --short` to enumerate ALL changes in the selected repository (staged + unstaged + untracked). Never use `git -C "<target_repo>" add -A` or `git -C "<target_repo>" add .`. Exclude binary files, generated files (`dist/`, `build/`, `*.generated.*`, `node_modules/`, `__pycache__/`), and sensitive files. Always quote paths: `git -C "<target_repo>" add "path/to/file.ts"`. For robust iteration, prefer `git -C "<target_repo>" status --porcelain`, which is parsing-friendly.
2. Show the file list AND the final commit message, ask for final confirmation (both files AND message together)
3. **Commit with multi-line message**:
   - **POSIX (Linux/macOS/Git Bash)**: Use multiple `-m` flags: `git -C "<target_repo>" commit -m "subject" -m "body paragraph" -m "footer"`
   - **PowerShell (Windows)**: Same multi-`-m` approach works. Do NOT embed `\n` in a single `-m` string — PowerShell renders it literally.
   - **Alternative**: Use a temporary file: `git -C "<target_repo>" commit -F /tmp/commit-msg.txt` (POSIX) or `git -C "<target_repo>" commit -F $env:TEMP\commit-msg.txt` (PowerShell)
4. Show result

### Pre-Commit Hook Failure · 预提交钩子失败

If `git -C "<target_repo>" commit` fails due to pre-commit hooks (linter, formatter, tests):

1. **Read the hook error output** — parse what failed and why
2. **Classify the failure** using pattern matching on the hook output:
   - **Auto-fixable**: output contains `eslint.*--fix`, `biome.*check.*--write`, `ruff.*--fix`, `prettier.*--write`, `ktlint.*-F`, `stylelint.*--fix`, `autopep8`, `black` → run the corresponding auto-fix command, then re-add and retry commit
     - NOTE: `checkstyle` is a reporting-only tool with no `--fix` — if only checkstyle errors appear, classify as Manual
   - **Manual**: output contains test failures (`FAIL`, `assertions failed`, `AssertionError`), type errors (`TS[0-9]`, `mypy.*error`, `pyright`), or complex lint rules with no auto-fix flag → show the error output, suggest fixes, ask user to resolve
   - **Infrastructure**: output contains `command not found`, `ModuleNotFoundError`, `cannot execute`, `permission denied`, hook script crash traces → report the issue, don't attempt auto-fix
   - **Unknown**: if the output doesn't clearly match any category → show it to the user and ask "Is this auto-fixable, or should I show the full error?"
3. **Retry**: After fixing, run `git -C "<target_repo>" add <fixed-files>` and `git -C "<target_repo>" commit` again (max 3 retries)
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
| **Full Pipeline** | "run the complete pipeline", "review, test, branch and commit" | Phase 0→1→2→3→4→5 |
| **Review Only** | "review my changes", "code review" | Lightweight Phase 0 + Phase 1; stop |
| **Test Only** | "generate tests", "run coverage" | Lightweight Phase 0 + Phase 2; stop |
| **Message Only** | "write commit message", "update changelog" | Change summary + Phase 3; stop |
| **Branch Only** | "create a feature branch", "name this branch" | Repository discovery + Phase 4; stop |
| **Commit Only** | "commit my changes", "stage and commit" | Repository/safety discovery + Phase 3 if needed + Phase 5; stop |
| **Combined Nodes** | "review and test", "branch then commit" | Explicit nodes + minimum dependencies; stop |

---

## Reference Files · 参考文件

- `references/review-agents.md` — 3 parallel agent prompts + coding standards checks (Claude Code)
- `references/review-checklist.md` — In-skill serial review checklist (universal fallback)
- `references/coding-standards.md` — **Authoritative coding standards**: Alibaba P3C, PEP 8, Airbnb JS, Vue 3, uni-app UTS, Android Kotlin, WCAG, Java 17+
- `references/tooling.md` — **Recommended static analysis toolchain**: ESLint, Ruff, Checkstyle, detekt, Biome, CodeGraph, and more
- `scripts/codegraph_gate.py` — **Required CodeGraph evidence gate** for available repositories before Review/Test completion
- `references/test-generation.md` — Test generation guides for JS/TS/Python/Java/Kotlin
- `references/commit-conventions.md` — Conventional Commits spec with dual-style branch naming
