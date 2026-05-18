"""
自然语言转 Skill 转化器

使用 LLM 将自然语言描述转换为标准 SKILL.md
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .base import BaseConverter
from ..llm.slots import LLMSlotEx
from ..llm.prompts import format_nl_to_skill_prompt, NL_TO_SKILL_SYSTEM


class NLConverter(BaseConverter):
    """
    自然语言转 Skill 转化器

    将用户的自然语言需求转换为标准 SKILL.md 格式

    需要 LLM 能力支持

    用法：
    ```python
    converter = NLConverter()
    result = converter.convert(
        "创建一个代码审查技能，可以检查代码质量和安全问题",
        llm=my_llm_function
    )
    # 返回 SKILL.md 格式字符串
    print(result["skill_md"])
    ```
    """

    def convert(
        self,
        source: str,
        llm: Optional[LLMSlotEx] = None,
        argument_hint: Optional[str] = None,
        tags: Optional[List[str]] = None,
        examples: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        将自然语言描述转换为 SKILL.md

        Args:
            source: 自然语言描述
            llm: LLM 能力（必需）
            argument_hint: 参数提示，如 "[issue-number]" 或 "[filename]"
            tags: 建议的标签
            examples: 使用示例
            **kwargs: 其他参数

        Returns:
            转化后的 skill 数据（包含 skill_md 字段为 SKILL.md 格式字符串）

        Raises:
            ValueError: 如果缺少 LLM 能力
        """
        ctx = self._create_context("nl", source, llm, tags=tags, examples=examples)

        if not llm:
            raise ValueError(
                "NLConverter 需要 LLM 能力。"
                "请通过 llm 参数提供 LLM 实现。"
            )

        # 准备提示词
        system, user = format_nl_to_skill_prompt(
            input_text=source,
            argument_hint=argument_hint,
            tags=tags,
            examples=examples,
        )

        # 调用 LLM
        skill_md_text = llm.complete(system, user)

        # 解析 LLM 返回的 SKILL.md
        data = self._parse_skill_md_text(skill_md_text)

        # 验证结果
        if not self._validate_result(data):
            ctx.add_warning("LLM 返回的内容可能不是有效的 SKILL.md")
            # 尝试从内容中提取 SKILL.md
            data = self._extract_skill_md(skill_md_text)

        # 转换为 SKILL.md 格式字符串
        skill_md = self._skill_to_md(data)
        data["skill_md"] = skill_md

        return data

    def _parse_skill_md_text(self, text: str) -> Dict[str, Any]:
        """
        解析 LLM 返回的 SKILL.md 文本

        Args:
            text: LLM 返回的文本

        Returns:
            解析后的数据
        """
        # 尝试从 markdown 代码块中提取 SKILL.md
        text = self._extract_skill_md(text)

        if not text.strip():
            return {}

        # 提取 frontmatter
        match = re.match(r"^---\n([\s\S]*?)\n---\n", text)
        if not match:
            # 无 frontmatter，整个文本作为 markdown body
            return {"markdown_body": text.strip()}

        frontmatter_text = match.group(1)
        markdown_body = text[match.end():].strip()

        # 解析 frontmatter
        try:
            import yaml
            fm = yaml.safe_load(frontmatter_text) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"无法解析 LLM 返回的 YAML frontmatter: {e}")

        # 构建数据
        data: Dict[str, Any] = {}

        if isinstance(fm, dict):
            data["name"] = fm.get("name", "")
            data["description"] = fm.get("description", "")
            data["license"] = fm.get("license")
            data["compatibility"] = fm.get("compatibility")
            data["metadata"] = fm.get("metadata", {})

            # 解析 allowed-tools（空格分隔或列表）
            allowed_tools = fm.get("allowed-tools", [])
            if isinstance(allowed_tools, str):
                allowed_tools = [t.strip() for t in allowed_tools.split() if t.strip()]
            elif not isinstance(allowed_tools, list):
                allowed_tools = []
            data["allowed_tools"] = allowed_tools

        data["markdown_body"] = markdown_body

        return data

    def _extract_skill_md(self, text: str) -> str:
        """
        从文本中提取 SKILL.md 内容

        Args:
            text: 原始文本

        Returns:
            SKILL.md 内容
        """
        # 尝试从 ```markdown ... ``` 代码块中提取
        patterns = [
            r"```markdown\s*([\s\S]*?)\s*```",
            r"```yaml\s*([\s\S]*?)\s*```",
            r"```md\s*([\s\S]*?)\s*```",
            r"```\s*([\s\S]*?)\s*```",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                content = match.group(1).strip()
                # 验证提取的内容看起来像 SKILL.md
                if "---" in content or content.startswith("#"):
                    return content

        # 如果没有代码块，返回原始文本（可能是直接的 SKILL.md）
        return text.strip()
