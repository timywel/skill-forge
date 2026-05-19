# SKILL 规范文档

> **版本**: 3.1.0
> **日期**: 2026-05-18
> **参考**: [Agent Skills 规范](https://agentskills.io/specification)

---

## 1. 概述

**Skill（技能）**是一个可复用的能力单元，包含结构化元数据和指令，告诉 AI agent 它能做什么以及如何做。

---

## 2. 目录结构

Skill 是一个**目录**，至少包含一个 `SKILL.md` 文件：

```
skill-name/
├── SKILL.md             # 必需：YAML frontmatter + Markdown 指令（英文，LLM 读取）
├── SKILL.zh.md          # 可选：中文内容（LLM 读取）
├── skill.meta.yaml      # 可选：索引器/CLI 使用的元数据（LLM 不读取）
├── scripts/             # 可选：可执行代码
├── references/          # 可选：附加文档
├── assets/              # 可选：模板、数据、图片等静态资源
└── ...
```

### 2.1 文件分离原则

| 文件 | 用途 | 读取者 |
|------|------|--------|
| `SKILL.md` | LLM 读取的英文内容 | LLM |
| `SKILL.zh.md` | LLM 读取的中文内容 | LLM |
| `skill.meta.yaml` | 所有元数据字段 | 索引器 / CLI / API |

**为什么分离？** LLM 只读取内容文件（SKILL.md / SKILL.zh.md）。`category`、`cognitive_phase`、`triggers`、`name_zh` 等 BaiZe 特定字段存储在 `skill.meta.yaml` 中，节省 token。索引器无需解析 markdown 内容即可读取元数据。

---

## 3. SKILL.md 格式

`SKILL.md` 必须包含 YAML frontmatter，后跟 Markdown 内容。

```
---                          ← YAML frontmatter
name: skill-name             ← 必需
description: 这个技能做什么    ← 必需（1-1024 字符）
  以及何时使用。
---                          ← frontmatter 结束

## 指令                     ← Markdown 正文
1. 分步指导
2. ...
```

**注意**：`SKILL.md` frontmatter 仅包含 [Agent Skills](https://agentskills.io/specification) 要求的必填字段：`name`、`description`、`license`、`compatibility`、`metadata`、`allowed-tools`。BaiZe 特定字段（`category`、`cognitive_phase`、`triggers`、i18n 字段等）写入 `skill.meta.yaml`。

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

## 5. skill.meta.yaml 格式（BaiZe 元数据）

`skill.meta.yaml` 文件存储 BaiZe 特定元数据字段。由索引器/CLI 读取，**LLM 不解析此文件**。

```yaml
# BaiZe Skill 元数据
# 仅供索引器/CLI 读取 — LLM 不读取此文件

# === 标识与版本 ===
name: code-generate
version: "1.0.0"

# === i18n 多语言字段 ===
name_key: skills.code-generate.name
name_zh: 代码生成
name_en: code-generate
description_key: skills.code-generate.description
description_zh: "根据技术规范自动生成代码及对应测试用例。"
description_en: "Automatically generate code and corresponding tests based on technical specifications."

# === 分类与认知阶段 ===
category: code                            # code|quality|test|security|doc|infra|spec|project|tooling|internet|domain|process|loop|framework|system
cognitive_phase: executor                # observer|strategist|executor|critic

# === 层与来源 ===
layer: system                             # system|user
origin: BaiZe                              # GSD|ECC|Superpowers|Ralph|Meta|BaiZe

# === MCP 配置 ===
mcp_server: null                          # MCP server 标识（若有）
mcp_tools: []                              # MCP 工具列表

# === 触发与能力 ===
triggers:                                   # 触发关键词列表
  - "project-create"
  - "feature-generate"
  - "code-generation"

capabilities:                               # 能力列表
  - "code-generation"
  - "test-generation"

commands: []                                # CLI 依赖命令

# === 可选字段 ===
compatibility: null
allowed_tools: []
metadata: {}
```

### 5.1 Category 可选值

| 值 | 说明 |
|----|------|
| `code` | 代码生成、实现 |
| `quality` | 代码质量、Linting、Review |
| `test` | 测试生成、验证 |
| `security` | 安全扫描、漏洞评估 |
| `doc` | 文档编写 |
| `infra` | 基础设施、部署、Docker、K8s |
| `spec` | 需求、规格说明 |
| `project` | 项目脚手架、模板 |
| `tooling` | 工具生成、构建脚本 |
| `internet` | 网页抓取、浏览器自动化、搜索 |
| `domain` | 领域特定（医疗、金融等） |
| `process` | 工作流、流水线编排 |
| `loop` | 迭代、反馈循环 |
| `framework` | 框架特定技能 |
| `system` | 系统级、元技能 |

### 5.2 Cognitive Phase 可选值

| 值 | 说明 |
|----|------|
| `observer` | 分析、调研、监控 |
| `strategist` | 规划、设计、路线图 |
| `executor` | 执行操作、生成代码 |
| `critic` | 评审、评估、提供反馈 |

### 5.3 向后兼容性

如果 `skill.meta.yaml` 不存在，索引器从 `SKILL.md` frontmatter 推断缺失字段：
- `category` → 从 `name` + `description` 关键词推断
- `cognitive_phase` → 从 `description` 关键词推断
- `triggers` → 从 `name` + `description` 关键词推断
- `name_zh`、`description_zh` → 空（无中文内容）

---

## 6. 正文内容

Frontmatter 之后的 Markdown 正文包含技能指令。**无格式限制**——写出任何有助于 agent 完成任务的内容。

**推荐章节**：
- 分步指令
- 输入输出示例
- 常见边界情况

---

## 7. 可选目录

| 目录 | 用途 |
|------|------|
| `scripts/` | 可执行代码（Python、Bash、JavaScript 等）。应自包含、注明依赖、妥善处理错误。 |
| `references/` | 按需加载的附加文档：`REFERENCE.md`、`FORMS.md`、领域特定文件。保持文件聚焦——agent 按需加载。 |
| `assets/` | 静态资源：模板、图片、数据文件。 |

---

## 8. 渐进式披露

按上下文使用效率组织技能：

| 层级 | Token 数 | 加载时机 |
|------|---------|---------|
| 元数据 | ~100 | 所有技能启动时 |
| 指令 | <5000 | 技能激活时 |
| 资源 | 按需 | 仅在需要时 |

> 保持 `SKILL.md` 在 500 行以内。将详细参考资料移到单独文件。

---

## 9. 文件引用

使用相对于 skill 根目录的相对路径：

```markdown
详见[参考指南](references/REFERENCE.md)。

运行提取脚本：
scripts/extract.py
```

保持文件引用在 `SKILL.md` **一层深度内**。避免深层嵌套的引用链。

---

## 10. 验证

使用 `skills-ref` 验证：

```bash
skills-ref validate ./my-skill
```

此命令检查 frontmatter 是否有效并符合所有命名规范。

---

## 11. 快捷参考

### SKILL.md Frontmatter 字段（LLM 读取）

| 字段 | 必需 |
|------|:----:|
| `name` | **是** |
| `description` | **是** |
| `license` | 否 |
| `compatibility` | 否 |
| `metadata` | 否 |
| `allowed-tools` | 否 |

### skill.meta.yaml 字段（索引器/CLI 读取）

| 字段 | 说明 |
|------|------|
| `name` | Skill 名称 |
| `version` | 版本字符串 |
| `name_key` | name 的 i18n key |
| `name_zh` | 中文名称 |
| `name_en` | 英文名称 |
| `description_key` | description 的 i18n key |
| `description_zh` | 中文描述 |
| `description_en` | 英文描述 |
| `category` | Skill 分类 |
| `cognitive_phase` | 认知阶段 |
| `layer` | system / user |
| `origin` | 来源 |
| `mcp_server` | MCP server 标识 |
| `mcp_tools` | MCP 工具列表 |
| `triggers` | 触发关键词 |
| `capabilities` | 能力列表 |
| `commands` | CLI 依赖命令 |

### 目录结构

```
skill-name/               # kebab-case
├── SKILL.md             # 必需：LLM 读取的英文内容
├── SKILL.zh.md          # 可选：LLM 读取的中文内容
├── skill.meta.yaml      # 可选：BaiZe 索引器元数据
├── scripts/             # 可选：可执行文件
├── references/          # 可选：按需加载的文档
└── assets/              # 可选：静态资源
```

---

**文档版本**: 3.1.0
**最后更新**: 2026-05-18
**参考**: [Agent Skills Specification](https://agentskills.io/specification)