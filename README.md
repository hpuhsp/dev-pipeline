<p align="right"><sub><a href="#-english">English</a> | <a href="#-chinese">中文</a></sub></p>

---

<a id="-english"></a>
# Dev Pipeline

Multi-step code delivery skill pack for Claude Code and other AI Agents.

## Pipeline

```
git diff → ① Code Review → ② Unit Test → ③ Commit Message → ④ Branch → ⑤ Commit
```

## Features

- **Dual-mode Review**: 3-agent parallel review (Claude Code) / in-skill serial fallback (other agents)
- **6 Coding Standards**: Alibaba P3C, PEP 8, Airbnb JS, Vue 3, uni-app UTS, Android Kotlin
- **Auto-detection**: test framework, project tech stack, commit type
- **Conventional Commits**: auto type/scope inference, `deps` type, 70-char subject
- **Portable**: pure Markdown, zero external dependencies
- **Fix-First Review**: AUTO-FIX for mechanical issues, ASK for architectural decisions

## Install

```bash
cp -r .claude/skills/dev-pipeline ~/.claude/skills/dev-pipeline   # user-level
npx skills add hpuhsp/dev-pipeline -g                              # or via npm
```

## Usage

| Mode | Triggers |
|------|----------|
| Full Pipeline | `commit my changes`, `ship it`, `done coding` |
| Code Review | `review my code`, `code review` |
| Test Generation | `generate tests` |
| Commit Message | `write commit message` |
| Quick Mode | `quick commit`, `skip review` |

## File Structure

```
dev-pipeline/
├── SKILL.md                         # Pipeline orchestrator
└── references/
    ├── review-agents.md             # 3-agent parallel review prompts
    ├── review-checklist.md          # In-skill serial review fallback
    ├── coding-standards.md          # Authoritative coding standards
    ├── test-generation.md           # Test generation guides
    ├── tooling.md                   # Static analysis toolchain
    └── commit-conventions.md        # Conventional Commits spec
```

## License

MIT

---

<a id="-chinese"></a>
# Dev Pipeline · 开发流水线

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
dev-pipeline/
├── SKILL.md                         # 主编排器
└── references/
    ├── review-agents.md             # 3 Agent 并行审查 prompt
    ├── review-checklist.md          # Skill 内串行审查清单
    ├── coding-standards.md          # 权威编码规范速查
    ├── test-generation.md           # 测试生成指南
    ├── tooling.md                   # 静态分析工具链推荐
    └── commit-conventions.md        # Conventional Commits 规范
```

## 许可

MIT
