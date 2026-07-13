# 权威编码规范速查

各语言/平台的权威编码规范参考。审查时根据项目技术栈自动匹配对应的规范进行检查。

> **Token-efficient loading**: This file covers 7 languages (~22KB). When loading, **read only the section matching the detected tech stack** from Phase 0. For example, for a TypeScript React project, read only "JavaScript / TypeScript" + "React" + "Web 前端通用". Skip Java, Kotlin, Python, and UTS sections.

---

## Java

### 阿里 P3C 开发手册（Alibaba Java Coding Guidelines）

最权威的中文 Java 规范。核心规则：

**命名规范**
- 类名：UpperCamelCase（`UserService`, `OrderDTO`）
- 方法/变量：lowerCamelCase（`getUserById`, `orderList`）
- 常量：CONSTANT_CASE（`MAX_RETRY_COUNT`）
- 抽象类以 `Abstract`/`Base` 开头；异常类以 `Exception` 结尾；测试类以 `Test` 结尾
- POJO 中布尔变量不加 `is` 前缀（会导致序列化框架问题）
- POJO 命名后缀约定：`DTO`（数据传输）、`VO`（视图）、`BO`（业务对象）、`Query`/`Criteria`（查询参数）、`DO`（数据对象）
- 包名全小写，点分隔，禁止下划线

**代码结构**
- `@Override` 注解强制：**所有覆写方法必须加 `@Override` 注解**（P3C 强制）
- 单个方法不超过 80 行
- `if`/`for`/`while` 必须使用大括号（即使只有一行）
- `switch` 必须包含 `default` 分支（即使不做任何操作）
- 不允许 `switch` case 穿透（必须 break 或注释 `// fall through`）
- 不能使用已废弃的类或方法
- `equals()` 调用时将常量/确定值放前面：`"test".equals(str)` 防 NPE

**集合与并发**
- `ArrayList` 初始化指定容量：`new ArrayList<>(expectedSize)`
- 不要在 `foreach` 中 `remove`（应使用 `Iterator`）
- 方法返回空集合/空数组而非 `null`（避免调用方 NPE）
- 线程安全的类优先使用 `java.util.concurrent` 下的
- 使用 `ThreadPoolExecutor` 而非 `Executors` 创建线程池

**日期与字符串处理**
- **必须使用 `java.time` API**（`LocalDate`, `LocalDateTime`, `Instant` 等），禁止使用 `java.util.Date`、`java.sql.Date`、`SimpleDateFormat`（线程不安全且已过时）
- `SimpleDateFormat` 是线程不安全的，使用 `DateTimeFormatter` 替代
- 循环内字符串拼接必须使用 `StringBuilder` 的 `append()` 方法

**面向对象**
- 重写 `equals()` 必须重写 `hashCode()`
- 禁止在构造方法中加入业务逻辑（应放 `init()` 中）
- 非 static 成员变量与子类共享时必须声明为 `protected`（P3C 强制）；仅本类使用则用 `private`
- 接口的方法签名不要加 `public` 修饰符

**MySQL**
- 表名/字段名必须小写，下划线分隔
- 索引名：`idx_字段名`（普通）、`uk_字段名`（唯一）
- `varchar` 长度不超过 5000（超过用 `text`，单独建表）
- 禁止使用 `SELECT *`
- 超过 3 张表禁止 join（应在应用层组合）
- 禁止使用存储过程、触发器、视图、外键

**异常与日志**
- 不能 `catch` 后什么都不做（至少打日志）
- 异常不用于流程控制
- 日志输出使用占位符：`log.info("user:{}", userId)` 而非字符串拼接
- 生产环境禁止 `System.out`

**工程规范**
- 线上禁用 `System.exit()` 和 `Runtime.halt()`
- 魔法值（-1, 0, 1, 99...）必须定义为常量
- Object 的 `clone()` 默认是浅拷贝，重写需实现 `Cloneable`

### Google Java Style Guide（补充规则）

- 缩进：2 空格（阿里用 4 空格，以项目配置为准）
- 列宽：100 字符
- import 不使用通配符 `import java.util.*`
- 重载方法应放在一起

### Java 17+ 现代特性（不可变性与类型安全）

**Records（不可变数据载体）**
- 数据载体类优先使用 `record` 替代 `class` + Lombok `@Data`
  ```java
  // ✅ record — 自动生成 equals/hashCode/toString/accessor
  public record UserDTO(Long id, String name, String email) {}

  // ❌ 传统 POJO — 或使用 Lombok @Data
  ```
- Record 所有字段自动 `final`，不可变，线程安全
- Record 可以有 compact constructor 做参数校验：
  ```java
  public record PositiveAmount(BigDecimal value) {
      public PositiveAmount {
          if (value.compareTo(BigDecimal.ZERO) <= 0)
              throw new IllegalArgumentException("must be positive");
      }
  }
  ```

**Sealed Classes（封闭类型层级）**
- 固定的类型层级使用 `sealed class` 替代开放继承：
  ```java
  // ✅ 编译器强制执行穷尽检查
  public sealed interface PaymentResult
      permits PaymentSuccess, PaymentFailed, PaymentPending {}

  // switch 穷尽检查 — 遗漏类型编译报错
  String message = switch (result) {
      case PaymentSuccess s -> "OK: " + s.transactionId();
      case PaymentFailed f  -> "FAIL: " + f.reason();
      case PaymentPending p -> "PENDING...";
  };
  ```

**Pattern Matching（模式匹配）**
- `instanceof` 模式匹配（Java 16+）：`if (obj instanceof String s)` 省去手动强制转换
- `switch` 模式匹配（**Java 21 正式发布**，Java 17-20 需 `--enable-preview`）：
  ```java
  switch (obj) {
      case Integer i when i > 0 -> "positive integer";  // Java 21 final syntax
      case Integer i            -> "non-positive integer";
      case String s             -> s.toUpperCase();
      default                   -> "unknown";
  }
  ```
  注意：Java 17-20 预览版使用 `&&` 替代 `when`

**Switch 表达式（Java 14+）**
- 使用 `->` 箭头语法，省略 `break`
- 编译器强制穷尽检查

### Optional 最佳实践

- 链式调用优先使用 `map`/`flatMap`，避免 `isPresent()` + `get()`：
  ```java
  // ✅ 链式转换
  return userRepo.findByEmail(email)
      .map(User::getDepartment)
      .map(Department::getName)
      .orElse("Unknown");

  // ❌ 命令式判空
  Optional<User> opt = userRepo.findByEmail(email);
  if (opt.isPresent()) { return opt.get().getName(); }
  ```
- 禁止 `Optional` 作为字段类型或方法参数 — 仅用于返回值
- 集合空值用空集合而非 `Optional<List<T>>`

### Streams 最佳实践

- 避免在 Stream 中产生副作用（mutate 外部状态）
- 优先使用内置 collect 而非手动 accumulate：
  ```java
  // ✅ Collectors
  Map<Long, User> byId = users.stream()
      .collect(Collectors.toMap(User::getId, Function.identity()));

  // ❌ forEach 手动加
  Map<Long, User> byId = new HashMap<>();
  users.stream().forEach(u -> byId.put(u.getId(), u));
  ```
- 复杂管道超过 5 步拆分为独立中间变量
- `parallel()` 只在数据量 >10000 且无 I/O 的纯计算场景使用（线程池开销）

### 不可变性 (Immutability)

- 字段优先 `final` — 能 final 就 final
- 集合字段使用 `Collections.unmodifiableList()` 或 `List.copyOf()` 防御性拷贝
- Builder 模式用于复杂对象构造（或 Lombok `@Builder`）
- 禁止暴露可变内部状态（getter 返回防御性拷贝）

### Null 安全注解

- 使用 `@Nullable` / `@NonNull` 注解（JSR-305 或 `org.checkerframework`）标注方法签名
- Spring Boot 项目使用 `@NonNullApi` 包级注解，默认所有参数/返回值非空
- 配合 IDE 和 NullAway / SpotBugs 做静态空值分析

### 领域特定异常

- 禁止使用泛化异常：`throw new RuntimeException("error")`
- 使用业务语义的异常类：
  ```java
  // ✅ 业务语义
  throw new UserNotFoundException(email);
  throw new InsufficientBalanceException(accountId, required, available);

  // ❌ 无意义泛化
  throw new RuntimeException("something went wrong");
  ```
- 异常类名以 `Exception` 结尾，放在与使用类同包或独立 `exception` 包下

### 测试标准

- **JUnit 5**（`org.junit.jupiter`）：用 `@Test`、`@BeforeEach`、`@ParameterizedTest`
- **AssertJ**：流畅断言 `assertThat(result).isEqualTo(expected)`
- **Mockito**：`@Mock` + `@InjectMocks`，`when().thenReturn()` 链式桩
- 测试类命名：`<被测类名>Test`；测试方法使用 `@DisplayName` 中文描述

---

### 框架特定规则

**Spring Boot 项目**
- Controller 使用 `@RestController` + `@RequestMapping`
- Service 使用 `@Service` + `@Transactional(readOnly = true)` 默认
- 依赖注入优先构造器注入（`@RequiredArgsConstructor`），避免字段 `@Autowired`
- 配置使用 `@ConfigurationProperties` + record（Spring Boot 2.2+）
- 异常处理使用 `@ControllerAdvice` / `@RestControllerAdvice` 全局处理

**Quarkus 项目**
- 使用 CDI 作用域：`@ApplicationScoped`（默认）、`@RequestScoped`
- Panache 实体：`@Entity` extends `PanacheEntity`
- 响应式管道：`@Channel` + Multi/Uni

---

## Kotlin / Android

### Android Kotlin Style Guide（官方）

**命名**
- 类/接口：UpperCamelCase
- 函数/属性：lowerCamelCase
- 常量：CONSTANT_CASE（`const val` 或 `@JvmField` 顶层变量）
- 测试类：`<被测试类>Test`

**格式**
- 缩进：4 空格
- 列宽：100 字符
- 冒号规则：类型声明/返回类型冒号前不加空格（`bar: String`, `fun foo(): Int`）；类继承冒号前加空格（`class Foo : Bar`）
- lambda 中变量名尽量简短或使用 `it`

**惯用法**
- 优先使用 `val` 而非 `var`
- 优先使用不可变集合
- 利用 `?.let {}`、`?:` 进行空安全操作
- 避免 `!!` 非空断言（除非确实不可能为 null）
- 使用 `when` 替代长 `if-else if` 链
- 优先数据类 (`data class`) 用于纯数据持有
- 扩展函数优先于工具类静态方法

### Android 特定规则

- Activity/Fragment 不使用带参构造（系统通过反射创建）
- UI 操作必须在主线程；耗时操作必须在后台线程
- 使用 `ConstraintLayout` 减少布局嵌套
- 资源文件命名：`activity_`、`fragment_`、`item_`、`dialog_` 前缀
- 使用 `@StringRes`、`@ColorRes` 等资源注解

### Jetpack Compose（现代 Android UI）

- `@Composable` 函数：PascalCase 命名，不返回任何值（返回 Unit）
- 状态提升（State Hoisting）：状态向上提升到调用方，`@Composable` 函数接收 `value: T` + `onValueChange: (T) -> Unit` 而非内部持有 `var`
- `remember`：缓存跨重组的数据；`rememberSaveable` 用于进程死亡后恢复
- 副作用管理：
  - `LaunchedEffect(key)`：key 变化时重启协程，自动在离开组合时取消
  - `DisposableEffect(key)`：需要手动清理资源时（如注册/注销监听器）
  - `rememberCoroutineScope()`：需要用户交互触发协程时（如点击事件）
  - 禁止在 `@Composable` 函数中直接启动协程（使用上述 API）
- Modifier 顺序敏感：先声明的在外层，影响布局和事件传播
- 禁止在 Compose 中使用 `GlobalScope`（使用 Compose 感知的协程作用域）

### Kotlin 协程（Coroutines）

- 禁止使用 `GlobalScope`：使用 `viewModelScope`（Android ViewModel）、`lifecycleScope`（Lifecycle 拥有者）、或自行创建的 `CoroutineScope` + `SupervisorJob()`
- 结构化并发：父协程取消时子协程自动取消
- Dispatchers 选择：
  - `Dispatchers.Main` — UI 操作、LiveData/StateFlow 更新
  - `Dispatchers.IO` — 网络请求、数据库操作、文件 I/O
  - `Dispatchers.Default` — CPU 密集型计算
- 用 `supervisorScope` 隔离子协程失败（一个子协程失败不取消兄弟）
- 异常处理：顶层协程用 `CoroutineExceptionHandler`，内部用 `try/catch`

### Kotlin Flow 与响应式模式

- `StateFlow` / `SharedFlow`：热流用于状态和事件分发
- 生命周期感知收集：UI 层使用 `repeatOnLifecycle(Lifecycle.State.STARTED) { flow.collect { ... } }` 或 `flowWithLifecycle(lifecycle, Lifecycle.State.STARTED)`
- 禁止在 `lifecycleScope.launch { flow.collect {} }` 中直接收集（无生命周期感知，后台泄漏）
- `stateIn(scope, SharingStarted.WhileSubscribed(5000), initialValue)` 将冷流转换为热 StateFlow
- `shareIn` 用于多观察者共享冷流
- `collectLatest`：新值到达时自动取消上一个收集（用于搜索、自动保存等场景）
- `catch {}` 操作符捕获上游异常；不要吞没异常（至少打日志）

### Kotlin 密封类型（Sealed Classes）

- 受限类型层级优先使用 `sealed class` / `sealed interface`：
  ```kotlin
  // ✅ 编译器强制穷尽 when 检查
  sealed interface UiState {
      data object Loading : UiState
      data class Success(val data: List<Item>) : UiState
      data class Error(val message: String) : UiState
  }
  ```
- `when` 穷尽检查 — 遗漏分支编译报错
- `sealed interface`（Kotlin 1.5+）允许跨包扩展，比 `sealed class` 更灵活
- 枚举 (`enum class`) 用于编译期已知的固定值集；sealed class 用于动态数据的受限状态

### Kotlin 测试

- **JUnit 5** + **MockK**（Kotlin 首选 mock 框架）：
  ```kotlin
  class UserServiceTest {
      private val repository = mockk<UserRepository>()
      private val userService = UserService(repository)

      @Test
      fun `should create user with valid input`() {
          every { repository.findByEmail(any()) } returns null
          coEvery { repository.saveAsync(any()) } returns mockk()
          // ...
      }
  }
  ```
- `mockk` vs `mockito`：Kotlin 项目优先 MockK（支持 `coEvery` 协程 mock、`every` DSL、`relaxed` mock）
- **Compose 测试**：`ComposeTestRule`（`createComposeRule()`）+ `onNodeWithText/onNodeWithTag` 查找 + `performClick/performTextInput` 交互 + `assertIsDisplayed/assertTextEquals` 断言
- 使用 `@RunWith(AndroidJUnit4::class)` 进行 Android 仪器化测试
- 测试文件：`src/test/kotlin/` 或 `src/androidTest/kotlin/`（Android 仪器化）

### detekt（Kotlin 静态分析）

- `EmptyFunctionBlock` — 空函数体需注释说明
- `TooManyFunctions` — 单文件方法数不超过阈值
- `LongParameterList` — 参数超过阈值时使用数据类包装
- `MagicNumber` — 数字字面量应命名
- `SpreadOperator` — 避免 `*` 展开操作符（性能）

---

## Swift / iOS

### Swift API Design Guidelines（Apple 官方）

**命名**
- 类型/协议：PascalCase（`UserService`, `Decodable`）
- 变量/函数/属性：camelCase（`userName`, `fetchData()`）
- 布尔属性：`is`/`has`/`should` 前缀（`isEnabled`, `hasPermission`）
- 协议名描述能力而非类型（`Decodable` 而非 `DecodableType`）

**API 设计原则**
- 优先清晰而非简洁（`model.insert(5, at: 2)` 而非 `model.insert(5, 2)`）
- 使用参数标签区分用途
- 可变方法用动词原形，不可变用过去分词（`sort()` vs `sorted()`）
- 失败的初始化器用 `init?` 而非 `init` + 返回 Optional

### Swift 编码规范

**格式**
- 缩进：4 空格
- 行宽建议 ≤ 120 字符
- 逗号后加空格，逗号前不加
- 冒号：字典字面量键后加空格，类型声明前加空格
- `guard` 语句提早返回，减少嵌套

**Optionals**
- 优先可选绑定（`if let`/`guard let`）而非强制解包（`!`）
- 避免隐式解包可选（`!`），仅限 IBOutlet
- 链式可选调用优先于嵌套 `if let`

**错误处理**
- 使用 `throws` + `Error` 协议而非返回 Optional
- `Result` 类型用于异步回调场景
- `do-catch` 捕获具体错误类型，避免空 catch

**并发**
- 优先 `async/await` 而非 CompletionHandler
- 使用 `actor` 保护共享可变状态
- `Task` 用于启动异步任务，`TaskGroup` 用于并行
- 避免 `DispatchQueue` 当 `async/await` 可用时

### SwiftUI 规范

- View 结构体使用 `private` 内部子 View
- `@State` 用于本地 UI 状态，`@Binding` 用于父传子
- `@StateObject` 持有 View 的模型，`@ObservedObject` 用于外部传入
- `@EnvironmentObject` 用于全局依赖注入
- 避免在 View 中直接做业务逻辑，抽取到 ViewModel

### 内存管理

- 闭包中引用 `self` 时注意循环引用，使用 `[weak self]`
- `weak` 用于避免循环引用，`unowned` 用于生命周期相同的引用
- 在 `deinit` 中清理资源

### 测试

- XCTest（内置）：`XCTestCase` + `setUp`/`tearDown`
- Quick/Nimble（BDD 风格）：`describe`/`context`/`it`
- 测试文件：`*Tests.swift`，与源文件同结构放于 test target

---

## JavaScript / TypeScript

### Airbnb JavaScript Style Guide（业界标准）

**命名**
- 变量/函数：camelCase
- 类/构造函数：PascalCase
- 常量：UPPER_SNAKE_CASE（仅模块级 export 常量）
- 文件名：camelCase 或 kebab-case（与默认导出同名）

**格式**
- 缩进：2 空格
- 行宽：100 字符
- 分号：必须
- 字符串：单引号 `'`
- 结尾逗号：`{ a: 1, b: 2, }`

**最佳实践**
- 使用 `const` 默认声明变量，需要重新赋值时用 `let`，**禁止 `var`**
- 使用 `===` 而非 `==`
- 使用字面量创建对象和数组：`{}`、`[]`
- 优先使用对象解构获取属性：`const { name, age } = user`（Airbnb）
- 链式调用超过 2 个方法时换行
- 禁止未使用的变量（`no-unused-vars`）
- 禁止在循环中定义函数
- `import` 放在文件顶部

### Google TypeScript Style Guide（TS 补充）

- 接口名不加 `I` 前缀
- 类型断言使用 `as Type`（不用 `<Type>`）
- 优先 interface 而非 type（除非需要联合类型）
- 建议函数返回值声明类型（复杂类型时必须，简单类型由作者判断 — Google TS Style 不强制所有函数）
- **禁止使用 `any`**（Google TS Style: "Do not use the `any` type"；优先 `unknown` 或具体类型；除非有明确的临时原因并附 // FIXME 注释说明）
- **禁止使用 `@ts-ignore`**（Google TS Style 完全禁止，包括 `@ts-expect-error` 和 `@ts-nocheck`；仅单元测试中可例外使用 `@ts-expect-error`）
- 推荐启用 `strict: true`（包括 `strictNullChecks`），这是 TypeScript 代码质量的基础
- 使用 `const enum` 或 string union 替代魔法字符串
- 善用 `readonly` 和 `as const`

### JS/TS 测试

- **Jest** / **Vitest** 为首选测试框架（Vitest 性能更优，与 Vite 原生集成）
- 命名：`describe('<component/function>', () => { it('should <behavior> when <condition>', () => {...}) })`
- AAA 结构：Arrange（准备）→ Act（执行）→ Assert（验证）
- Mock：仅 mock 外部依赖（API、DB、文件系统），不 mock 被测模块内部函数
- React：`@testing-library/react` — `render()` + `screen.getByRole/getByText/getByTestId` + `fireEvent` 或 `userEvent` + `waitFor` 等异步断言
- Vue 3：`@vue/test-utils` — `mount(Component, { props, slots })` + `wrapper.find/wrapper.findAll` + `wrapper.trigger`
- 快照测试：谨慎使用；仅用于稳定的纯展示组件，不用于频繁变化的大组件
- 覆盖率：关注关键路径（>70% 分支覆盖），不强制 100%

### React 规范

- 组件名：PascalCase；组件文件使用同名
- Hook 以 `use` 开头；自定义 Hook 必须遵循 `rules-of-hooks`：不在条件/循环/return 之后调用 Hook（必须始终在组件/Hook 顶层以相同顺序调用）
- 事件处理函数以 `handle` 开头（社区广泛采用的惯例）：`handleClick`
- 传递事件处理 props 以 `on` 开头（React 官方）：`onClick`
- `useEffect` 依赖项必须完整声明（`eslint-plugin-react-hooks/exhaustive-deps`）
- `useMemo` 用于昂贵的计算缓存；`useCallback` 用于传递给子组件的函数引用稳定性 — 不要无脑包裹所有函数（过度 memoization）
- 用 `key` prop 时使用稳定唯一值（不用 index）
- 避免不必要的 state（能从 props/其他 state 计算出的就用 `useMemo` 或直接计算）
- Error Boundary：在组件树的适当层级放置 `<ErrorBoundary>`，优雅降级而非白屏
- 严格模式开发：使用 `<StrictMode>` 检测副作用问题和过时 API
- Next.js：优先 Server Components，仅在需要交互/浏览器 API 时添加 `'use client'`；服务端数据获取用 `async` Server Component 或 `fetch` + `cache()`

### Vue 3 规范（Vue Style Guide 官方）

**Priority A — 必须遵守（防错）**
- 组件名必须为多词（避免与 HTML 元素冲突，根 `App` 除外）：`TodoItem` 而非 `Item`
- Props 必须使用详细定义（type, required, default, validator），禁用 `props: ['status']`
- `v-for` 必须搭配 `:key`，且 key 使用稳定唯一值（不用 index）
- `v-if` 和 `v-for` 禁止在同一元素上 — 在 Vue 3 中 `v-if` 优先级高于 `v-for`，导致 `v-if` 无法访问 `v-for` 的循环变量（在 Vue 2 中 `v-for` 优先级更高造成性能问题）；应使用 computed 先过滤
- 组件 `data()` 必须是函数（防止多实例共享状态）

**Priority B — 强烈推荐（提高可读性）**
- SFC 文件命名：PascalCase 或 kebab-case，全项目统一
- 基础 UI 组件使用统一前缀：`Base`、`App` 或 `V`（如 `BaseButton.vue`）
- 紧密耦合的子组件以父组件名为前缀：`TodoList.vue` → `TodoListItem.vue`
- Computed 属性保持简单，单一职责，不含副作用 — 拆分为多个专注的 computed
- SFC 顶层顺序：`<template>` → `<script>` → `<style>`
- 组件选项顺序：name → components → props → emits → setup/data → computed → watch → methods

**Priority C — 推荐（统一风格）**
- 模板中组件名使用 PascalCase（区分原生 HTML）：`<MyComponent />`
- Props 名：JS 中 camelCase，模板中 kebab-case：`:greeting-text="hi"`
- 无插槽内容的组件使用自闭合：`<MyComponent />`
- 模板中禁止复杂表达式 — 应提取为 computed/methods
- 属性值始终加引号（单引或双引，全项目统一）

**Composition API 额外规则（`<script setup>`）**
- `<script setup>` 是 Vue 3 官方推荐的默认写法，所有新组件应优先使用
- `defineProps`：TypeScript 项目推荐泛型声明 `defineProps<{...}>()`（配合 `withDefaults` 设置默认值）；非 TypeScript 项目使用运行时声明
- `defineEmits` 必须声明事件签名：`const emit = defineEmits<{ update: [value: string] }>()`
- `defineModel`（Vue 3.4+）：`const modelValue = defineModel<string>()` 替代传统 v-model props+emit 双定义
- `defineExpose` 只暴露必要项，避免过度暴露内部状态
- `watch`/`watchEffect` 在不再需要时 `onUnmounted` 中停止（手动创建的 watcher）
- 响应式 API：**推荐统一使用 `ref`**（`ref` 支持所有类型且无解构陷阱；`reactive` 有限制：不可重新赋值、解构丢失响应性）

**禁止模式**
- 禁止在 `computed` 中执行副作用（API 调用、DOM 操作、状态变更）
- 禁止直接修改 props（子组件修改父组件数据）
- 禁止在 `watch`/`watchEffect` 中修改被监听的数据（死循环）
- 禁止使用 `v-html` 除非内容经过净化（XSS 风险）

### uni-app 跨平台规范

**通用规则**
- 使用 uni-app 内置组件替代 HTML 标签：`<view>` 替代 `<div>`，`<text>` 替代 `<span>`，`<image>` 替代 `<img>`
- 适配使用 `rpx`（responsive pixel），750rpx = 屏幕宽度，非固定 px
- 页面生命周期使用 uni-app 标准：`onLoad`/`onShow`/`onReady`/`onHide`/`onUnload`
- CSS 避免使用 `*` 选择器（小程序不支持）
- 避免使用 `window`/`document`/`location` 等浏览器全局对象（App/小程序不存在）
- 网络请求使用 `uni.request` 而非 `fetch`/`axios`（除非明确适配层）
- 路由跳转使用 `uni.navigateTo`/`uni.redirectTo`/`uni.switchTab` 而非 vue-router

**条件编译**
- 平台差异化代码使用条件编译：
  ```
  // #ifdef APP-PLUS
  // 仅 App 平台代码
  // #endif

  // #ifdef H5
  // 仅 H5 平台代码
  // #endif

  // #ifdef MP-WEIXIN
  // 仅微信小程序
  // #endif
  ```
- 条件编译注释必须在独立行，不能混在代码行内

**小程序特定约束**
- 禁止使用 `v-html`（小程序不支持）
- 禁止在模板中使用 `filters`（小程序不支持）
- `scoped` 样式在小程序中穿透使用 `:deep()`（废弃 `/deep/`、`>>>`）
- 包大小敏感：避免引入大体积第三方库，优先使用 uni-app API 或平台原生能力

**性能优化**
- 长列表必须使用 `<scroll-view>` 或虚拟列表（如 `uni-recycle-view`）
- 图片使用 `<image>` 的 `lazy-load` 属性
- 避免过多的全局组件注册（影响所有页面的初始化）
- 页面预加载使用 `uni.preloadPage`（减少白屏时间）

### UTS (uni-app TypeScript) 规范

**语言特性与约束**
- UTS 是 DCloud 设计的 TypeScript 子集，编译为 Kotlin (Android) / Swift (iOS) / JS (Web)
- **不支持 Node.js API**：不能使用 `fs`、`path`、`http` 等 — UTS 运行在 uni-app 运行时，不是 Node 环境
- **类型系统限制**：不支持 `any` 类型（严格模式默认开启），不支持 `unknown`、`never` 等高级类型
- **不支持泛型约束**：`<T extends SomeType>` 不可用
- **不支持装饰器**（`@Component` 等）
- **不支持 `eval()`、`new Function()`** 等动态代码执行
- 没有 `DOM`、`BOM` API — 不能使用 `document`/`window`/`navigator`

**UTS 特有语法**
- 平台特定代码使用条件编译：
  ```
  // #ifdef APP-ANDROID
  // Kotlin 平台代码
  // #endif

  // #ifdef APP-IOS
  // Swift 平台代码
  // #endif
  ```
- 调用原生能力使用 `uni.requireNativePlugin('PluginName')`
- 异步编程：支持 `async/await`，但不支持顶层 `await`（必须在 `async` 函数内）
- 类型声明文件 `.d.ts` 可正常使用（用于声明原生模块类型）

**命名与组织**
- 模块文件名：kebab-case（`user-service.uts`）
- 导出函数/类：PascalCase
- 变量/函数参数：camelCase
- 常量：UPPER_SNAKE_CASE
- 每个 `.uts` 文件职责单一：一个文件只做一件事（数据获取 / 原生桥接 / 工具函数）

**安全与性能**
- 原生模块调用必须加 try/catch（原生层崩溃会导致 App 闪退）
- 避免在循环中调用原生方法（跨语言调用开销大）→ 批量处理
- 大对象传递前考虑序列化边界成本（Kotlin ↔ Swift ↔ JS 桥接有序列化损耗）
- 合理使用 `lazy` 初始化原生插件（避免启动时全部加载）

**禁止模式**
- 禁止混用 UTS 和标准 TypeScript 文件（导入路径分开，逻辑隔离）
- 禁止在 UTS 中引用 Node.js 类型（`@types/node`）
- 禁止使用 `as any` 绕过类型检查（UTS 严格模式不允许）
- 禁止直接操作平台原生对象而不封装（破坏跨平台兼容性）

---

## Python

### PEP 8 — Style Guide for Python Code

**命名**
- 模块：`lower_with_under.py`
- 类：`CapWords`（`CapWords` 缩写保持全大写：`HTTPClient`）
- 函数/方法/变量：`lower_with_under()`
- 常量：`CAPS_WITH_UNDER`
- `_protected`（单下划线前缀）；`__private`（双下划线）

**格式**
- 缩进：4 空格（禁止 tab）
- 列宽：79 字符（docstring/注释：72）
- import 分行，标准库 → 第三方 → 本地（禁止 `from module import *` 通配符导入）
- 顶层函数/类之间空 2 行；方法之间空 1 行
- 禁止尾部空格；二元运算符两侧各 1 空格；括号内不加空格
- 禁止单行复合语句（`if x: do_something()` 必须分行）
- 行续优先使用括号内隐式续行，而非反斜杠 `\`

**规则**
- 比较用 `is`/`is not`（None 比较）而非 `==`
- 不要与 `True`/`False` 比较：`if x:` 而非 `if x == True:`
- 函数调用时等号两边不加空格：`func(a=1)`
- 逗号后面加空格：`[1, 2, 3]`
- 可变默认参数的陷阱：`def f(items=[])` → `def f(items=None)`
- 注释作为完整句子：首字母大写，以句号结尾；行内注释与代码至少 2 空格

### PEP 257 — Docstring Conventions

- 所有公共模块/函数/类/方法必须有 docstring
- 使用三重双引号 `"""`
- 单行 docstring：`"""Return the pathname of foo."""`
- 多行：首行概述，空行，详细描述

### Google Python Style Guide

- 使用类型注解（Python 3.6+）
- `import` 不使用通配符
- 使用 `with` 语句管理文件和 socket
- 使用 `format()` 或 f-string 而非 `%` 格式化
- 避免全局变量
- 尽量使用生成器和列表推导
- 默认参数不使用可变对象

### 现代 Python 类型系统（Typing）

- `TypedDict`：为字典结构提供类型安全的 key/value 定义（替代裸 `dict[str, Any]`）
  ```python
  class UserDict(TypedDict):
      id: int
      name: str
      email: str | None
  ```
- `Protocol`：结构化子类型（不依赖继承，满足方法签名即可）
- `@dataclass`：数据载体类的标准选择（替代手写 `__init__`）
- `Literal["a", "b"]`：限制值的集合（类似枚举）
- `Final`：声明不可修改值；`Self`（3.11+）返回自身类型
- `T | None` 优先于 `Optional[T]`（3.10+）
- `dict[str, int]` 优先于 `Dict[str, int]`（3.9+ builtin generics）

### Python 结构化模式匹配（match/case, 3.10+）

- `match`/`case` 用于结构化数据解构（替代复杂的 `if/elif isinstance` 链）
- 模式可以解构 `dict`、`list`、dataclass、namedtuple 等
- 守卫条件用 `case pattern if condition:`

### Python asyncio

- `async`/`await` 用于 I/O 密集型操作，禁止在 `async` 函数中写 CPU 阻塞代码
- `asyncio.gather()` 并发多个协程；`asyncio.create_task()` 创建后台任务
- 禁止 `await` 忘记：未 await 的协程不会执行（最常见 asyncio bug）
- 混用 sync/async 时：从同步代码调用异步 → `asyncio.run()`（不能在 async 上下文内使用）；从异步代码调用阻塞同步 → `asyncio.to_thread()` 或 `anyio.to_thread.run_sync()`
- 不要在 async 上下文中直接调用阻塞函数（会阻塞整个事件循环）
- FastAPI：路径函数可以是 `def` 或 `async def`（中间件/依赖自动检测）

### Python Web 框架

**FastAPI**
- 路径函数：`async def` 用于 async 依赖；`def` 用于同步（线程池中运行）
- Pydantic v2：`BaseModel` + `model_validate()` + `field_validator`；禁止混用 v1 `class Config`
- 依赖注入用 `Depends()`：`def get_db() -> Generator[Session, None, None]`
- 异常：抛 `HTTPException(status_code=..., detail=...)`，不用 `return JSONResponse(...)`
- 响应模型：`response_model=` 标注过滤敏感字段
- 后台任务：`BackgroundTasks` 用于轻量任务

**Django**
- Model：字段类型精确（不用 `CharField(max_length=255)` 当 `255` 无业务理由）；`class Meta` 中 `ordering` 和 `indexes` 明确
- View：优先 CBV（`DetailView`, `ListView`）+ 注入；FBV 用于简单逻辑
- N+1：`select_related()`（外键）/ `prefetch_related()`（多对多）防止懒加载查询
- Settings：多个 `settings` 文件（`base.py`, `dev.py`, `prod.py`）；禁止在 settings 中写业务逻辑
- Signals：谨慎使用，避免隐式依赖链；首选显式 service 调用

### Python 测试（pytest）

- **pytest** 为首选测试框架（`unittest` 仅用于遗留项目）
- Fixtures：`@pytest.fixture` + `conftest.py` 共享；`yield` 模式做 teardown
- 参数化：`@pytest.mark.parametrize("input,expected", [...])` 覆盖多场景
- Mock：`unittest.mock.patch()` 用于外部依赖；`monkeypatch` fixture 用于环境变量/属性替换
- 命名：`test_<function>_<scenario>`（`test_create_user_with_valid_email`）
- 目录：`tests/` 根，与源代码结构镜像（`tests/services/test_user.py`）
- 运行：`pytest tests/`（全部）或 `pytest tests/auth/ -v`（模块范围）
- pytest 自动重写 `assert` 提供丰富的失败诊断（变量值、表达式对比），无需手动添加诊断消息；仅在断言链复杂或需额外业务上下文时添加自定义消息

---

## Web 前端通用

### W3C / WCAG 2.1 AA（可访问性）

- **语义化 HTML**：使用 `<nav>`, `<main>`, `<article>`, `<section>`, `<header>`, `<footer>`, `<aside>` 替代 `<div>`（帮助屏幕阅读器理解页面结构）
- 所有图片必须有 `alt` 属性
- 表单控件必须有关联 `label`
- 颜色对比度 ≥ 4.5:1（正文）/ 3:1（大号文本）
- 不使用仅颜色区分信息
- 键盘可导航（Tab、Enter、Esc）；Tab 顺序合理（避免 `tabindex > 0`）
- 可聚焦元素必须有可见的 `:focus-visible` 样式（不要 `outline: none` 而不提供替代）
- `aria-label` / `aria-describedby` 用于非文本控件

### CSS / 样式

- BEM 命名法：`.block__element--modifier`
- 避免 `!important`
- 不使用 ID 选择器（用于样式）
- 避免超过 3 层选择器嵌套

### Web 性能

- 图片使用 `loading="lazy"` 延迟加载
- 字体使用 `font-display: swap`
- 避免 `<link>` 阻塞渲染（CSS in `<head>`, JS async/defer）

---

## 审查时如何使用此文档

1. **阶段 0 环境感知** 中检测到的技术栈决定使用哪些规范
2. **Agent 3 (可维护性+风格)** 在审查时按语言加载对应章节
3. 规范检查结果归入审查输出：
   - 违反强制性规范 → 🔴 阻塞项
   - 违反推荐规范 → 🟡 建议项
4. 如果项目已有 `.editorconfig`、`eslint.config.*`、`.pylintrc`、`checkstyle.xml` 等配置文件，**以项目配置为准**，此文档作为补充
