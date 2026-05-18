# SKILL 规范文档

> **版本**: 3.0.0
> **日期**: 2026-04-02
> **参考**: [Agent Skills 规范](https://agentskills.io/specification)

---

## 1. 概述

**Skill（技能）**是一个可复用的能力单元，包含结构化元数据和指令，告诉 AI agent 它能做什么以及如何做。

---

## 2. 目录结构

Skill 是一个**目录**，至少包含一个 `SKILL.md` 文件：

```
skill-name/
├── SKILL.md          # 必需：YAML frontmatter + Markdown 指令
├── scripts/          # 可选：可执行代码
├── references/       # 可选：附加文档
├── assets/           # 可选：模板、数据、图片
└── ...
```

---

## 3. SKILL.md 格式

`SKILL.md` 必须包含 YAML frontmatter，后跟 Markdown 内容。

```
---                          ← YAML frontmatter
name: skill-name             ← 必需
description: 这个技能做什么    ← 必需（1-1024 字符）
  以及何时使用。
---                          ← frontmatter 结束

## Instructions                  ← Markdown body
1. 分步指导
2. ...
```

---

## 4. Frontmatter 字段

### 4.1 必需字段

| 字段 | 约束 |
|------|------|
| `name` | 最多 64 字符。仅小写 `a-z`、`0-9`、`-`。禁止首尾/连续连字符。必须与父目录名一致。 |
| `description` | 最多 1024 字符。描述技能功能和适用场景，包含有助于 agent 判断何时使用的关键词。 |

**有效名称**: `pdf-processing`, `data-analysis`, `code-review`

**无效名称**:
```
PDF-Processing   ← 不允许大写
-pdf             ← 不能以连字符开头
pdf--processing  ← 不允许连续连字符
```

**良好描述**:
```
"从 PDF 文件提取文本和表格，填写表单，合并多个 PDF。
适用于处理 PDF 文档、填写表单或提取文档内容的场景。"
```

**不佳描述**:
```
"帮助处理 PDF。"
```

### 4.2 可选字段

| 字段 | 约束 |
|------|------|
| `license` | 许可证名称或捆绑许可证文件路径。建议简短。 |
| `compatibility` | 最多 500 字符。环境要求（如目标产品、系统包、网络访问）。大多数技能不需要此字段。 |
| `metadata` | 任意键值对映射（字符串键到字符串值）。键名应唯一以避免冲突。 |
| `allowed-tools` | 预批准工具的空格分隔列表。（实验性——支持程度因 agent 实现而异。） |

---

## 5. Body 内容

Frontmatter 之后的 Markdown body 包含技能指令。**无格式限制**——写出任何有助于 agent 完成任务的内容。

**推荐章节**：
- 分步指令
- 输入输出示例
- 常见边界情况

---

## 6. 可选目录

| 目录 | 用途 |
|------|------|
| `scripts/` | 可执行代码（Python、Bash、JavaScript 等）。应自包含、注明依赖、妥善处理错误。 |
| `references/` | 按需加载的附加文档：`REFERENCE.md`、`FORMS.md`、领域特定文件。保持文件聚焦——agent 按需加载。 |
| `assets/` | 静态资源：模板、图片、数据文件。 |

---

## 7. 渐进式披露

按上下文使用效率组织技能：

| 层级 | Token 数 | 加载时机 |
|------|---------|---------|
| 元数据 | ~100 | 所有技能启动时 |
| 指令 | <5000 | 技能激活时 |
| 资源 | 按需 | 仅在需要时 |

> 保持 `SKILL.md` 在 500 行以内。将详细参考资料移到单独文件。

---

## 8. 文件引用

使用相对于 skill 根目录的相对路径：

```markdown
详见[参考指南](references/REFERENCE.md)。

运行提取脚本：
scripts/extract.py
```

保持文件引用在 `SKILL.md` **一层深度内**。避免深层嵌套的引用链。

---

## 9. 验证

使用 `skills-ref` 验证：

```bash
skills-ref validate ./my-skill
```

此命令检查 frontmatter 是否有效并符合所有命名规范。

---

## 10. 快捷参考

### Frontmatter 字段

| 字段 | 必需 |
|------|:----:|
| `name` | **是** |
| `description` | **是** |
| `license` | 否 |
| `compatibility` | 否 |
| `metadata` | 否 |
| `allowed-tools` | 否 |

### 目录结构

```
skill-name/               # kebab-case
├── SKILL.md             # 必需入口点
├── scripts/             # 可选：可执行脚本
├── references/          # 可选：按需文档
└── assets/              # 可选：静态资源
```

---

**文档版本**: 3.0.0
**最后更新**: 2026-04-02
**参考**: [Agent Skills Specification](https://agentskills.io/specification)
