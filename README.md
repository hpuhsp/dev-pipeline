# Dev Pipeline · 开发流水线

Multi-step code delivery skill pack for Claude Code and other AI Agents.

适用于 Claude Code 及其他 AI Agent 的多步骤代码交付技能包。

## Pipeline · 管道流程

```
git diff → ① Code Review → ② Unit Test → ③ Commit Message → ④ Branch → ⑤ Commit
           · 代码审查       · 单元测试      · 提交信息         · 分支      · 提交
```

## Features · 特性

- **Dual-mode Review** · 双模式审查：Claude Code → 3-agent parallel review; other agents → in-skill serial fallback
- **6 Coding Standards** · 6 语言编码规范：Alibaba P3C, PEP 8, Airbnb JS, Vue 3, uni-app UTS, Android Kotlin
- **Auto-detection** · 自动检测：test framework, project tech stack, commit type
- **Conventional Commits** · 规范提交：auto type/scope inference, `deps` type support, 70-char subject
- **Portable** · 可移植：pure Markdown, zero external dependencies, copy-and-use
- **Fix-First Review** · 修复优先：AUTO-FIX for mechanical issues, ASK for architectural decisions

## Install · 安装

**User-level (all projects) · 用户级：**
```bash
cp -r .claude/skills/dev-pipeline ~/.claude/skills/dev-pipeline
```

**Project-level · 项目级：**
```bash
cp -r .claude/skills/dev-pipeline <project>/.claude/skills/dev-pipeline
```

**From .skill file · 从打包文件：**
```bash
# Unzip dev-pipeline.skill to target .claude/skills/ directory
```

**From npm (coming soon) · npm 安装：**
```bash
npx skills add hpuhsp/dev-pipeline -g
```

## Usage · 使用方式

| Mode · 模式 | Triggers · 触发词 |
|-------------|-------------------|
| Full Pipeline | `commit my changes`, `ship it`, `提交代码`, `改完了` |
| Code Review | `review my code`, `code review`, `review我的改动` |
| Test Generation | `generate tests`, `生成测试`, `写单元测试` |
| Commit Message | `write commit message`, `生成commit message` |
| Quick Mode | `quick commit`, `skip review`, `快速提交` |

## File Structure · 文件结构

```
dev-pipeline/
├── SKILL.md                         # Pipeline orchestrator · 主编排器
└── references/
    ├── review-agents.md             # 3-Agent parallel review prompts · 并行审查
    ├── review-checklist.md          # In-skill serial review fallback · 串行回退
    ├── coding-standards.md          # Authoritative coding standards · 编码规范
    ├── test-generation.md           # Test generation guides · 测试生成
    ├── tooling.md                   # Static analysis toolchain · 工具链推荐
    └── commit-conventions.md        # Conventional Commits spec · 提交规范
```

## License · 许可

MIT
