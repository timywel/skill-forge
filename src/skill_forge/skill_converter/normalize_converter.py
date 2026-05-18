"""
标准化转化器

基于 Agent Skills 规范 (https://agentskills.io/specification)

支持的格式：
1. SKILL.md frontmatter 格式（自动识别）
2. 纯 Markdown 格式
3. Agent .agent.md 格式
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Optional

from .base import BaseConverter


class NormalizeConverter(BaseConverter):
    """标准化转化器"""

    def convert(
        self,
        source: str,
        **kwargs,
    ) -> Dict[str, Any]:
        ctx = self._create_context("normalize", source, **kwargs)

        if Path(source).exists():
            content = Path(source).read_text(encoding="utf-8")
            ctx.source_path = str(Path(source).absolute())
        else:
            content = source

        format_type = self._detect_format(content)

        if format_type == "skill_md":
            data = self._convert_skill_md(content)
        elif format_type == "markdown":
            data = self._convert_markdown(content)
        elif format_type == "agent_md":
            data = self._convert_agent_md(content)
        else:
            data = self._convert_markdown(content)

        return self._normalize_data(data)

    def _detect_format(self, content: str) -> str:
        content = content.strip()

        # SKILL.md frontmatter 格式
        if content.startswith("---"):
            match = re.match(r"^---\n([\s\S]*?)\n---\n", content)
            if match:
                after_frontmatter = content[match.end():].strip()
                if after_frontmatter and (after_frontmatter.startswith("#") or after_frontmatter.startswith("##")):
                    return "skill_md"

        # Agent .agent.md 格式
        if re.search(r"## Identity", content, re.IGNORECASE):
            return "agent_md"

        # 纯 Markdown
        if content.startswith("#") or content.startswith("##"):
            return "markdown"

        return "markdown"

    def _convert_skill_md(self, content: str) -> Dict[str, Any]:
        """转换 SKILL.md 格式"""
        import yaml

        match = re.match(r"^---\n([\s\S]*?)\n---\n", content)
        if not match:
            return {}

        frontmatter_text = match.group(1)
        markdown_body = content[match.end():].strip()

        try:
            fm = yaml.safe_load(frontmatter_text) or {}
        except yaml.YAMLError:
            return {}

        if not isinstance(fm, dict):
            return {}

        # 解析 allowed-tools（空格分隔或列表）
        allowed_tools = fm.get("allowed-tools", [])
        if isinstance(allowed_tools, str):
            allowed_tools = [t.strip() for t in allowed_tools.split() if t.strip()]
        elif not isinstance(allowed_tools, list):
            allowed_tools = []

        return {
            "name": fm.get("name", ""),
            "description": fm.get("description", ""),
            "license": fm.get("license"),
            "compatibility": fm.get("compatibility"),
            "metadata": fm.get("metadata", {}),
            "allowed_tools": allowed_tools,
            "markdown_body": markdown_body,
        }

    def _convert_markdown(self, content: str) -> Dict[str, Any]:
        """转换纯 Markdown 格式"""
        name = "unknown-skill"
        name_match = re.search(r"^#\s*([a-z][a-z0-9-]+)", content, re.MULTILINE)
        if name_match:
            name = name_match.group(1)

        desc = ""
        first_para = re.search(r"^#{1,2}\s+[^\n]+\n*([^\n#]+)", content, re.MULTILINE)
        if first_para:
            desc = first_para.group(1).strip()[:200]

        return {
            "name": name,
            "description": desc,
            "markdown_body": content,
        }

    def _convert_agent_md(self, content: str) -> Dict[str, Any]:
        """转换 Agent .agent.md 格式"""
        if content.startswith("---"):
            match = re.match(r"^---\n([\s\S]*?)\n---\n", content)
            if match:
                content = content[match.end():].strip()

        name = "converted-agent"
        name_match = re.search(r"^#\s*([A-Za-z][A-Za-z0-9 -]+?)(?:\s+Agent|\s*$)", content, re.MULTILINE)
        if name_match:
            name = self._normalize_name(name_match.group(1))

        desc = ""
        role_match = re.search(r"Role[:：]\s*(.+?)(?:\n|$)", content, re.IGNORECASE)
        if role_match:
            desc = role_match.group(1).strip()[:200]

        body = content
        body = re.sub(r"^#.*$\n?", "", body, flags=re.MULTILINE)
        body = re.sub(r"^##\s+", "## ", body, flags=re.MULTILINE)
        body = re.sub(r"\n{3,}", "\n\n", body).strip()

        return {
            "name": name,
            "description": desc or "由 Agent 转换的 Skill",
            "markdown_body": body,
            "allowed_tools": ["Read", "Glob", "Grep"],
        }

    def _normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """规范化数据"""
        if not data.get("name"):
            data["name"] = "unknown-skill"
        else:
            data["name"] = self._normalize_name(data["name"])

        if not data.get("description"):
            data["description"] = ""
        if not data.get("markdown_body"):
            data["markdown_body"] = ""
        if not data.get("allowed_tools"):
            data["allowed_tools"] = []

        return data

    def _normalize_name(self, name: str) -> str:
        if not name:
            return "unknown-skill"
        name = name.lower()
        name = re.sub(r"[\s_]+", "-", name)
        name = re.sub(r"[^a-z0-9-]", "", name)
        name = re.sub(r"-+", "-", name)
        name = name.strip("-")
        return name or "unknown-skill"
