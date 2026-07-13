# Conventional Commits Spec · 规范

Commit message conventions based on the [Conventional Commits 1.0.0](https://www.conventionalcommits.org/) standard.
基于 Conventional Commits 1.0.0 标准的提交信息规范。

## Basic Format · 基本格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

- **type**: required — change type · 必填，变更类型
- **scope**: optional — affected area · 可选，影响范围
- **subject**: required — short description, max 70 chars in English (35 chars in Chinese) · 必填，简短描述（英文 70 字符以内，中文 35 字以内）
- **body**: optional — detailed description, wrap at 72 chars per line · 可选，详细描述（每行 72 字符以内）
- **footer**: optional — issue refs / breaking change notes · 可选，关联 issue / 破坏性变更说明

## Type Reference · 类型速查表

| type | 说明 | 使用场景 |
|------|------|---------|
| `feat` | 新功能 | 新增 API、组件、页面、功能模块 |
| `fix` | Bug 修复 | 修复逻辑错误、崩溃、异常、行为不正确 |
| `docs` | 文档变更 | README、注释、API 文档（不包含代码行为变更） |
| `style` | 代码风格 | 格式化、缺失分号、引号统一（不影响代码逻辑） |
| `refactor` | 重构 | 代码结构优化，不增加功能也不修复 bug |
| `perf` | 性能优化 | 提升性能的代码变更 |
| `test` | 测试 | 添加/修改测试代码（不包含被测代码的变更） |
| `deps` | 依赖更新 | 仅升级/降级依赖版本（lockfile 变更） |
| `build` | 构建系统 | 构建工具/脚本变更（非依赖版本） |
| `ci` | CI/CD | CI 配置文件、脚本变更 |
| `chore` | 杂项 | 不修改 src 或 test 的其他变更（如 .gitignore） |
| `revert` | 回退 | 回退之前的提交 |

## Scope Inference · Scope 推断规则

Infer scope automatically from file paths · 从文件路径自动推断 scope：

| 文件路径 | 推断 scope |
|----------|-----------|
| `src/auth/login.ts` | `auth` |
| `src/components/Button/index.tsx` | `button` |
| `src/api/user/routes.py` | `user` |
| `src/main/java/com/x/order/OrderService.java` | `order` |
| `packages/utils/src/date.ts` | `date` 或 `utils` |
| `docs/guide/getting-started.md` | `guide` |
| `src/auth/*`, `src/api/auth/*` 同时变更 | `auth` |
| 跨多个无关联模块 | 省略 scope 或取最高层 |

## Subject Rules · Subject 编写规则

- Imperative mood, present tense ("add" not "added") · 使用祈使句，现在时（"添加" 而非 "添加了"）
- Lowercase first letter for English · 首字母小写（中文直接写，英文小写开头）
- No trailing period · 结尾不加句号
- Concise: max 70 characters in English, 35 in Chinese · 简短精炼（英文 70 字符以内，中文 35 字以内）

```
✅ feat(auth): add JWT token refresh
✅ fix(order): fix total calculation with discount
✅ docs(api): update authentication guide
✅ refactor(db): extract query builder to shared module

❌ feat(auth): Added JWT token refresh.  （过去式 + 句号）
❌ FIX: 修复了一个订单计算的bug，当折扣和优惠券同时存在时总价不对（太长，格式不对）
```

## Body Rules · Body 编写规则

Add a body when the subject alone can't explain the change · 当 subject 不足以说清楚变更时，添加 body：

- Explain **why**, not how — the code already shows how · 解释 **为什么** 做这个变更（而非怎么做——代码已经说了）
- Wrap at 72 characters per line · 每行 72 字符以内
- Blank line between subject and body · 与 subject 之间空一行

```
fix(order): fix total calculation with stacked discounts

Previously, applying a percentage discount after a fixed discount
would calculate against the original price instead of the already
discounted price, resulting in incorrect totals.

The fix applies discounts sequentially in the order they were added.
```

## Footer Rules · Footer 编写规则

### Breaking Changes · 破坏性变更

Add `BREAKING CHANGE:` when the change is not backward compatible (API signature changes, config renames, behavior changes that break downstream).
当变更不向后兼容时（API 签名变更、配置重命名、行为变更导致下游破裂），添加 `BREAKING CHANGE:`。

```
feat(api): change login response format

BREAKING CHANGE: The login endpoint now returns `token` instead of
`accessToken` in the response body. All clients must update.
```

或使用类型标记 `!`（简写）：

```
feat(api)!: change login response format
```

### Issue References · 关联 Issue

```
fix(auth): resolve token expiration race condition

Closes #234
Refs #123
```

## Branch Naming · 分支命名规范

Two supported styles — pick one per project · 支持两种风格，项目统一选择一种：

**Style A: Semantic prefix (recommended — dev-pipeline default) · 风格 A：语义前缀**

| 提交类型 | 分支前缀 | 示例 |
|---------|---------|------|
| `feat` | `feature/` | `feature/oauth2-integration` |
| `fix` | `fix/` | `fix/order-discount-calculation` |
| `refactor` | `refactor/` | `refactor/query-builder-extract` |
| `docs` | `docs/` | `docs/api-authentication` |
| `perf` | `perf/` | `perf/list-virtual-scroll` |
| `chore` / `build` / `deps` | `chore/` | `chore/update-dependencies` |
| `test` | `test/` | `test/auth-coverage` |

**Style B: Direct type alignment (common in the Conventional Commits ecosystem) · 风格 B：类型直接对齐**

| 提交类型 | 分支前缀 | 示例 |
|---------|---------|------|
| `feat` | `feat/` | `feat/oauth2-integration` |
| `fix` | `fix/` | `fix/order-discount-calculation` |
| `deps` | `deps/` | `deps/bump-axios` |

**Style C: Git-Flow (strict) · 风格 C：Git-Flow 严格规范**

| 提交类型 | 分支前缀 | 基准分支 | 示例 |
|---------|---------|---------|------|
| `feat` | `feature/` | `develop` | `feature/oauth2-integration` |
| `fix` | `bugfix/` | `develop` | `bugfix/order-discount-calculation` |
| 紧急生产修复 | `hotfix/` | `main`/`master` | `hotfix/crash-on-startup` |
| 发布准备 | `release/` | `develop` | `release/v1.2.0` |
| `refactor` | `refactor/` | `develop` | `refactor/query-builder` |
| `docs` | `docs/` | `develop` | `docs/api-guide` |
| `perf` | `perf/` | `develop` | `perf/list-virtual-scroll` |
| `chore`/`build`/`deps` | `chore/` | `develop` | `chore/update-deps` |

Git-Flow rules (additional) · Git-Flow 额外规则：
- `bugfix/` replaces `fix/` — Git-Flow uses `bugfix/` for non-urgent bug fixes · Git-Flow 用 `bugfix/` 而非 `fix/`
- `hotfix/` branches from `main`/`master` — for urgent production fixes only · 仅用于紧急生产修复，从 main/master 分出
- `release/` branches from `develop` — for release stabilization · 用于发布稳定化，从 develop 分出
- After merge, feature/bugfix/hotfix branches are deleted · 合并后删除分支
- `develop` is the integration branch; `main`/`master` is production-ready · develop 为集成分支，main/master 为生产分支

Branch name rules (all styles) · 分支名规则（所有风格通用）：
- All lowercase, kebab-case · 全小写，kebab-case
- Short and descriptive, 3-5 words · 简短描述性（3-5 词）
- Max 50 characters · 50 字符以内

## Full Examples · 完整示例

### Example 1: New feature · 新功能
```
feat(user): add avatar upload with resize

Supports JPG and PNG uploads up to 5MB.
Images are automatically resized to 200x200.
```

### Example 2: Bug fix · Bug 修复
```
fix(cart): handle expired session during checkout

When a session expires mid-checkout, the cart was being cleared
instead of preserved. Session recovery now restores the cart state.

Closes #567
```

### Example 3: Refactor · 重构
```
refactor(payment): replace stripe SDK with payment adapter

Introduces PaymentAdapter interface to decouple payment provider.

BREAKING CHANGE: PaymentService.create() now requires a
PaymentAdapter instance instead of Stripe API key.
```

### Example 4: Docs · 文档
```
docs(readme): add local development setup guide
```

### Example 5: Simple fix · 简单修复
```
fix: fix typo in error message
```

## Anti-Patterns · 错误模式（避免）

| Wrong · 错误 | Right · 正确 |
|------|------|
| `Added login feature` | `feat(auth): add login feature` |
| `fix bug` | `fix(api): handle null response body` |
| `WIP` / `save` / `tmp` | Never commit messages like these · 永远不要提交这样的信息 |
| `feat: add feature and fix bug and update docs` | Split into separate commits · 拆分为多个独立提交 |
| One commit with 50 unrelated files · 一个提交包含 50 个不相关的文件 | Group logically, commit separately · 按逻辑分组，多次提交 |
