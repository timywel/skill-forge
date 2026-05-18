# SKILL Specification

> **Version**: 3.0.0
> **Date**: 2026-04-02
> **Reference**: [Agent Skills Specification](https://agentskills.io/specification)

---

## 1. Overview

A **Skill** is a reusable unit that extends an AI agent's capabilities. It consists of structured metadata and instructions that tell the agent what it can do and how to do it.

---

## 2. Directory Structure

A skill is a **directory** containing at minimum a `SKILL.md` file:

```
skill-name/
├── SKILL.md          # Required: YAML frontmatter + Markdown instructions
├── scripts/          # Optional: executable code
├── references/       # Optional: additional documentation
├── assets/           # Optional: templates, data, images
└── ...
```

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

## 5. Body Content

The Markdown body after frontmatter contains skill instructions. **No format restrictions** — write whatever helps agents perform the task effectively.

**Recommended sections**:
- Step-by-step instructions
- Examples of inputs and outputs
- Common edge cases

---

## 6. Optional Directories

| Directory | Purpose |
|-----------|---------|
| `scripts/` | Executable code (Python, Bash, JavaScript, etc.). Should be self-contained, document dependencies, and handle errors gracefully. |
| `references/` | Additional documentation loaded on demand: `REFERENCE.md`, `FORMS.md`, domain-specific files. Keep files focused — agents load these on demand. |
| `assets/` | Static resources: templates, images, data files. |

---

## 7. Progressive Disclosure

Structure skills for efficient context use:

| Layer | Tokens | When Loaded |
|-------|--------|-------------|
| Metadata | ~100 | At startup for all skills |
| Instructions | <5000 | When skill is activated |
| Resources | As needed | Only when required |

> Keep `SKILL.md` under 500 lines. Move detailed reference material to separate files.

---

## 8. File References

Use relative paths from the skill root:

```markdown
See [the reference guide](references/REFERENCE.md) for details.

Run the extraction script:
scripts/extract.py
```

Keep file references **one level deep** from `SKILL.md`. Avoid deeply nested reference chains.

---

## 9. Validation

Use the `skills-ref` reference library to validate:

```bash
skills-ref validate ./my-skill
```

This checks that frontmatter is valid and follows all naming conventions.

---

## 10. Quick Reference

### Frontmatter Fields

| Field | Required |
|-------|:--------:|
| `name` | **Yes** |
| `description` | **Yes** |
| `license` | No |
| `compatibility` | No |
| `metadata` | No |
| `allowed-tools` | No |

### Directory Structure

```
skill-name/               # kebab-case
├── SKILL.md             # required entry point
├── scripts/             # optional: executables
├── references/          # optional: on-demand docs
└── assets/              # optional: static resources
```

---

**Document Version**: 3.0.0
**Last Updated**: 2026-04-02
**Reference**: [Agent Skills Specification](https://agentskills.io/specification)
