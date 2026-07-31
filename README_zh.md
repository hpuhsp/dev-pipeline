# Dev Pipeline

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.5.0-blue.svg)](CHANGELOG.md)
[![Validation](https://github.com/hpuhsp/dev-pipeline/actions/workflows/validate.yml/badge.svg)](https://github.com/hpuhsp/dev-pipeline/actions/workflows/validate.yml)

[English](README.md)

Dev Pipeline 是面向 Claude Code、Codex 及其他 AI 编程 Agent 的意图路由式代码交付 Skill。它提供代码审查、单元测试、提交信息、分支选择和提交执行等可组合节点，不会把每次请求都强制变成完整流水线。

## 为什么使用 Dev Pipeline

Dev Pipeline 会先分析用户提示词，再选择满足请求的最小节点集合，并在目标节点完成后停止。

```text
用户提示词
    |
    v
意图路由器
    |
    +-- Review  代码审查
    +-- Test    单元测试
    +-- Message 提交信息
    +-- Branch  分支选择
    +-- Commit  提交执行
    `-- 明确组合或完整流水线
```

只有用户明确要求端到端交付时，才执行：

```text
Review -> Test -> Message -> Branch -> Commit
```

## 路由示例

| 用户提示词 | 目标路由 | 不会执行 |
|---|---|---|
| `审查当前改动` | Review | Test、Message、Branch、Commit |
| `生成单元测试和覆盖率报告` | Test | Review、Branch、Commit |
| `生成 commit message` | Message | Review、Test、Branch、Commit |
| `创建 feature 分支` | Branch | Review、Test、Commit |
| `提交当前改动` | Commit + 最小安全检查 | 非必要的 Review、Test、Branch |
| `审查并测试` | Review + Test | Message、Branch、Commit |
| `执行完整交付流水线` | Full Pipeline | 无 |

用户的显式排除具有最高优先级。例如“提交并推送，不要审查”不会进入 Review 或 Test。

## 核心能力

### 提示词意图路由

- 从提示词生成目标节点、最小依赖节点和排除节点。
- 禁止完成一个阶段后隐式流转到下一阶段。
- 仅按目标节点加载环境信息和参考文档，减少上下文与 token 消耗。
- Push、PR 等扩展动作必须由用户明确请求。

### 代码审查

- Agent 工具可用且改动规模合适时，使用三个并行审查视角。
- 小规模改动或不支持子 Agent 时，自动回退为 Skill 内串行审查。
- 覆盖正确性、安全性、性能、可维护性和项目一致性。
- 支持 Alibaba P3C、PEP 8、Airbnb JavaScript、Vue 3、uni-app UTS、Android Kotlin、Swift API Design Guidelines 和 WCAG。
- 按置信度过滤发现，并区分机械性自动修复与需要用户决策的问题。

### 变更感知测试

无第三方依赖的测试运行器会选择成本最低且安全的层级：

| 层级 | 典型变更 | 行为 |
|---|---|---|
| `structural` | README、CHANGELOG、LICENSE 或纯 `docs/` | 跳过单测，保留结构校验 |
| `unit` | Skill、脚本、测试、CI、发布包或未知文件 | 运行确定性测试 |
| `agent-eval` | 审查提示词、检查清单或评估样例 | 运行确定性测试，建议按需执行 Agent 评估 |

JSON 与 Markdown 报告包含：测试总数、通过率、耗时、行为需求覆盖率、场景覆盖率、失败标识，以及 Agent 评估 token 预算和实际消耗。普通确定性验证的 Agent token 消耗为 0。

### 多仓库 Git 路由

- 解析每个变更文件所属的 Git worktree。
- Git Submodule 视为独立仓库。
- 没有独立 `.git` 元数据的 Git Subtree 归属父仓库。
- 变更跨多个独立仓库时停止并要求用户选择目标仓库。
- 分支和提交命令统一使用 `git -C <target_repo>`。
- 不执行 `git stash`，不读取 `refs/stash`，不分析已 stash 内容。

### 按仓库隔离的 CodeGraph

- 对每个发生变更的 Git worktree 独立检测 CodeGraph，不使用全流程全局可用标记。
- 仅当本地索引存在、CLI 可执行且状态健康时，才执行受影响测试分析。
- 始终在同一个仓库根目录中执行 diff、CodeGraph 查询和测试命令。
- Git Submodule 必须拥有自己的 CodeGraph 索引；真正的 Git Subtree 使用父仓库索引。
- 单个仓库不可用时仅在该仓库回退，并报告按仓库区分的原因。
- 仅在用户明确要求、复杂改动或回归选择本会过宽/过慢时启用 CodeGraph；普通局部改动不执行任何 CodeGraph 命令。
- 启用后的审查或测试必须先产生可审计的 `affected` 执行证据；空结果与执行失败会明确区分。

### 安全提交

- 根据真实变更生成 Conventional Commit 信息。
- 自动识别 Git-Flow 与常规分支命名风格。
- 选择性暂存文件，不使用 `git add .` 或 `git add -A`。
- 检查凭据、私钥和敏感文件。
- 将提交钩子错误区分为可自动修复、需人工修复和基础设施问题。

## 安装

通过 GitHub 安装：

```bash
npx skills add hpuhsp/dev-pipeline -g
```

手动安装到项目：

```bash
git clone https://github.com/hpuhsp/dev-pipeline.git
cp -r dev-pipeline/.claude/skills/dev-pipeline <your-project>/.claude/skills/dev-pipeline
```

安装到用户目录：

```bash
cp -r .claude/skills/dev-pipeline ~/.claude/skills/dev-pipeline
```

仓库中的 `dev-pipeline.skill` 是与源码保持同步的便携发布包。修改 Skill 后运行 `python scripts/sync_skill.py`，即可重建发布包并同步本机已配置副本；使用 `--check` 可只验证而不写入。

如需一次完成验证、提交、推送 `main` 并快进同步 `origin/master`，运行 `python scripts/publish_master.py --message "type(scope): summary"`。使用 `--dry-run` 仅查看目标操作；无需同步本机 Skill 时可加 `--skip-user-skill-sync`。

## 使用方式

直接描述需要的动作，无需 Slash Command：

```text
审查当前改动的正确性和安全性。
为当前变更生成单元测试和覆盖率报告。
根据暂存文件生成 Conventional Commit 信息。
在拥有这些变更的仓库中创建合适的分支。
提交当前改动，但不要执行审查和测试。
执行完整流水线，任何验证失败时停止。
```

## 验证

运行完整确定性测试：

```bash
python scripts/test_runner.py --all
```

根据当前工作区变更智能选择测试：

```bash
python scripts/test_runner.py --report-dir artifacts/test-results
```

GitHub Actions 使用相同的变更感知验证，并上传 JSON 与 Markdown 报告。

## 项目结构

```text
.
|-- .claude/skills/dev-pipeline/
|   |-- SKILL.md
|   `-- references/
|-- scripts/test_runner.py
|-- scripts/sync_skill.py
|-- scripts/publish_master.py
|-- tests/
|-- docs/superpowers/
|-- dev-pipeline.skill
|-- CHANGELOG.md
`-- LICENSE
```

## 设计原则

- 用户显式意图优先于关键词推断。
- 选择最小安全路由，避免加载无关上下文。
- 普通 CI 优先使用确定性验证，而不是模型评估。
- 保持仓库边界，禁止分析 stash 内容。
- 在报告完成前取得最新验证证据。

## License

[MIT](LICENSE)
