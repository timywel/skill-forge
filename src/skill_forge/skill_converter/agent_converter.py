"""
Agent 转 Skill 转化器

将 Claude Code Agent (.agent.md) 转换为标准 SKILL.md

支持两种 Agent 格式：
1. Claude Code Agent 格式（## Identity, ## Instructions, ## Guidelines）
2. Design Agent 格式（带 emoji 的标题如 ## 🧠 Your Identity & Memory）
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BaseConverter
from ..llm.slots import LLMSlotEx


class AgentConverter(BaseConverter):
    """
    Agent 转 Skill 转化器

    将 .agent.md 文件转换为 SKILL.md 格式

    用法：
    ```python
    converter = AgentConverter()
    result = converter.convert(".claude/agents/my-agent/agent.md")
    # 返回 SKILL.md 格式字符串
    print(result["skill_md"])
    ```
    """

    def convert(
        self,
        source: str,
        llm: Optional[LLMSlotEx] = None,
        name: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        将 Agent 文件转换为 SKILL.md

        Args:
            source: Agent 文件路径
            llm: LLM 能力（可选，用于生成描述）
            name: 可选的 skill 名称
            **kwargs: 其他参数

        Returns:
            转化后的 skill 数据（包含 skill_md 字段为 SKILL.md 格式字符串）
        """
        ctx = self._create_context("agent", source, llm)

        # 读取 Agent 文件
        content = self._read_agent_file(source)

        # 解析 Agent 内容
        agent_data = self._parse_agent_content(content)

        # 转换
        skill_data = self._convert_to_skill(agent_data, name)

        # 验证和补全
        skill_data = self._normalize_data(skill_data)

        # 转换为 SKILL.md 格式字符串
        skill_md = self._skill_to_md(skill_data)
        skill_data["skill_md"] = skill_md

        return skill_data

    def _read_agent_file(self, path: str) -> str:
        """读取 Agent 文件内容"""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Agent 文件不存在: {path}")

        return p.read_text(encoding="utf-8")

    def _parse_agent_content(self, content: str) -> Dict[str, Any]:
        """
        解析 Agent 文件内容

        支持两种格式：
        1. Claude Code Agent 格式
        2. Design Agent 格式（带 emoji）

        Args:
            content: Agent 文件文本

        Returns:
            解析后的数据
        """
        data: Dict[str, Any] = {}

        # 移除 frontmatter（如果有）
        if content.startswith("---"):
            match = re.match(r"^---\n([\s\S]*?)\n---\n", content)
            if match:
                # 简单解析 frontmatter
                frontmatter = match.group(1)
                for line in frontmatter.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        key = key.strip().lower()
                        value = value.strip()
                        if key == "name":
                            data["agent_name"] = self._normalize_name(value)
                        elif key == "description":
                            data["description"] = value
                        elif key == "vibe":
                            data["vibe"] = value
                # 移除 frontmatter，保留正文
                content = content[match.end():]

        # 检测格式类型
        is_design_format = bool(re.search(
            r"## \S.*Your (Identity|Instructions|Guidelines|Tools|Core Mission|Critical Rules|Brand Strategy Deliverables)",
            content
        ))

        if is_design_format:
            data = self._parse_design_format(content, data)
        else:
            data = self._parse_standard_format(content, data)

        # 提取名称（如果还没有）
        if not data.get("agent_name"):
            name_match = re.search(r"^#\s*([A-Za-z][A-Za-z0-9 -]+?)(?:\s+Agent|\s*$)", content, re.MULTILINE)
            if name_match:
                data["agent_name"] = self._normalize_name(name_match.group(1))

        # 提取描述（如果还没有）
        if not data.get("description"):
            first_para = re.search(r"(?:You are|I'm|I am)\s+\*\*([^*]+)\*\*[,.，：:]\s*([^\n]+)", content)
            if first_para:
                data["description"] = f"{first_para.group(1)} - {first_para.group(2)}".strip()[:200]

        # 迁移变量到 markdown_body
        if not data.get("markdown_body"):
            data["markdown_body"] = self._build_markdown_body(data)

        return data

    def _parse_design_format(self, content: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析 Design Agent 格式"""
        # 提取主要功能块
        block_patterns = [
            (r"## 🧠 Your Identity & Memory\n([\s\S]*?)(?=## |\n#|\Z)", "identity"),
            (r"## 🎯 Your Core Mission\n([\s\S]*?)(?=## |\n#|\Z)", "mission"),
            (r"## 🚨 Critical Rules.*?\n([\s\S]*?)(?=## |\n#|\Z)", "rules"),
            (r"## 📋 Your.*?Deliverables\n([\s\S]*?)(?=## |\n#|\Z)", "deliverables"),
        ]

        for pattern, block_name in block_patterns:
            match = re.search(pattern, content)
            if match:
                data[block_name] = match.group(1).strip()

        # 提取 Role
        for pattern in [
            r"\*\*Role\*\*:\s*(.+?)(?:\n|$)",
            r"Role[:：]\s*(.+?)(?:\n|$)",
        ]:
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                data["role"] = match.group(1).strip()
                break

        # 提取 Personality
        personality_match = re.search(r"\*\*Personality\*\*:\s*(.+?)(?:\n|$)", content, re.MULTILINE)
        if personality_match:
            data["personality"] = personality_match.group(1).strip()

        return data

    def _parse_standard_format(self, content: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析标准 Claude Code Agent 格式"""
        # 提取 Identity 块
        identity_match = re.search(
            r"## Identity\s*\n([\s\S]*?)(?=## |\n#|\Z)",
            content,
            re.IGNORECASE
        )
        if identity_match:
            data["identity"] = identity_match.group(1).strip()
            # 提取 Role
            role_match = re.search(r"Role[:：]\s*(.+?)(?:\n|$)", data["identity"], re.IGNORECASE)
            if role_match:
                data["role"] = role_match.group(1).strip()

        # 提取 Instructions 块
        instructions_match = re.search(
            r"## Instructions\s*\n([\s\S]*?)(?=## |\n#|\Z)",
            content,
            re.IGNORECASE
        )
        if instructions_match:
            data["instructions"] = instructions_match.group(1).strip()

        # 提取 Guidelines 块
        guidelines_match = re.search(
            r"## Guidelines\s*\n([\s\S]*?)(?=## |\n#|\Z)",
            content,
            re.IGNORECASE
        )
        if guidelines_match:
            data["guidelines"] = guidelines_match.group(1).strip()

        # 提取 Tools 块
        tools_match = re.search(
            r"## Tools\s*\n([\s\S]*?)(?=## |\n#|\Z)",
            content,
            re.IGNORECASE
        )
        if tools_match:
            data["tools_raw"] = tools_match.group(1)
            data["tools"] = self._parse_tools(tools_match.group(1))

        return data

    def _parse_tools(self, tools_text: str) -> List[str]:
        """解析工具列表"""
        tools = []
        known_tools = {
            "Read", "Glob", "Grep", "Bash", "Edit", "Write",
            "WebFetch", "WebSearch", "NotebookEdit",
            "TaskCreate", "TaskGet", "TaskList", "TaskUpdate",
            "ExitPlanMode", "Agent", "TaskOutput",
            "AskUserQuestion",
        }

        for line in tools_text.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # 处理列表项
            if line.startswith("-"):
                line = line.lstrip("-").strip()

            # 提取工具名称
            for tool in known_tools:
                if tool.lower() in line.lower():
                    if tool not in tools:
                        tools.append(tool)
                    break

        return tools if tools else ["Read", "Glob", "Grep"]

    def _convert_to_skill(
        self,
        agent_data: Dict[str, Any],
        override_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """将 Agent 数据转换为 Skill 格式"""
        # 确定名称
        name = override_name or agent_data.get("agent_name", "converted-agent")
        name = self._normalize_name(name)

        # 生成 description
        description = (
            agent_data.get("description") or
            agent_data.get("role") or
            f"由 {name} Agent 转换的 Skill"
        )
        if len(description) > 200:
            description = description[:197] + "..."

        # 生成 tags
        tags = []
        if agent_data.get("personality"):
            tags.append("personality")
        if "design" in name.lower():
            tags.extend(["design", "creative"])
        if "ux" in name.lower() or "ui" in name.lower():
            tags.extend(["ux", "ui", "design"])

        # 构建 markdown body
        markdown_body = self._build_markdown_body(agent_data)

        skill = {
            "name": name,
            "description": description,
            "markdown_body": markdown_body,
            "allowed_tools": agent_data.get("tools", ["Read", "Glob", "Grep"]),
            "user_invocable": True,
            "tags": tags,
        }

        return skill

    def _build_markdown_body(self, agent_data: Dict[str, Any]) -> str:
        """构建 markdown body"""
        lines: List[str] = []

        # Identity
        if agent_data.get("role"):
            lines.append("## Identity")
            lines.append(f"- Role: {agent_data['role']}")
            if agent_data.get("personality"):
                lines.append(f"- Personality: {agent_data['personality']}")
            lines.append("")

        # Mission/Instructions
        if agent_data.get("mission") or agent_data.get("instructions"):
            lines.append("## Instructions")
            content = agent_data.get("mission") or agent_data.get("instructions", "")
            for line in content.split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    lines.append(line)
            lines.append("")

        # Rules/Guidelines
        if agent_data.get("rules") or agent_data.get("guidelines"):
            lines.append("## Guidelines")
            content = agent_data.get("rules") or agent_data.get("guidelines", "")
            for line in content.split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    lines.append(line)
            lines.append("")

        # Tools
        if agent_data.get("tools"):
            lines.append("## Tools")
            for tool in agent_data["tools"]:
                lines.append(f"- {tool}")
            lines.append("")

        result = "\n".join(lines)

        # 如果 body 仍然为空，使用默认值
        if not result.strip():
            result = f"""## Identity
- Role: {agent_data.get('role', 'Agent 转换的 Skill')}

## Instructions
1. 执行任务
2. 返回结果
"""

        return result

    def _normalize_name(self, name: str) -> str:
        """将名称标准化为 kebab-case"""
        if not name:
            return "converted-agent"

        # 转小写
        name = name.lower()

        # 替换空格、下划线、特殊字符为连字符
        name = re.sub(r"[\s_]+", "-", name)
        name = re.sub(r"[^a-z0-9-]", "-", name)

        # 移除连续连字符
        name = re.sub(r"-+", "-", name)

        # 移除首尾连字符
        name = name.strip("-")

        return name or "converted-agent"

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

        if "user_invocable" not in data:
            data["user_invocable"] = True

        return data
