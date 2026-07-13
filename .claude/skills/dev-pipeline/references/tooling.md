# Recommended Static Analysis Toolchain · 推荐静态分析工具链

When the review phase finds code issues and the project lacks the relevant tooling, suggest installing these industry-standard tools.
审查阶段检测到代码问题时，如项目缺失相关工具，可建议安装以下推荐的业界标准工具。

---

## JavaScript / TypeScript

| 工具 | 用途 | 安装/配置 |
|------|------|----------|
| **ESLint 9** | 代码规则检查 | `npm i -D eslint` + flat config (`eslint.config.mjs`) |
| **Prettier** | 代码格式化 | `npm i -D prettier` + `.prettierrc` |
| **TypeScript** | 类型检查 | `npm i -D typescript` + `tsconfig.json` → `tsc --noEmit` |
| **Oxlint** | 超快 Lint（替代 ESLint） | `npm i -D oxlint` — 比 ESLint 快 50-100x |
| **Biome** | Lint + Format 一体化 | `npm i -D @biomejs/biome` + `biome.json` |
| **Knip** | 死代码检测 | `npm i -D knip` → `npx knip` |

**推荐组合（2025+）**：
- **全栈/大型项目**: Biome (lint+format) + TypeScript (typecheck) + Knip (dead code)
- **React/Next.js**: ESLint 9 (`@eslint/js` + `typescript-eslint`) + Prettier
- **Vue 3**: ESLint 9 + `eslint-plugin-vue` + Prettier
- **uni-app**: ESLint 9 + `@uni-helper/eslint-config`

**在 package.json 中加入**：
```json
{
  "scripts": {
    "lint": "biome check .",
    "format": "biome check --write .",
    "typecheck": "tsc --noEmit",
    "deadcode": "knip"
  }
}
```

---

## Python

| 工具 | 用途 | 安装/配置 |
|------|------|----------|
| **Ruff** | Lint + Format（Rust 实现，极快） | `pip install ruff` + `pyproject.toml` 配置 |
| **mypy** | 静态类型检查 | `pip install mypy` + `pyproject.toml` `[tool.mypy]` |
| **pytest** | 测试框架 | `pip install pytest` + `pytest.ini` 或 `pyproject.toml` |
| **coverage** | 测试覆盖率 | `pip install coverage` → `coverage run -m pytest` |
| **Bandit** | 安全漏洞扫描 | `pip install bandit` → `bandit -r src/` |
| **deptry** | 依赖检测（未使用/缺失） | `pip install deptry` → `deptry .` |
| ~~**pylint**~~ | ~~传统 linter~~ | 已被 Ruff 替代，除非项目已有配置 |
| ~~**flake8**~~ | ~~传统 linter~~ | 已被 Ruff 替代 |

**推荐组合（2025+）**：Ruff (lint+format) + mypy + pytest + Bandit

**在 pyproject.toml 中加入**：
```toml
[tool.ruff]
lint.select = ["E", "F", "I", "N", "W", "UP", "B", "SIM"]

[tool.mypy]
strict = true
```

---

## Java

| 工具 | 用途 | 安装/配置 |
|------|------|----------|
| **Checkstyle** | 代码风格检查（Google / Sun 规范） | Maven/Gradle 插件 + `checkstyle.xml` |
| **SpotBugs** | 字节码级别 Bug 检测 | Maven/Gradle 插件 |
| **PMD** | 代码质量 + CPD（重复代码检测） | Maven/Gradle 插件 + 规则集 |
| **Error Prone** | Google 的编译时 Bug 检测 | Maven/Gradle 编译插件 |
| **NullAway** | 空指针静态分析 | 配合 Error Prone 使用 |
| **SonarLint** | IDE 集成（SonarQube 规则） | IntelliJ IDEA 插件 |

**推荐组合**：
- **Maven**: `maven-checkstyle-plugin` + `spotbugs-maven-plugin` + `maven-pmd-plugin`
- **Gradle**: `checkstyle` + `com.github.spotbugs` + `pmd`
- **通用**: SonarLint（IDE 内实时提示）

**Maven pom.xml 参考**：
```xml
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-checkstyle-plugin</artifactId>
    <version>3.4.0</version>
    <configuration>
        <configLocation>google_checks.xml</configLocation>
    </configuration>
</plugin>
```

---

## Kotlin / Android

| 工具 | 用途 | 安装/配置 |
|------|------|----------|
| **detekt** | Kotlin 静态分析 | Gradle 插件 + `detekt.yml` |
| **ktlint** | Kotlin 代码格式化 | Gradle 插件 或 CLI |
| **Android Lint** | Android 特定检查 | Android Gradle Plugin 内置 |
| **LeakCanary** | 内存泄漏检测 | `debugImplementation` |

**推荐组合**：detekt (lint) + ktlint (format) + Android Lint（Android 项目）

---

## Swift / iOS

| 工具 | 用途 | 安装/配置 |
|------|------|----------|
| **SwiftLint** | Swift 代码规则检查 | `brew install swiftlint` + `.swiftlint.yml` |
| **SwiftFormat** | Swift 代码格式化 | `brew install swiftformat` |
| **Periphery** | 死代码检测 | `brew install periphery` → `periphery scan` |
| **xcodebuild** | 构建/测试 | Xcode 内置 |
| **xcodegen** | 项目文件生成 | `brew install xcodegen` + `project.yml` |

**推荐组合**：SwiftLint (lint) + SwiftFormat (format) + Periphery (dead code)

**.swiftlint.yml 参考**：
```yaml
included:
  - Sources
  - Tests
excluded:
  - Pods
  - Carthage
opt_in_rules:
  - empty_count
  - closure_spacing
  - force_unwrapping
  - implicitly_unwrapped_optional
  - override_in_extension
  - private_outlet
  - vertical_whitespace_closing_braces
disabled_rules:
  - trailing_whitespace
line_length:
  warning: 120
  error: 200
```

---

## CodeGraph (Optional Enhancement) · CodeGraph（可选增强）

CodeGraph CLI builds a code relationship graph from your project, enabling impact analysis and call chain tracing. When integrated, dev-pipeline uses it to identify impacted test files during review and regression testing.
CodeGraph CLI 从项目代码构建代码关系图，支持影响分析和调用链追踪。集成后，dev-pipeline 在审查和回归测试阶段使用它识别受影响的测试文件。

| 命令 | 用途 | 说明 |
|------|------|------|
| `codegraph affected --stdin --quiet` | Impacted test files | Pipe `git diff --name-only`, returns bare file paths · 管道传入 diff，返回受影响测试文件路径 |
| `codegraph status --json` | Index health check | Verify `.codegraph/codegraph.db` is fresh · 验证索引状态 |
| `codegraph impact <symbol> --depth N` | Blast radius | Trace impact of a specific symbol · 追踪符号影响范围 |
| `codegraph callers/callees <symbol>` | Call chain | Trace upstream/downstream dependencies · 追踪上下游调用链 |

**Canonical pipe pattern** · 标准管道模式:

```bash
git diff --name-only | codegraph affected --stdin --quiet
```

**Integration in dev-pipeline** · 在 dev-pipeline 中的集成:
- Phase 0: Auto-detect `.codegraph/codegraph.db` → set `codegraph_available` flag · 自动检测
- Phase 1: Impacted test files → appended to review agent prompts as context · 审查上下文
- Phase 2: Impacted test files → targeted regression test execution · 精准回归测试

**Install**: See [CodeGraph documentation](https://github.com/colbymchenry/codegraph). The `.codegraph/` directory is local and auto-gitignored. · 安装请参考 CodeGraph 文档，`.codegraph/` 目录为本地索引，自动 gitignore。

---

## Universal Tools (all languages) · 通用工具

| 工具 | 用途 | 适用 |
|------|------|------|
| **EditorConfig** | 跨编辑器基础格式统一 | 所有项目，`.editorconfig` 文件 |
| **pre-commit** | Git 提交前 hook 框架 | 所有项目，`.pre-commit-config.yaml` |
| **ShellCheck** | Shell 脚本 lint | 项目中有 `.sh` 脚本时 |
| **actionlint** | GitHub Actions workflow lint | 有 `.github/workflows/` 时 |
| **Hadolint** | Dockerfile lint | 有 `Dockerfile` 时 |
| **Trivy** | 依赖/镜像漏洞扫描 | CI/CD 管道中 |

---

## How to Use This Doc During Review · 审查时如何使用此文档

1. During **Phase 0 environment discovery**, detect whether the project already has lint/format/typecheck configs · 检测项目是否已有 lint/format/typecheck 配置
2. If a key tool is missing (e.g. a Java project without Checkstyle), add a 🟡 suggestion to the review results · 如缺失关键工具，在审查结果中作为 🟡 建议项标注:
   - Format · 格式: `TOOLING: suggest adding [tool] for [purpose]. Install: [command]`
3. Never force installation — suggest only, let the user decide · 不要强制安装，仅建议
4. If the project already has configs, respect existing tool output (an ESLint error IS a BLOCKER) · 尊重现有工具输出
