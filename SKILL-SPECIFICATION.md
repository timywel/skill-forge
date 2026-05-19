# SKILL Specification

> **Version**: 3.1.0
> **Date**: 2026-05-18
> **Reference**: [Agent Skills Specification](https://agentskills.io/specification)

---

## 1. Overview

A **Skill** is a reusable unit that extends an AI agent's capabilities. It consists of structured metadata and instructions that tell the agent what it can do and how to do it.

---

## 2. Directory Structure

A skill is a **directory** containing at minimum a `SKILL.md` file:

```
skill-name/
├── SKILL.md             # Required: YAML frontmatter + Markdown instructions (English, LLM reads)
├── SKILL.zh.md          # Optional: Chinese content (LLM reads)
├── skill.meta.yaml      # Optional: metadata for indexer/CLI (not read by LLM)
├── scripts/             # Optional: executable code
├── references/          # Optional: additional documentation
├── assets/              # Optional: templates, data, images
└── ...
```

### 2.1 File Separation Principle

| File | Purpose | Reader |
|------|---------|--------|
| `SKILL.md` | English content for LLM | LLM |
| `SKILL.zh.md` | Chinese content for LLM | LLM |
| `skill.meta.yaml` | All metadata fields | Indexer / CLI / API |

**Why separate?** LLM reads only the content files (SKILL.md / SKILL.zh.md). Metadata like `category`, `cognitive_phase`, `triggers`, `name_zh`, etc. are stored in `skill.meta.yaml` to save tokens. The indexer reads metadata without parsing markdown content.

---

## 3. SKILL.md Format

`SKILL.md` must contain YAML frontmatter followed by Markdown content.

```
---                          ← YAML frontmatter
name: skill-name             ← Required
description: What this       ← Required (1-1024 chars)
  skill does and when
  to use it.
---                          ← frontmatter end

## Instructions                  ← Markdown body
1. Step-by-step guidance
2. ...
```

**Note**: `SKILL.md` frontmatter only contains the core fields required by [Agent Skills](https://agentskills.io/specification): `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`. BaiZe-specific fields (`category`, `cognitive_phase`, `triggers`, i18n fields, etc.) go into `skill.meta.yaml`.

---

## 4. Frontmatter Fields

### 4.1 Required Fields

| Field | Constraints |
|-------|-------------|
| `name` | Max 64 chars. Lowercase `a-z`, `0-9`, `-` only. No leading/trailing hyphens. No consecutive hyphens. Must match parent directory name. |
| `description` | Max 1024 chars. Describe what the skill does and when to use it. Include keywords that help agents identify relevant tasks. |

**Valid names**: `pdf-processing`, `data-analysis`, `code-review`

**Invalid names**:
```
PDF-Processing   ← uppercase not allowed
-pdf             ← cannot start with hyphen
pdf--processing  ← consecutive hyphens not allowed
```

**Good description**:
```
"Extracts text and tables from PDF files, fills forms, and merges PDFs.
Use when working with PDF documents or when the user mentions PDFs,
forms, or document extraction."
```

**Poor description**:
```
"Helps with PDFs."
```

### 4.2 Optional Fields

| Field | Constraints |
|-------|-------------|
| `license` | License name or path to bundled license file. Keep it short. |
| `compatibility` | Max 500 chars. Environment requirements (e.g., product, packages, network access). Most skills do not need this. |
| `metadata` | Arbitrary key-value mapping (string keys to string values). Key names should be unique to avoid conflicts. |
| `allowed-tools` | Space-delimited list of pre-approved tools. (Experimental — support may vary between agent implementations.) |

---

## 5. skill.meta.yaml Format (BaiZe Metadata)

The `skill.meta.yaml` file stores BaiZe-specific metadata fields. It is read by the indexer/CLI and is **not** parsed by the LLM.

```yaml
# BaiZe Skill Metadata
# Read by indexer/CLI only — LLM does not read this file

# === Identity & Version ===
name: code-generate
version: "1.0.0"

# === i18n Fields ===
name_key: skills.code-generate.name
name_zh: 代码生成
name_en: code-generate
description_key: skills.code-generate.description
description_zh: "根据技术规范自动生成代码及对应测试用例。"
description_en: "Automatically generate code and corresponding tests based on technical specifications."

# === Classification & Cognitive Phase ===
category: code                            # code|quality|test|security|doc|infra|spec|project|tooling|internet|domain|process|loop|framework|system
cognitive_phase: executor                # observer|strategist|executor|critic

# === Layer & Origin ===
layer: system                             # system|user
origin: BaiZe                              # GSD|ECC|Superpowers|Ralph|Meta|BaiZe

# === MCP Configuration ===
mcp_server: null                          # MCP server identifier (if any)
mcp_tools: []                              # MCP tool list

# === Triggers & Capabilities ===
triggers:                                   # Trigger keyword list
  - "project-create"
  - "feature-generate"
  - "code-generation"

capabilities:                               # Capability list
  - "code-generation"
  - "test-generation"

commands: []                                # CLI dependencies

# === Optional Fields ===
compatibility: null
allowed_tools: []
metadata: {}
```

### 5.1 Category Values

| Value | Description |
|-------|-------------|
| `code` | Code generation, implementation |
| `quality` | Code quality, linting, review |
| `test` | Test generation, validation |
| `security` | Security scanning, vulnerability assessment |
| `doc` | Documentation writing |
| `infra` | Infrastructure, deployment, Docker, K8s |
| `spec` | Requirements, specifications |
| `project` | Project scaffolding, templates |
| `tooling` | Tool generation, build scripts |
| `internet` | Web scraping, browser automation, search |
| `domain` | Domain-specific (medical, finance, etc.) |
| `process` | Workflow, pipeline orchestration |
| `loop` | Iteration, feedback loops |
| `framework` | Framework-specific skills |
| `system` | System-level, meta skills |

### 5.2 Cognitive Phase Values

| Value | Description |
|-------|-------------|
| `observer` | Analyzing, researching, monitoring |
| `strategist` | Planning, designing, roadmapping |
| `executor` | Performing actions, generating code |
| `critic` | Reviewing, evaluating, providing feedback |

### 5.3 Backward Compatibility

If `skill.meta.yaml` does not exist, the indexer infers missing fields from `SKILL.md` frontmatter:
- `category` → inferred from `name` + `description` keywords
- `cognitive_phase` → inferred from `description` keywords
- `triggers` → inferred from `name` + `description` keywords
- `name_zh`, `description_zh` → empty (no Chinese content)

---

## 6. Body Content

The Markdown body after frontmatter contains skill instructions. **No format restrictions** — write whatever helps agents perform the task effectively.

**Recommended sections**:
- Step-by-step instructions
- Examples of inputs and outputs
- Common edge cases

---

## 7. Optional Directories

| Directory | Purpose |
|-----------|---------|
| `scripts/` | Executable code (Python, Bash, JavaScript, etc.). Should be self-contained, document dependencies, and handle errors gracefully. |
| `references/` | Additional documentation loaded on demand: `REFERENCE.md`, `FORMS.md`, domain-specific files. Keep files focused — agents load these on demand. |
| `assets/` | Static resources: templates, images, data files. |

---

## 8. Progressive Disclosure

Structure skills for efficient context use:

| Layer | Tokens | When Loaded |
|-------|--------|-------------|
| Metadata | ~100 | At startup for all skills |
| Instructions | <5000 | When skill is activated |
| Resources | As needed | Only when required |

> Keep `SKILL.md` under 500 lines. Move detailed reference material to separate files.

---

## 9. File References

Use relative paths from the skill root:

```markdown
See [the reference guide](references/REFERENCE.md) for details.

Run the extraction script:
scripts/extract.py
```

Keep file references **one level deep** from `SKILL.md`. Avoid deeply nested reference chains.

---

## 10. Validation

Use the `skills-ref` reference library to validate:

```bash
skills-ref validate ./my-skill
```

This checks that frontmatter is valid and follows all naming conventions.

---

## 11. Quick Reference

### SKILL.md Frontmatter Fields (LLM reads)

| Field | Required |
|-------|:--------:|
| `name` | **Yes** |
| `description` | **Yes** |
| `license` | No |
| `compatibility` | No |
| `metadata` | No |
| `allowed-tools` | No |

### skill.meta.yaml Fields (Indexer/CLI reads)

| Field | Description |
|-------|-------------|
| `name` | Skill name |
| `version` | Version string |
| `name_key` | i18n key for name |
| `name_zh` | Chinese name |
| `name_en` | English name |
| `description_key` | i18n key for description |
| `description_zh` | Chinese description |
| `description_en` | English description |
| `category` | Skill category |
| `cognitive_phase` | Cognitive phase |
| `layer` | system / user |
| `origin` | Origin source |
| `mcp_server` | MCP server identifier |
| `mcp_tools` | MCP tool list |
| `triggers` | Trigger keywords |
| `capabilities` | Capability list |
| `commands` | CLI dependencies |

### Directory Structure

```
skill-name/               # kebab-case
├── SKILL.md             # required: English content for LLM
├── SKILL.zh.md          # optional: Chinese content for LLM
├── skill.meta.yaml      # optional: BaiZe metadata for indexer
├── scripts/             # optional: executables
├── references/          # optional: on-demand docs
└── assets/              # optional: static resources
```

---

**Document Version**: 3.1.0
**Last Updated**: 2026-05-18
**Reference**: [Agent Skills Specification](https://agentskills.io/specification)