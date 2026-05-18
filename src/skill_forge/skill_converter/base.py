"""
转化器基类

基于 Agent Skills 规范 (https://agentskills.io/specification)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from ..llm.slots import ConversionContext, LLMSlotEx


class BaseConverter(ABC):
    """转化器基类"""

    def __init__(self):
        self.context: Optional[ConversionContext] = None

    @abstractmethod
    def convert(
        self,
        source: str,
        llm: Optional[LLMSlotEx] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """转化 source 为 SKILL.md 格式"""
        ...

    def _create_context(
        self,
        source_type: str,
        source: str,
        llm: Optional[LLMSlotEx] = None,
        **kwargs,
    ) -> ConversionContext:
        ctx = ConversionContext(
            source_type=source_type,
            raw_input=source,
            llm=llm,
            options=kwargs,
        )
        if Path(source).exists():
            ctx.source_path = str(Path(source).absolute())
        self.context = ctx
        return ctx

    def _skill_to_md(self, skill: Dict[str, Any]) -> str:
        """将 skill 数据转换为 SKILL.md 格式字符串"""
        fm: Dict[str, Any] = {}

        fm["name"] = skill.get("name", "")
        fm["description"] = skill.get("description", "")

        if skill.get("license"):
            fm["license"] = skill["license"]
        if skill.get("compatibility"):
            fm["compatibility"] = skill["compatibility"]
        if skill.get("metadata"):
            fm["metadata"] = skill["metadata"]
        if skill.get("allowed_tools"):
            fm["allowed-tools"] = " ".join(skill["allowed_tools"])

        lines = []
        lines.append("---")
        fm_str = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
        lines.append(fm_str.strip())
        lines.append("---")
        lines.append("")

        body = skill.get("markdown_body", "")
        if body:
            lines.append(body)

        return "\n".join(lines)

    def _save_skill_md(self, data: Dict[str, Any], path: str) -> None:
        """保存 SKILL.md"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        content = self._skill_to_md(data)
        Path(path).write_text(content, encoding="utf-8")
