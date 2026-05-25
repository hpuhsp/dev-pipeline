# Code Review Checklist (1B — In-Skill Serial Fallback)

语言无关的代码审查清单。当 Agent 工具不可用时，按此清单自行审查，输出格式对齐 1A 并行模式。

## Multi-Pass Review Approach · 多轮审查

为模拟 3-Agent 并行审查的深度，分 3 轮独立审查，每轮聚焦一个维度：

- **Pass 1**: 正确性 + 安全性（对应 Agent 1）
- **Pass 2**: 性能 + 效率（对应 Agent 2）
- **Pass 3**: 可维护性 + 编码规范（对应 Agent 3）

每轮结束后独立打分（SCORE: X/10），最后聚合。

## 统一输出格式（与 1A 对齐）

对每个发现使用：
```
[BLOCKER|WARNING] (confidence: N/10, fix: AUTO|ASK) file:line — 问题描述 → 修复建议
```

- **SEVERITY**: `BLOCKER`（必须修复）或 `WARNING`（推荐修复）
- **confidence**: 1-10，9-10=已验证；7-8=高置信；5-6=可能误报；3-4=推测（移至附录）；1-2=极低（抑制）
- **fix**: `AUTO`=可自动修复（重命名、格式化、null 检查、提取常量等机械操作）；`ASK`=需用户决策（架构变更、API 变更、性能权衡）

### AUTO vs ASK 分类指南

| 发现类型 | 分类为 | 原因 |
|---------|--------|------|
| 变量/函数命名不规范 | AUTO | 机械重命名 |
| 提取魔法值为常量 | AUTO | 机械提取 |
| 添加 null/undefined 检查 | AUTO | 机械添加 `?.`/`if not None` 等 |
| 修复 `==` 为 `===` | AUTO | 机械替换 |
| 添加 `@Override` 注解 | AUTO | 机械添加 |
| 修复格式（缩进、空格、换行） | AUTO | 运行格式化工具 |
| 删除未使用的 import/变量 | AUTO | 机械删除 |
| 修复可变默认参数 | AUTO | 机械替换模式 |
| **架构重构** | **ASK** | 需权衡设计 |
| **API 签名变更** | **ASK** | 可能破坏下游 |
| **安全策略变更** | **ASK** | 需安全评估 |
| **性能权衡** | **ASK** | 需业务上下文 |
| **新增/替换框架或库** | **ASK** | 需团队共识 |

## Pass 1: 正确性 + 安全性

### 正确性检查

- **空值处理**：外部输入、API 响应、数据库查询结果是否都做了 null/undefined 检查？
  - JS/TS: 可选链 `?.`、空值合并 `??`、类型守卫
  - Python: `is None` 检查、`dict.get()` 代替 `dict[key]`
  - Java: `Optional` 或显式 null 检查
- **边界条件**：空数组、空字符串、0、负数、极大值 是否处理？
- **异步操作**：Promise/async 是否正确 await？错误是否被捕获？
  - JS/TS: 检查是否缺少 `await`、`.catch()` 或 `try/catch`
  - Python: 检查 `async/await` 是否正确、协程是否正确调度
  - Java: 检查 `CompletableFuture` 异常处理
- **类型安全**：类型转换是否安全？是否有隐式类型转换导致的问题？
- **循环/递归**：终止条件是否正确？是否可能死循环或栈溢出？
- **逻辑错误**：Off-by-one、反条件（&& vs ||）、错运算符
- **竞争条件**：共享可变状态并发访问有无同步？JS setState after await 是否检查组件仍然 mounted？
- **资源清理**：文件句柄、连接、事件监听器是否释放？

### 安全检查

- **注入风险**：用户输入是否拼接到 SQL / Shell / HTML？
  - 检查是否使用了参数化查询而不是字符串拼接
  - 检查模板引擎是否启用了自动转义
- **敏感信息**：是否有硬编码的密钥、Token、密码、连接字符串？
  - 搜索关键词：`password`、`secret`、`token`、`api_key`、`private_key`、`BEGIN RSA`
- **权限控制**：新增接口是否有适当的权限检查？是否可越权访问？
- **输入验证**：外部输入是否做了校验？（长度、格式、范围）
- **依赖安全**：新增的第三方依赖是否有已知漏洞？
- **不安全反序列化**：`pickle.loads()`、`eval()`、不受信输入的 `JSON.parse()`？
- **路径穿越**：从用户输入构造文件路径有无消毒？

### 常见错误模式

```
❌ JS:   const data = JSON.parse(response.body); // body 可能是 null
✅ JS:   const data = JSON.parse(response.body ?? '{}');

❌ Python: value = config['timeout']  # KeyError
✅ Python: value = config.get('timeout', 30)

❌ Java: String name = user.getName().toUpperCase(); // NPE
✅ Java: String name = Optional.ofNullable(user).map(User::getName).map(String::toUpperCase).orElse("");
```

每项发现标注：[BLOCKER|WARNING] (confidence, fix) file:line
Pass 1 结束: SCORE: X/10

---

## Pass 2: 性能 + 效率

### 性能检查

- **N+1 查询**：循环内是否调用了数据库查询或远程 API？
- **不必要的工作**：循环内能提升的计算？重复文件读取/网络请求？循环内正则重编译？
- **错过并发**：独立的 I/O 顺序执行？多个可并行的 await → `Promise.all` / `asyncio.gather`？
- **热路径膨胀**：启动或每个请求路径上的同步 I/O？频繁调用的构造器中的重初始化？
- **不必要分配**：大对象/数组拷贝？`Array.map().filter().reduce()` 链 → 单次 reduce？循环内字符串拼接 → join/StringBuilder？
- **内存泄漏**：
  - JS/TS: 未清理的 event listener、setInterval、闭包引用、无限增长的 Map 缓存无淘汰
  - Python: 循环引用、未关闭的文件句柄
  - Java: 未关闭的 Stream/Connection
- **过宽操作**：读取整个文件/加载所有记录而只需过滤少量？
- **算法复杂度**：O(n²) 可优化为 O(n log n) 或 O(n)？
- **TOCTOU**：先检查存在再操作 → 应直接操作并处理错误
- **无操作更新**：状态更新无条件触发？添加变化检测守卫
- **懒加载**：重导入可改为动态/懒加载？`React.lazy()`、动态 `import()`

每项发现标注：[BLOCKER|WARNING] (confidence, fix) file:line
Pass 2 结束: SCORE: X/10

---

## Pass 3: 可维护性 + 编码规范

### 命名与函数设计

- 变量/函数名是否表达意图？（避免 `data`、`tmp`、`result`、`item`、`obj`、`val`、`handle`、`process`）
- 布尔值是否以 `is`/`has`/`should`/`can` 开头？
- 函数名是否以动词开头？
- 单个函数是否超过 30 行？（考虑拆分）
- 函数是否在做多件事？函数名中的 "and" 是坏信号
- 参数是否超过 4 个？（考虑用对象/配置参数）

### 代码质量

- 是否有复制粘贴的代码块？（3 行以上相同逻辑应提取）
- 是否有可以复用的已有工具函数？
- 是否有泄漏抽象暴露内部细节？
- 空 catch 块？`except: pass`？过于宽泛的异常捕获？
- 字符串类型代码：裸字符串应改用 enum/常量/union？
- 嵌套条件：3 层以上 if/else、三元链 → 早期返回 / guard clause / 查找表
- 无用注释：注释说 WHAT（名字已表达）→ 删除；仅保留 WHY
- 死代码：注释掉的代码块、不可达分支、未使用的 import？

### 编码规范合规

**Read `references/coding-standards.md`** 中与检测到的技术栈匹配的章节，逐一核对每条强制性规则。

- 违反强制性规范 → BLOCKER
- 违反推荐规范 → WARNING

按语言优先级：
| 语言 | 审查依据 | 关键检查项 |
|------|---------|-----------|
| Java | P3C + Google Java Style + Java 17+ | @Override, 命名, equals(), 日期 API, Optional, 异常 |
| Kotlin | Android Kotlin Style + detekt + Compose + Coroutines | val/var, !!, when, 作用域, Compose 模式 |
| JS/TS | Airbnb + Google TS Style | const/let/var, ===, any, 类型标注, 解构 |
| React | React 惯例 | 组件命名, hooks, key, useEffect deps |
| Vue 3 | Vue Style Guide A/B/C | 多词名, props, v-for :key, computed, ref |
| Python | PEP 8 + PEP 257 + Google | snake_case, is None, 可变默认值, f-strings |
| Web/CSS | WCAG 2.1 AA + BEM | alt, label, 对比度, 键盘, 语义化 HTML |

### 一致性

- 是否使用了与项目一致的错误处理模式？
- 是否使用了与项目一致的日志方式？
- 文件/目录命名是否与项目约定一致？
- import 顺序是否与项目一致？

每项发现标注：[BLOCKER|WARNING] (confidence, fix) file:line
Pass 3 结束: SCORE: X/10

---

## 聚合输出（与 1A 对齐）

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
```

## Fix-First 处理（与 1A 对齐）

- `AUTO` 标签的发现 → 自动应用修复，输出 `[AUTO-FIXED]`
- `ASK` 标签的发现 → 汇总为决策列表，交用户裁定

置信度门控：
- ≥7 → 主报告
- 5-6 → 主报告，"Medium confidence, verify"
- 3-4 → 附录
- 1-2 → 抑制
