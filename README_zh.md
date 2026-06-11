# Dev Pipeline · 开发流水线

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/hpuhsp/dev-pipeline.svg)](https://github.com/hpuhsp/dev-pipeline/stargazers)

[English](README.md) | 中文版

---

适用于 Claude Code 及其他 AI Agent 的多步骤代码交付技能包。

## 管道流程

```
git diff → ① 代码审查 → ② 单元测试 → ③ Commit Message → ④ 分支选择 → ⑤ 提交
```

## 特性

- **双模式审查**：Claude Code 启用 3 Agent 并行审查；其他环境自动退化为 Skill 内串行审查
- **6 语言编码规范**：阿里 P3C、PEP 8、Airbnb JS、Vue 3、uni-app UTS、Android Kotlin
- **自动检测**：测试框架、项目技术栈、提交类型
- **Conventional Commits**：自动推断 type/scope，支持 `deps` 类型，70 字符 subject
- **可移植**：纯 Markdown，零外部依赖，复制即用
- **修复优先审查**：机械问题自动修复 (AUTO-FIX)，架构决策请用户裁定 (ASK)

## 安装

```bash
cp -r .claude/skills/dev-pipeline ~/.claude/skills/dev-pipeline   # 用户级
npx skills add hpuhsp/dev-pipeline -g                              # npm 安装
```

## 使用方式

| 模式 | 触发词 |
|------|--------|
| 完整管道 | `提交代码`、`改完了`、`ship it` |
| 代码审查 | `review我的改动`、`帮我做code review` |
| 测试生成 | `生成测试`、`写单元测试` |
| Commit 生成 | `生成commit message`、`写changelog` |
| 快速模式 | `快速提交`、`skip review` |

## 文件结构

```
.claude/skills/dev-pipeline/
├── SKILL.md                         # 主编排器
└── references/
    ├── review-agents.md             # 3 Agent 并行审查 prompt
    ├── review-checklist.md          # Skill 内串行审查清单
    ├── coding-standards.md          # 权威编码规范速查
    ├── test-generation.md           # 测试生成指南
    ├── tooling.md                   # 静态分析工具链推荐
    └── commit-conventions.md        # Conventional Commits 规范
evals/                               # 植入缺陷的样例 diff + 预期发现
CHANGELOG.md                         # 版本历史
dev-pipeline.skill                   # 打包产物（zip），由 git archive 重建
```

## 版本

见 [CHANGELOG.md](CHANGELOG.md)。打包产物 `dev-pipeline.skill` 由 CI 保证与源文件同步。

## 许可

[MIT](LICENSE)
