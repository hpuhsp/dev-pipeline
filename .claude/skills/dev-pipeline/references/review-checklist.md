# Code Review Checklist (1B — In-Skill Serial Fallback)

Language-agnostic code review checklist. When the Agent tool is unavailable, review the diff yourself following this checklist. Output format matches the 1A parallel mode.
语言无关的代码审查清单。当 Agent 工具不可用时，按此清单自行审查，输出格式对齐 1A 并行模式。

## Multi-Pass Review Approach · 多轮审查

To approximate the depth of 3-agent parallel review, run 3 independent passes, each focused on one dimension:
为模拟 3-Agent 并行审查的深度，分 3 轮独立审查，每轮聚焦一个维度：

- **Pass 1**: Correctness + Security · 正确性 + 安全性（对应 Agent 1）
- **Pass 2**: Performance + Efficiency · 性能 + 效率（对应 Agent 2）
- **Pass 3**: Maintainability + Coding Standards · 可维护性 + 编码规范（对应 Agent 3）

Score each pass independently (SCORE: X/10), then aggregate at the end.
每轮结束后独立打分（SCORE: X/10），最后聚合。

> **CodeGraph execution gate (eligible repositories only)**: Apply the activation rule first. Run `python "<skill-dir>/scripts/codegraph_gate.py" --repository "<repository.root>"` only for eligible contexts and retain the JSON result. An eligible available context is review-ready only after `affected.state` is `executed`, `empty`, or documented `failed`; `pending` or absent evidence makes that review incomplete. Keep all test paths repository-relative and labelled by root. Ineligible contexts skip CodeGraph entirely and use the normal checklist. A failed context uses local fallback and never suppresses another context.

## Unified Output Format (aligned with 1A) · 统一输出格式

For each finding · 对每个发现使用：
```
[BLOCKER|WARNING] (confidence: N/10, fix: AUTO|ASK) file:line — problem → suggested fix
```

- **SEVERITY**: `BLOCKER` (must fix · 必须修复) or `WARNING` (should fix · 推荐修复)
- **confidence**: 1-10. 9-10=verified · 已验证; 7-8=high confidence · 高置信; 5-6=possible false positive · 可能误报; 3-4=speculative, move to appendix · 推测（移至附录）; 1-2=suppress · 极低（抑制）
- **fix**: `AUTO`=mechanically fixable (rename, format, null check, extract constant · 重命名、格式化、null 检查、提取常量等机械操作); `ASK`=needs user decision (architecture, API changes, performance trade-offs · 架构变更、API 变更、性能权衡)

### AUTO vs ASK Classification Guide · 分类指南

| Finding type · 发现类型 | Classify as · 分类为 | Reason · 原因 |
|---------|--------|------|
| Non-standard variable/function naming · 命名不规范 | AUTO | Mechanical rename · 机械重命名 |
| Extract magic value to constant · 提取魔法值为常量 | AUTO | Mechanical extraction · 机械提取 |
| Add null/undefined check · 添加 null 检查 | AUTO | Mechanical: `?.` / `if not None` · 机械添加 |
| Fix `==` to `===` | AUTO | Mechanical replacement · 机械替换 |
| Add `@Override` annotation · 添加注解 | AUTO | Mechanical addition · 机械添加 |
| Fix formatting (indent, spacing, line breaks) · 修复格式 | AUTO | Run formatter · 运行格式化工具 |
| Remove unused imports/variables · 删除未使用的 import/变量 | AUTO | Mechanical deletion · 机械删除 |
| Fix mutable default argument · 修复可变默认参数 | AUTO | Mechanical pattern swap · 机械替换模式 |
| **Architecture refactoring · 架构重构** | **ASK** | Design trade-offs · 需权衡设计 |
| **API signature change · API 签名变更** | **ASK** | May break downstream · 可能破坏下游 |
| **Security policy change · 安全策略变更** | **ASK** | Needs security assessment · 需安全评估 |
| **Performance trade-off · 性能权衡** | **ASK** | Needs business context · 需业务上下文 |
| **New/replaced framework or library · 新增/替换框架或库** | **ASK** | Needs team consensus · 需团队共识 |

## Pass 1: Correctness + Security · 正确性 + 安全性

### Correctness Checks · 正确性检查

- **Null handling · 空值处理**: Are external inputs, API responses, and DB query results checked for null/undefined?
  - JS/TS: optional chaining `?.`, nullish coalescing `??`, type guards
  - Python: `is None` checks, `dict.get()` instead of `dict[key]`
  - Java: `Optional` or explicit null checks
- **Edge cases · 边界条件**: Empty arrays, empty strings, zero, negative numbers, max values handled?
- **Async operations · 异步操作**: Promises/async correctly awaited? Errors caught?
  - JS/TS: missing `await`, `.catch()`, or `try/catch`?
  - Python: `async/await` correct? Coroutines properly scheduled?
  - Java: `CompletableFuture` exception handling?
- **Type safety · 类型安全**: Are type conversions safe? Implicit coercion bugs?
- **Loops/recursion · 循环/递归**: Termination conditions correct? Infinite loop or stack overflow possible?
- **Logic errors · 逻辑错误**: Off-by-one, inverted conditions (&& vs ||), wrong operators
- **Race conditions · 竞争条件**: Shared mutable state accessed concurrently without synchronization? JS setState after await without checking component is still mounted?
- **Resource cleanup · 资源清理**: File handles, connections, event listeners released?

### Security Checks · 安全检查

- **Injection risks · 注入风险**: User input concatenated into SQL / Shell / HTML?
  - Parameterized queries instead of string concatenation? · 是否使用参数化查询而非字符串拼接
  - Template engine auto-escaping enabled? · 模板引擎是否启用自动转义
- **Sensitive data · 敏感信息**: Hardcoded keys, tokens, passwords, connection strings?
  - Search keywords · 搜索关键词: `password`, `secret`, `token`, `api_key`, `private_key`, `BEGIN RSA`
- **Authorization · 权限控制**: New endpoints have proper permission checks? Privilege escalation possible?
- **Input validation · 输入验证**: External inputs validated (length, format, range)?
- **Dependency security · 依赖安全**: New third-party dependencies with known vulnerabilities?
- **Unsafe deserialization · 不安全反序列化**: `pickle.loads()`, `eval()`, `JSON.parse()` on untrusted input?
- **Path traversal · 路径穿越**: File paths built from user input without sanitization?

### Common Error Patterns · 常见错误模式

```
❌ JS:   const data = JSON.parse(response.body); // body 可能是 null
✅ JS:   const data = JSON.parse(response.body ?? '{}');

❌ Python: value = config['timeout']  # KeyError
✅ Python: value = config.get('timeout', 30)

❌ Java: String name = user.getName().toUpperCase(); // NPE
✅ Java: String name = Optional.ofNullable(user).map(User::getName).map(String::toUpperCase).orElse("");
```

Label each finding · 每项发现标注：[BLOCKER|WARNING] (confidence, fix) file:line
End of Pass 1 · Pass 1 结束: SCORE: X/10

---

## Pass 2: Performance + Efficiency · 性能 + 效率

### Performance Checks · 性能检查

- **N+1 queries · N+1 查询**: Database queries or remote API calls inside loops?
- **Unnecessary work · 不必要的工作**: Hoistable computations in loops? Repeated file reads / network requests? Regex recompiled inside loops?
- **Missed concurrency · 错过并发**: Independent I/O run sequentially? Multiple parallelizable awaits → `Promise.all` / `asyncio.gather`?
- **Hot-path bloat · 热路径膨胀**: Synchronous I/O on startup or per-request paths? Heavy re-initialization in frequently-called constructors?
- **Unnecessary allocations · 不必要分配**: Large object/array copies? `Array.map().filter().reduce()` chains → single-pass reduce? String concatenation in loops → join/StringBuilder?
- **Memory leaks · 内存泄漏**:
  - JS/TS: uncleaned event listeners, setInterval, closure references, unbounded Map caches without eviction
  - Python: reference cycles, unclosed file handles
  - Java: unclosed Stream/Connection
- **Overly broad operations · 过宽操作**: Reading entire files / loading all records when only a few are needed?
- **Algorithm complexity · 算法复杂度**: O(n²) where O(n log n) or O(n) would do?
- **TOCTOU**: Check-then-act → operate directly and handle the error instead · 先检查存在再操作 → 应直接操作并处理错误
- **No-op updates · 无操作更新**: State updates firing unconditionally? Add change-detection guard
- **Lazy loading · 懒加载**: Heavy imports convertible to dynamic/lazy? `React.lazy()`, dynamic `import()`

Label each finding · 每项发现标注：[BLOCKER|WARNING] (confidence, fix) file:line
End of Pass 2 · Pass 2 结束: SCORE: X/10

---

## Pass 3: Maintainability + Coding Standards · 可维护性 + 编码规范

### Naming & Function Design · 命名与函数设计

- Do names express intent? Avoid `data`, `tmp`, `result`, `item`, `obj`, `val`, `handle`, `process` · 变量/函数名是否表达意图
- Booleans prefixed with `is`/`has`/`should`/`can`? · 布尔值前缀
- Function names start with a verb? · 函数名以动词开头
- Any function over 30 lines? Consider splitting · 单个函数超过 30 行考虑拆分
- Function doing multiple things? "And" in the name is a bad signal · 函数名中的 "and" 是坏信号
- More than 4 parameters? Consider a config object · 参数超过 4 个考虑用对象参数

### Code Quality · 代码质量

- Copy-pasted blocks? Extract shared logic of 3+ identical lines · 3 行以上相同逻辑应提取
- Existing utility functions that could be reused? · 是否有可复用的已有工具函数
- Leaky abstractions exposing internals? · 泄漏抽象暴露内部细节
- Empty catch blocks? `except: pass`? Overly broad exception handling? · 空 catch 块、过宽异常捕获
- Stringly-typed code: raw strings where enum/constant/union fits? · 裸字符串应改用 enum/常量/union
- Nested conditionals: 3+ levels of if/else, ternary chains → early return / guard clause / lookup table · 嵌套条件 → 早期返回
- Useless comments: WHAT comments (names already say it) → delete; keep only WHY · 注释说 WHAT → 删除，仅保留 WHY
- Dead code: commented-out blocks, unreachable branches, unused imports? · 死代码

### Coding Standards Compliance · 编码规范合规

**Read `references/coding-standards.md`** — only the section matching the detected tech stack, and check every mandatory rule.
读取其中与检测到的技术栈匹配的章节，逐一核对每条强制性规则。

- Mandatory standard violation → BLOCKER · 违反强制性规范
- Recommended standard violation → WARNING · 违反推荐规范

By language · 按语言优先级：
| Language · 语言 | Standards · 审查依据 | Key checks · 关键检查项 |
|------|---------|-----------|
| Java | P3C + Google Java Style + Java 17+ | @Override, naming, equals(), date API, Optional, exceptions |
| Kotlin | Android Kotlin Style + detekt + Compose + Coroutines | val/var, !!, when, scope functions, Compose patterns |
| JS/TS | Airbnb + Google TS Style | const/let/var, ===, any, type annotations, destructuring |
| React | React conventions | component naming, hooks, key, useEffect deps |
| Vue 3 | Vue Style Guide A/B/C | multi-word names, props, v-for :key, computed, ref |
| Python | PEP 8 + PEP 257 + Google | snake_case, is None, mutable defaults, f-strings |
| Web/CSS | WCAG 2.1 AA + BEM | alt, label, contrast, keyboard, semantic HTML |

### Consistency · 一致性

- Error handling pattern consistent with the project? · 错误处理模式与项目一致
- Logging style consistent with the project? · 日志方式与项目一致
- File/directory naming follows project conventions? · 文件/目录命名与项目约定一致
- Import order consistent with the project? · import 顺序与项目一致

Label each finding · 每项发现标注：[BLOCKER|WARNING] (confidence, fix) file:line
End of Pass 3 · Pass 3 结束: MAINTAINABILITY+STYLE SCORE: X/10, CODING STANDARDS COMPLIANCE SCORE: X/10

---

## Aggregate Output (aligned with 1A) · 聚合输出

```
## Code Review Results (In-Skill Serial Review)

### 🔴 Blockers (must fix)
- [ ] [AUTO-FIXED] file:line — problem → auto-fixed (Pass N, conf: X/10)
- [ ] [NEEDS DECISION] file:line — problem → recommended fix (Pass N, conf: X/10)
  ...

### 🟡 Warnings (should fix)
- [ ] [AUTO-FIXED] file:line — problem → auto-fixed (Pass N, conf: X/10)
- [ ] file:line — problem → fix suggestion (Pass N, conf: X/10)
  ...

### 🟢 Passing
- No correctness/security issues (Pass 1 ✅)
- No performance issues (Pass 2 ✅)
- Code style compliant (Pass 3 ✅)

### Appendix — Low-Confidence Findings
- (conf: 4/10) file:line — description (Pass N)

### Overall Score: X/10
  - Correctness+Security: X/10 (Pass 1)
  - Performance+Efficiency: X/10 (Pass 2)
  - Maintainability+Standards: X/10 (Pass 3)
  - Coding Standards Compliance: X/10 (Pass 3, per coding-standards.md)
```

## Fix-First Handling (aligned with 1A) · Fix-First 处理

- `AUTO` findings → apply the fix automatically, output `[AUTO-FIXED]` · 自动应用修复
- `ASK` findings → batch into a decision list for the user · 汇总为决策列表，交用户裁定

Confidence gating · 置信度门控：
- ≥7 → main report · 主报告
- 5-6 → main report with "Medium confidence, verify" · 主报告，附核实提示
- 3-4 → appendix · 附录
- 1-2 → suppress · 抑制
