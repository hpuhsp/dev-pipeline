---
name: dev-pipeline
description: >
  多步骤代码交付管道：代码审查 → 单元测试 → Commit Message → 分支选择 → 提交。
  Use this skill whenever the user has finished coding and needs to commit/ship their changes —
  it handles the full pipeline from review through commit. Proactively invoke when the user says
  they've completed code changes ("改完了", "写好了", "提交代码") even if they don't explicitly
  ask for review or testing, because this skill ensures every commit is reviewed, tested, and
  properly formatted. Also invoke for any single step of the pipeline: code review against
  authoritative standards (Alibaba P3C, PEP 8, Airbnb JS, Vue, uni-app UTS), unit test
  generation with auto-detected frameworks, Conventional Commits message generation, branch
  naming, or the complete delivery workflow. Triggers include: "提交代码", "帮我提交",
  "review我的改动", "做code review", "审查代码", "生成测试", "写commit message",
  "写changelog", "选分支", "ship it", "代码写好了", "改完了", "检查代码规范",
  "跑流水线", "dev pipeline". Especially valuable for multi-file changes that need
  systematic review, proper testing, and standardized commit history.
---

# 开发流水线 (Dev Pipeline)

一站式日常开发工作流。审查阶段在 Claude Code 环境自动启用 3-agent 并行审查，其他环境退化为 Skill 内串行审查。后续阶段统一串行执行。

## 工作流概览

```
git diff/staged
  │
  ├─ ① 代码审查 ──── Claude Code: 3 Agent 并行
  │                  其他环境:   Skill 内串行
  │
  ├─ ② 单元测试生成
  ├─ ③ 变更日志 / Commit Message
  ├─ ④ 分支选择
  └─ ⑤ 执行提交
```

每一步输出是下一步的输入。遇到失败或用户否定，暂停管道，修复后继续。

---

## 阶段 0：环境感知

在开始任何操作前，先摸清项目状态：

1. 运行 `git status` 了解变更范围（已暂存 / 工作区 / 未跟踪文件）
2. 运行 `git diff` 和 `git diff --staged` 获取完整 diff
3. 检测项目的技术栈（用一个 Glob 批量检测所有关键文件）：
   - `package.json`、`tsconfig.json` → JS/TS 项目
   - `pyproject.toml`、`setup.py`、`requirements*.txt` → Python 项目
   - `pom.xml`、`build.gradle`、`build.gradle.kts` → Java/Kotlin 项目
   - `.editorconfig`、`.eslintrc.*`、`.prettierrc*` → 代码风格工具
   - 同时检查 `vue`、`react`、`next`、`uni-app` 相关依赖确认前端框架
   - **并行检测**：用 `Glob` 一次性搜索全部关键文件，减少串行等待

将这些信息汇总，简要告知用户变更范围（涉及几个文件、什么类型的变化、影响范围）。

### 阶段 0.5：Scope Drift 检测（可选）

当项目根目录存在 `TODOS.md` 或 `.plan` 文件时，快速检测变更范围是否偏离计划：

1. 如果存在 `TODOS.md`：检查 diff 中文件是否匹配 TODO 条目的描述
2. 如果 git log 有明确的功能描述：检查是否有无关文件被顺带修改（"while I was in there..."）
3. 输出格式：
   ```
   Scope Check: CLEAN | DRIFT DETECTED | NEEDS REVIEW
   Intent: <本次变更的意图（1 句）>
   Delivered: <diff 实际内容（1 句）>
   ```
4. 如果 DRIFT DETECTED：标注那些与意图无关的文件，询问用户是否应分开提交
5. 如果 CLEAN 或无 TODOS.md/.plan：直接进入阶段 1

---

## 阶段 1：代码审查 (Dual Mode)

### 模式检测

检查你是否拥有 **Agent 工具**（查找工具列表中的 `Agent`）。

- **有 Agent 工具** → 执行 [1A: 并行 Agent 审查]
- **无 Agent 工具** → 执行 [1B: Skill 内串行审查]

---

### 1A: 并行 Agent 审查（Claude Code）

**核心原则**：一次消息中并行启动 3 个 Agent，每个 Agent 有独立的上下文窗口，从不同维度审查同一份 diff。

#### 前置准备

读取 `references/review-agents.md`，其中包含 3 个 Agent 的完整 prompt。

#### 启动方式

**必须在同一条消息中同时启动 3 个 Agent**（不要逐个启动，会浪费等待时间）：

```
Agent 1 (security-correctness): 审查安全漏洞、逻辑错误、空值处理、边界条件
Agent 2 (performance-efficiency):  审查性能问题、N+1 查询、内存泄漏、不必要的计算
Agent 3 (maintainability-style):   审查命名、代码重复、架构一致性、编码规范合规
```

每个 Agent 的 prompt 从 `references/review-agents.md` 中获取对应的完整版本，并将本次 `git diff` 作为输入传入。

每个 Agent 使用 `subagent_type: "general-purpose"`，不需要 `Explore` 类型（审查是分析任务，不是搜索任务）。

#### 聚合结果 + Fix-First 分类

等待全部 3 个 Agent 返回后，对每个 finding 做二次分类，然后聚合输出。

**Fix-First 分类规则**：

对每个 finding 的 `fix:` 标签进行审核：
- `AUTO`：可机械修复的问题（重命名、提取常量、添加空检查、修复格式）→ 自动应用修复，输出 `[AUTO-FIXED]`
- `ASK`：需用户决策的问题（架构变更、API 变更、破坏性修改）→ 聚合为用户选择列表
- 如果 Agent 未标注 fix，按以下默认规则：命名/格式/空检查 → AUTO；逻辑变更/架构/安全/性能 → ASK

**置信度门控**：
- 置信度 ≥ 7 → 展示在主体报告中
- 置信度 5-6 → 展示但标注 "中等置信度，请验证"
- 置信度 3-4 → 移至附录（不阻塞管道）
- 置信度 1-2 → 抑制（不展示）

**聚合输出格式**：

```
## Code Review 结果 (Parallel 3-Agent)

### 🔴 阻塞项 (必须修复)
- [ ] [AUTO-FIXED] file:line — 问题 → 已自动修复 (Agent N, conf: X/10)
- [ ] [NEEDS DECISION] file:line — 问题 → 推荐修复方案 (Agent N, conf: X/10)
  ...

### 🟡 建议项 (推荐修复)
- [ ] [AUTO-FIXED] file:line — 问题 → 已自动修复 (Agent N, conf: X/10)
- [ ] file:line — 问题 → 修复建议 (Agent N, conf: X/10)
  ...

### 🟢 通过项
- 无安全风险 (Agent 1 ✅)
- 性能良好 (Agent 2 ✅)
- 代码风格符合规范 (Agent 3 ✅) [编码规范: {匹配的标准}]

### 附录 — 低置信度发现
- (conf: 4/10) file:line — 描述 (Agent N)

### 总体评分: X/10
  - 安全性+正确性: X/10 (Agent 1)
  - 性能+效率:     X/10 (Agent 2)
  - 可维护性+规范: X/10 (Agent 3)
  - 编码规范合规:  X/10 (Agent 3, 依据 coding-standards.md)
```

**去重规则**：多个 Agent 提到同一问题时，合并为一条，标注所有来源。以最高置信度为准。

**冲突处理**：Agent 之间意见不同时，标注冲突并给出你的判断，请用户裁定。

---

### 1B: Skill 内串行审查（其他 AI Agent）

当 Agent 工具不可用时，自己执行审查。阅读 `references/review-checklist.md` 获取完整清单。

逐维度审查（正确性 → 安全性 → 性能 → 可维护性 → 一致性），输出格式与 1A 一致，但来源标注为 "Skill 内审查"。

---

### 审查后决策

- 存在 🔴 阻塞项 → 征询用户是否修复后再继续
- 仅 🟡 建议项 → 标注后继续管道，用户自行决定
- 全部 🟢 → 直接进入阶段 2

---

## 阶段 2：单元测试生成

根据变更代码生成单元测试。阅读 `references/test-generation.md` 获取各语言测试生成指南。

### 原则

- **不测试第三方库**：只测试你写的代码，不测试框架或库的行为
- **关注边界**：正常路径 + 边界条件 + 错误路径
- **一个测试一个行为**：每个测试只验证一件事情
- **使用项目已有框架**：不引入新测试框架

### 框架检测

按优先级检测：
1. `package.json` 的 devDependencies/dependencies: `jest`、`vitest`、`mocha`
2. `pyproject.toml` 或 `setup.cfg`: `pytest`、`unittest`
3. `pom.xml` 或 `build.gradle`: `junit`、`testng`、`mockito`
4. 项目根目录的配置文件（`jest.config.*`、`vitest.config.*`、`pytest.ini`）

### 输出

测试文件放置在项目约定位置：
- JS/TS: `__tests__/` 或与源文件同目录的 `*.test.ts`
- Python: `tests/` 目录下 `test_*.py`
- Java/Kotlin: `src/test/java/` 下对应包路径

测试生成后，运行现有测试套件确保未引入回归。

---

## 阶段 3：变更日志 / Commit Message

基于 Conventional Commits 规范生成提交信息。阅读 `references/commit-conventions.md`。

### 类型自动推理

| 变更特征 | 类型 | 示例 |
|---------|------|------|
| 新增文件/函数/组件/API | `feat` | `feat(auth): add JWT token refresh` |
| 修复已有的逻辑/行为 | `fix` | `fix(api): handle null response body` |
| 仅改动文档/注释 | `docs` | `docs(readme): update install guide` |
| 依赖版本升级/降级 | `deps` | `deps: bump axios to 1.7.0` |
| 格式化/引号/分号等风格调整 | `style` | `style: format with prettier` |
| 重构（不改变行为） | `refactor` | `refactor(db): extract query builder` |
| 性能优化 | `perf` | `perf(list): add virtual scrolling` |
| 测试相关 | `test` | `test(auth): add 2FA coverage` |
| 构建/配置/杂项 | `build` / `chore` | `chore: update .gitignore` |

### scope 推理

- 从变更文件路径推断 scope（如 `src/auth/login.ts` → `auth`）
- 多文件变更取共同的顶层模块作为 scope
- 范围太广时省略 scope

### 破坏性变更

检测到 API 签名变更、配置重命名、返回值类型变化时，在 footer 添加 `BREAKING CHANGE:`。

### 输出格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

展示给用户确认，用户可直接编辑修改。

---

## 阶段 4：分支选择

| 类型 | 分支前缀 | 示例 |
|------|---------|------|
| `feat` | `feature/` | `feature/jwt-token-refresh` |
| `fix` | `fix/` | `fix/null-response-handling` |
| `refactor` | `refactor/` | `refactor/query-builder` |
| `docs` | `docs/` | `docs/install-guide` |
| `perf` | `perf/` | `perf/virtual-scroll` |
| `chore` / `build` | `chore/` | `chore/update-deps` |

### 操作

1. 检查当前分支（`git branch --show-current`）
2. 如果已是 `feature/*` 或 `fix/*` 且与变更匹配 → 直接在当前分支提交
3. 如果在 `main`/`master`/`develop` → 推荐创建新分支
4. 多类型混合变更（如 feat+docs）：
   - 分支以前缀对应主要变更类型（通常是 `feat`）
   - 提示用户 docs/chore 类变更可跟随主分支提交，或拆分为独立 PR
5. 展示推荐的分支名并请用户确认
6. 执行 `git checkout -b <分支名>`（用户确认后）

---

## 阶段 5：执行提交

### 提交前检查清单

- [ ] Code Review 无阻塞项
- [ ] 测试已生成且现有测试全部通过
- [ ] Commit message 已经用户确认
- [ ] 分支已选择/创建
- [ ] 无敏感文件（`.env`、`.pem`、credentials 等）

### 提交流程

1. **选择性暂存**：`git add <files>`（不用 `git add -A`）
2. 展示将要提交的文件清单，请用户最终确认
3. `git commit -m "<generated message>"`
4. 展示结果

```
✅ 提交成功
   Branch: feature/jwt-refresh
   Commit: a1b2c3d feat(auth): add JWT token refresh

   下一步:
   - git push origin feature/jwt-refresh
   - 或者让我帮你创建 PR
```

---

## 模式速查

| 模式 | 触发词 | 行为 |
|------|--------|------|
| **完整管道** | "提交代码"、"ship it" | 阶段 0→1→2→3→4→5 |
| **快速模式** | "快速提交"、"skip review" | 仅 阶段 3→4→5 |
| **单步-审查** | "review 我的改动" | 仅阶段 1 |
| **单步-测试** | "生成测试" | 仅阶段 2 |
| **单步-消息** | "生成 commit message" | 仅阶段 3 |

---

## 参考文件

- `references/review-agents.md` — 3 个并行 Agent 的完整 prompt + 编码规范检查（Claude Code 专用）
- `references/review-checklist.md` — Skill 内串行审查清单（通用回退）
- `references/coding-standards.md` — **权威编码规范速查**（阿里 P3C、PEP 8、Airbnb JS、Android Kotlin、Vue、uni-app UTS、WCAG 等）
- `references/tooling.md` — **推荐静态分析工具链**（ESLint、Ruff、Checkstyle、detekt、Biome 等）
- `references/test-generation.md` — 各语言测试生成指南
- `references/commit-conventions.md` — Conventional Commits 详细规范
