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
| `codegraph affected --stdin --quiet` | Impacted test files | Pipe `git diff HEAD --name-only` to include staged and unstaged changes; returns bare file paths · 管道传入已暂存和未暂存变更，返回受影响测试文件路径 |
| `codegraph status --json` | Index health check | Verify `.codegraph/codegraph.db` is fresh · 验证索引状态 |
| `codegraph context "<task>" --max-nodes 30 --max-code 8 --format markdown` | Task map | Build bounded, relevant context before broad file reads |
| `codegraph query <symbol> --limit 10` | Symbol lookup | Resolve the changed or suspected symbol before graph traversal |
| `codegraph impact <symbol> --depth N` | Blast radius | Trace impact of a specific symbol · 追踪符号影响范围 |
| `codegraph callers/callees <symbol>` | Call chain | Trace upstream/downstream dependencies · 追踪上下游调用链 |

**Canonical pipe pattern (repository-scoped)** · 标准管道模式（仓库作用域）:

```bash
(cd "<repository.root>" && git diff HEAD --name-only | codegraph affected --stdin --quiet)
```

The current directory must be the same repository that owns the diff and `.codegraph` index. Do not run this from a parent repository for a submodule. On PowerShell, use `Push-Location "<repository.root>"; try { git diff HEAD --name-only | codegraph affected --stdin --quiet } finally { Pop-Location }`.

**Integration in dev-pipeline** · 在 dev-pipeline 中的集成:
- Phase 0: Create one `repository_context` for every changed Git worktree, but defer CodeGraph detection. Set `repository_context.codegraph.eligible = true` only for an explicit CodeGraph/affected/impact request, a complex cross-module/API/route/core-service/unknown-call-chain review, or regression selection that would otherwise be broad, slow, or cross-package. For all other changes, record `not-needed` and make no CodeGraph call.
- For an eligible context only, require all of the following before setting `repository_context.codegraph.available = true` · 每个符合条件的变更仓库独立启用前必须同时满足：
  1. `<repository.root>/.codegraph/codegraph.db` exists;
  2. `command -v codegraph` (POSIX) or `Get-Command codegraph` (PowerShell) succeeds;
  3. `codegraph status --json` executed from `<repository.root>` exits successfully and returns a healthy, usable index state.
- If any check fails, record `index-missing`, `cli-missing`, or `status-unhealthy` on that context and fall back only for that context.
- A submodule is an independent context and must have its own index. A subtree without independent Git metadata uses its parent context and parent index.
- Detection is read-only. Never install, initialize, index, sync, or rebuild CodeGraph automatically.
- `wasm` backend is usable but slower: record `wasm-backend` as a warning; do not classify it as `status-unhealthy` solely for that backend.
- Phase 1: Per-context gate evidence and impacted test files → appended to review prompts with repository-root labels · 审查上下文
- Phase 2: Per-context gate evidence and impacted test files → targeted regression test execution from the same repository root · 精准回归测试

### Execution evidence gate

For every eligible repository context in a Review or Test route, run the bundled script before starting work:

```bash
python "<skill-dir>/scripts/codegraph_gate.py" --repository "<repository.root>"
```

The script is read-only. It runs `codegraph status --json`, obtains changed paths through `git diff HEAD --name-only`, then runs `codegraph affected --stdin --json` from the same repository root. Persist its JSON result. An `affected.state` of `executed` or `empty` is normal completion; `failed` is valid evidence only when the report includes its error and the pipeline falls back for that repository. Missing or `pending` evidence means the Review/Test phase is not complete only for an eligible, available context. Ineligible contexts must not run the script and are complete with `affected.state = not-required`.

If Python is unavailable, run the canonical quiet command, record its cwd, exit code, and output count, then use the same completion rule. Never claim `empty` without executing a command.

### Exploration gate for complex changes

Use CodeGraph before broad `grep`/read exploration when the change is cross-module, affects a public API, route, core service, or unknown bug call chain. Keep this selective; do not add graph calls to trivial, local, or documentation-only changes.

| Need | First command | Follow-up |
|---|---|---|
| Map an unfamiliar task | `codegraph context "<task>" --max-nodes 30 --max-code 8 --format markdown` | Read only source the result does not cover |
| Resolve a changed symbol | `codegraph query <symbol> --limit 10` | `callers` and/or `callees` |
| Estimate blast radius | `codegraph impact <symbol> --depth 2` | Add impacted modules/tests to review scope |
| Trace a known dependency direction | `codegraph callers <symbol>` or `codegraph callees <symbol>` | Inspect only the relevant returned nodes |

Attach a compact `CODEGRAPH EXPLORATION` block with command, root, and relevant findings to the review context. Graph results are a structured starting point, not runtime proof; use normal code review for dynamic dispatch, reflection, generated code, and framework conventions.

### Maintenance and integration boundaries

`codegraph init`, `index`, `sync`, and `index --force` are user-approved maintenance operations, never pipeline actions. MCP server setup and TypeScript API integration are host/platform choices outside this Skill; use them when already configured, but the CLI gate must remain sufficient on every supported Agent.

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
