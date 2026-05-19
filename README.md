# Dev Pipeline

多步骤代码交付技能包，适用于 Claude Code 及其他 AI Agent。

## 管道流程

```
git diff → ① 代码审查 → ② 单元测试 → ③ Commit Message → ④ 分支选择 → ⑤ 提交
```

## 特性

- **双模式审查**：Claude Code 环境 3 Agent 并行审查；其他环境 Skill 内串行审查
- **6 语言编码规范**：阿里 P3C、PEP 8、Airbnb JS、Vue 3、uni-app UTS、Android Kotlin
- **自动检测**：测试框架、项目技术栈、提交类型
- **Conventional Commits**：自动推断 type/scope，支持 deps 类型
- **可移植**：纯 Markdown，零外部依赖，复制即用

## 安装

**用户级（所有项目可用）：**
```bash
cp -r .claude/skills/dev-pipeline ~/.claude/skills/dev-pipeline
```

**项目级（单项目）：**
```bash
cp -r .claude/skills/dev-pipeline <project>/.claude/skills/dev-pipeline
```

**从 .skill 文件安装：**
```bash
# 解压 dev-pipeline.skill 到目标项目的 .claude/skills/ 目录
```

## 使用方式

| 模式 | 触发词 |
|------|--------|
| 完整管道 | "提交代码"、"改完了"、"ship it" |
| 代码审查 | "review 我的改动"、"帮我做 code review" |
| 测试生成 | "生成测试"、"写单元测试" |
| Commit 生成 | "生成 commit message"、"写 changelog" |
| 快速模式 | "快速提交"（跳过审查和测试） |

## 文件结构

```
dev-pipeline/
├── SKILL.md                    # 主编排器
└── references/
    ├── review-agents.md        # 3 Agent 并行审查 prompt
    ├── review-checklist.md     # Skill 内串行审查清单
    ├── coding-standards.md     # 权威编码规范速查
    ├── test-generation.md      # 测试生成指南
    ├── tooling.md              # 静态分析工具链推荐
    └── commit-conventions.md   # Conventional Commits 规范
```

## 许可

MIT
