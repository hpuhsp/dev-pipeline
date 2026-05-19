# Code Review Checklist

语言无关的代码审查清单。审查时逐项检查，不只关注"代码能跑"。

## 1. 正确性 (Correctness)

### 必须检查
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

### 常见错误模式

```
❌ JS:   const data = JSON.parse(response.body); // body 可能是 null
✅ JS:   const data = JSON.parse(response.body ?? '{}');

❌ Python: value = config['timeout']  # KeyError
✅ Python: value = config.get('timeout', 30)

❌ Java: String name = user.getName().toUpperCase(); // NPE
✅ Java: String name = Optional.ofNullable(user).map(User::getName).map(String::toUpperCase).orElse("");
```

## 2. 安全性 (Security)

### 必须检查
- **注入风险**：用户输入是否拼接到 SQL / Shell / HTML？
  - 检查是否使用了参数化查询而不是字符串拼接
  - 检查模板引擎是否启用了自动转义
- **敏感信息**：是否有硬编码的密钥、Token、密码、连接字符串？
  - 搜索关键词：`password`、`secret`、`token`、`api_key`、`private_key`、`BEGIN RSA`
- **权限控制**：新增接口是否有适当的权限检查？是否可越权访问？
- **输入验证**：外部输入是否做了校验？（长度、格式、范围）
- **依赖安全**：新增的第三方依赖是否有已知漏洞？

## 3. 性能 (Performance)

### 关注信号
- **N+1 查询**：循环内是否调用了数据库查询或远程 API？
- **不必要的循环**：是否可以在一次遍历中完成？是否可以用内置方法替代手动循环？
- **大对象拷贝**：是否无意中深拷贝了大对象 / 大数组？
- **内存泄漏**：
  - JS/TS: 未清理的 event listener、setInterval、闭包引用
  - Python: 循环引用、未关闭的文件句柄
  - Java: 未关闭的 Stream/Connection
- **资源加载**：是否加载了不需要的数据？（SELECT * 但只用 2 列）

## 4. 可维护性 (Maintainability)

### 命名
- 变量/函数名是否表达意图？（避免 `data`、`tmp`、`result`、`item`）
- 布尔值是否以 `is`/`has`/`should`/`can` 开头？
- 函数名是否以动词开头？

### 函数设计
- 单个函数是否超过 30 行？（如果是，考虑拆分）
- 函数是否在做多件事？（函数名中的 "and" 是坏信号）
- 参数是否超过 4 个？（考虑用对象/配置参数）

### 代码重复
- 是否有复制粘贴的代码块？（3 行以上相同逻辑应提取）
- 是否有可以复用的已有工具函数？

## 5. 一致性 (Consistency)

- 是否使用了与项目一致的错误处理模式？
- 是否使用了与项目一致的日志方式？
- 文件/目录命名是否与项目约定一致？
- import 顺序是否与项目一致？

## 6. 特定语言检查

### JavaScript/TypeScript
- 是否使用 `===` 而不是 `==`？
- TypeScript: 是否避免了 `as any` 类型断言？
- React: 是否在 useEffect 中正确清理副作用？
- React: key prop 是否使用了稳定唯一值（避免 index）？

### Python
- 是否使用了类型注解（如果项目要求）？
- 可变默认参数：`def f(items=[])` → `def f(items=None)`
- 文件操作是否使用了 `with` 语句？

### Java/Kotlin
- Java: `equals()` 是否处理了 null？
- Kotlin: 是否合理使用 `?.` 而不是过度的 `!!`？
- 资源是否使用 try-with-resources？
