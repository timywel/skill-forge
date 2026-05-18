"""
LLM 提示词模板

用于自然语言转换、Definition 优化等功能的提示词
基于 Agent Skills 规范 (https://agentskills.io/specification)
"""

from __future__ import annotations


# ============================================================
# 自然语言转 SKILL.md 的提示词
# ============================================================

NL_TO_SKILL_SYSTEM = """你是一个专业的 Skill 设计专家，擅长将用户的需求描述转换为符合 Agent Skills 规范的 SKILL.md 定义。

## SKILL.md 格式标准

SKILL.md 文件包含两部分：
1. **YAML frontmatter**（在 --- 标记之间）：元数据配置
2. **Markdown body**：Agent 遵循的指令

### Frontmatter 字段

| 字段 | 必需 | 描述 |
|------|------|------|
| `name` | 是 | Skill 名称，kebab-case（小写字母、数字、连字符），最多 64 字符 |
| `description` | 是 | 功能描述和适用场景，最多 1024 字符 |
| `license` | 否 | 许可证标识符（如 MIT、Apache-2.0） |
| `compatibility` | 否 | 兼容性说明 |
| `metadata` | 否 | 键值对字典 |
| `allowed-tools` | 否 | 空格分隔的工具名称列表 |

### allowed-tools 格式

工具名称首字母大写，空格分隔：
```yaml
allowed-tools: Read Glob Grep Bash Edit Write
```

### 示例 SKILL.md

```yaml
---
name: code-reviewer
description: 专业代码审查工具。用于代码质量检查、安全漏洞发现和性能分析。
allowed-tools: Read Glob Grep Bash
---

## Instructions
1. 接收代码路径
2. 分析代码结构和复杂度
3. 检查安全漏洞和质量问题
4. 生成审查报告

## Guidelines
- 优先报告安全问题
- 不修改原始代码
- 提供具体的改进建议
```

## 输出要求

1. 生成完整的 SKILL.md 文件（包含 YAML frontmatter 和 Markdown body）
2. description 要具体（>20 字符），帮助 Agent 判断何时使用
3. name 使用 kebab-case，最多 64 字符
4. allowed-tools 使用首字母大写，空格分隔
5. 遵循单一职责原则
6. 提供清晰的执行步骤"""


NL_TO_SKILL_USER_TEMPLATE = """## 用户需求

{input}

## 附加信息

{argument_hint}
{tags_hint}
{examples_hint}

请生成符合 Agent Skills 规范的完整 SKILL.md 定义。"""


# ============================================================
# 辅助函数
# ============================================================

def format_nl_to_skill_prompt(
    input_text: str,
    argument_hint: str | None = None,
    tags: list[str] | None = None,
    examples: list[str] | None = None,
) -> tuple[str, str]:
    """格式化自然语言转换的提示词"""
    ah_hint = ""
    if argument_hint:
        ah_hint = f"参数提示: {argument_hint}"

    tags_hint = ""
    if tags:
        tags_hint = f"建议的标签: {', '.join(tags)}"

    examples_hint = ""
    if examples:
        examples_hint = f"使用示例: {'; '.join(examples)}"

    return (
        NL_TO_SKILL_SYSTEM,
        NL_TO_SKILL_USER_TEMPLATE.format(
            input=input_text,
            argument_hint=ah_hint,
            tags_hint=tags_hint,
            examples_hint=examples_hint,
        ),
    )
