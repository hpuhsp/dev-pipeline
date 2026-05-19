# 权威编码规范速查

各语言/平台的权威编码规范参考。审查时根据项目技术栈自动匹配对应的规范进行检查。

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
- 包名全小写，点分隔，禁止下划线

**代码结构**
- 单个方法不超过 80 行
- `if`/`for`/`while` 必须使用大括号（即使只有一行）
- 不允许 `switch` case 穿透（必须 break 或注释 `// fall through`）
- 不能使用已废弃的类或方法
- `equals()` 调用时将常量/确定值放前面：`"test".equals(str)` 防 NPE

**集合与并发**
- `ArrayList` 初始化指定容量：`new ArrayList<>(expectedSize)`
- 不要在 `foreach` 中 `remove`（应使用 `Iterator`）
- 线程安全的类优先使用 `java.util.concurrent` 下的
- `SimpleDateFormat` 是线程不安全的，使用 `DateTimeFormatter` 替代
- 使用 `ThreadPoolExecutor` 而非 `Executors` 创建线程池

**面向对象**
- 重写 `equals()` 必须重写 `hashCode()`
- 禁止在构造方法中加入业务逻辑（应放 `init()` 中）
- 类成员变量不应声明为 `protected`（除非确实需要子类访问）
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
- `switch` 模式匹配（Java 17+）：支持类型匹配 + 守卫条件
  ```java
  switch (obj) {
      case Integer i && i > 0 -> "positive integer";
      case Integer i            -> "non-positive integer";
      case String s             -> s.toUpperCase();
      default                   -> "unknown";
  }
  ```

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
- 冒号前加空格（类型声明）：`fun foo(bar: String)`
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

### detekt（Kotlin 静态分析）

- `EmptyFunctionBlock` — 空函数体需注释说明
- `TooManyFunctions` — 单文件方法数不超过阈值
- `LongParameterList` — 参数超过阈值时使用数据类包装
- `MagicNumber` — 数字字面量应命名
- `SpreadOperator` — 避免 `*` 展开操作符（性能）

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
- 分号：必须
- 字符串：单引号 `'`
- 结尾逗号：`{ a: 1, b: 2, }`

**最佳实践**
- 使用 `===` 而非 `==`
- 使用字面量创建对象和数组：`{}`、`[]`
- 链式调用超过 2 个方法时换行
- 禁止未使用的变量（`no-unused-vars`）
- 禁止在循环中定义函数
- `import` 放在文件顶部

### Google TypeScript Style Guide（TS 补充）

- 接口名不加 `I` 前缀
- 类型断言使用 `as Type`（不用 `<Type>`）
- 优先 interface 而非 type（除非需要联合类型）
- 函数返回值必须声明类型
- 禁止 `any`（除非有明确注释说明原因）
- `@ts-ignore` 必须有注释说明
- 使用 `const enum` 或 string union 替代魔法字符串
- 善用 `readonly` 和 `as const`

### React 规范

- 组件名：PascalCase；组件文件使用同名
- Hook 以 `use` 开头
- 事件处理函数以 `handle` 开头：`handleClick`
- 传递事件处理 props 以 `on` 开头：`onClick`
- 不要在 `useEffect` 中遗漏依赖项
- 用 `key` prop 时使用稳定唯一值（不用 index）
- 避免不必要的 state（能从 props/其他 state 计算出的就用 `useMemo`）

### Vue 3 规范（Vue Style Guide 官方）

**Priority A — 必须遵守（防错）**
- 组件名必须为多词（避免与 HTML 元素冲突，根 `App` 除外）：`TodoItem` 而非 `Item`
- Props 必须使用详细定义（type, required, default, validator），禁用 `props: ['status']`
- `v-for` 必须搭配 `:key`，且 key 使用稳定唯一值（不用 index）
- `v-if` 和 `v-for` 禁止在同一元素上 — `v-for` 优先级更高会导致性能灾难；应使用 computed 先过滤
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
- `defineProps` 使用泛型或运行时声明（不用纯类型推断丢失校验信息）
- `defineEmits` 必须声明事件签名：`const emit = defineEmits<{ update: [value: string] }>()`
- `defineExpose` 只暴露必要项，避免过度暴露内部状态
- `watch`/`watchEffect` 在不再需要时 `onUnmounted` 中停止（手动创建的 watcher）
- `ref` vs `reactive`：基本类型用 `ref`，对象优先 `reactive`（或用 `ref` + `reactive` 包装）

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
- import 分行，标准库 → 第三方 → 本地
- 顶层函数/类之间空 2 行；方法之间空 1 行

**规则**
- 比较用 `is`/`is not`（None 比较）而非 `==`
- 不要与 `True`/`False` 比较：`if x:` 而非 `if x == True:`
- 函数调用时等号两边不加空格：`func(a=1)`
- 逗号后面加空格：`[1, 2, 3]`
- 可变默认参数的陷阱：`def f(items=[])` → `def f(items=None)`

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

---

## Web 前端通用

### W3C / WCAG 2.1 AA（可访问性）

- 所有图片必须有 `alt` 属性
- 表单控件必须有关联 `label`
- 颜色对比度 ≥ 4.5:1（正文）/ 3:1（大号文本）
- 不使用仅颜色区分信息
- 键盘可导航（Tab、Enter、Esc）
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
