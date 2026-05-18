"""
Skill 数据模型

基于 Agent Skills 规范 (https://agentskills.io/specification)

核心字段：
- name: 必需，kebab-case，最大 64 字符
- description: 必需，最大 1024 字符
- license: 可选，许可证
- compatibility: 可选，环境要求
- metadata: 可选，键值对映射
- allowed-tools: 可选，预批准工具（空格分隔）
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class Skill(BaseModel):
    """
    Skill 完整数据模型（SKILL.md 格式）

    SKILL.md 文件包含两部分：
    1. YAML frontmatter（在 --- 标记之间）
    2. Markdown 内容（agent 遵循的指令）

    示例 SKILL.md：
    ```markdown
    ---
    name: pdf-processor
    description: Extract text, tables, and forms from PDF files. Use when the user mentions PDFs, document extraction, or form filling.
    license: Apache-2.0
    compatibility: Requires Python 3.10+ and pdfplumber
    allowed-tools: Read Glob Bash(python *) Write
    ---

    ## Instructions

    1. Validate the input file
    2. Extract content using the extraction script
    3. Report findings
    ```
    """

    # ============================================================
    # Frontmatter 字段（Agent Skills 规范）
    # ============================================================

    # name: 必需，kebab-case，最大 64 字符
    name: str = Field(
        ...,
        description="Skill 名称。仅小写字母、数字和连字符（最多 64 个字符）"
    )

    # description: 必需，最大 1024 字符
    description: str = Field(
        ...,
        description="Skill 功能和何时使用。应包含有助于 agent 判断何时使用的关键词。"
    )

    # license: 可选
    license: Optional[str] = Field(
        default=None,
        description="许可证名称或捆绑许可证文件路径"
    )

    # compatibility: 可选
    compatibility: Optional[str] = Field(
        default=None,
        description="环境要求（如目标产品、系统包、网络访问）"
    )

    # metadata: 可选，键值对映射
    metadata: Dict[str, str] = Field(
        default_factory=dict,
        description="任意键值对映射"
    )

    # allowed-tools: 可选，空格分隔
    allowed_tools: List[str] = Field(
        default_factory=list,
        description="预批准工具的空格分隔列表"
    )

    # ============================================================
    # i18n 多语言字段（v3.1.0 新增，写入 skill.meta.yaml）
    # ============================================================

    # i18n key 字段（自动生成）
    name_key: Optional[str] = Field(default=None, exclude=True)
    name_zh: Optional[str] = Field(default=None, exclude=True)
    name_en: Optional[str] = Field(default=None, exclude=True)
    description_key: Optional[str] = Field(default=None, exclude=True)
    description_zh: Optional[str] = Field(default=None, exclude=True)
    description_en: Optional[str] = Field(default=None, exclude=True)

    # ============================================================
    # BaiZe 扩展字段（v3.1.0 新增，写入 skill.meta.yaml）
    # ============================================================

    category: Optional[str] = Field(default=None, exclude=True)
    cognitive_phase: Optional[str] = Field(default=None, exclude=True)
    layer: Optional[str] = Field(default="system", exclude=True)
    mcp_server: Optional[str] = Field(default=None, exclude=True)
    mcp_tools: Optional[List[str]] = Field(default=None, exclude=True)
    triggers: Optional[List[str]] = Field(default=None, exclude=True)
    capabilities: Optional[List[str]] = Field(default=None, exclude=True)
    commands: Optional[List[str]] = Field(default=None, exclude=True)
    origin: Optional[str] = Field(default="BaiZe", exclude=True)

    # ============================================================
    # 内部字段（不写入 frontmatter）
    # ============================================================

    # file_path: SKILL.md 文件路径
    file_path: Optional[str] = Field(default=None, exclude=True)

    # skill_dir: Skill 目录路径
    skill_dir: Optional[str] = Field(default=None, exclude=True)

    # markdown_body: Markdown 内容部分
    markdown_body: Optional[str] = Field(default=None, exclude=True)

    # ============================================================
    # 验证器
    # ============================================================

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """验证 name 格式：kebab-case，仅小写字母、数字和连字符"""
        if not v:
            raise ValueError("name 不能为空")

        # 全部小写
        v = v.lower()

        # 仅允许小写字母、数字、连字符
        if not re.match(r"^[a-z0-9][a-z0-9-]*$", v):
            raise ValueError(
                f"name '{v}' 必须为 kebab-case（小写字母、数字、连字符，首字符不能是连字符）"
            )

        # 不能有连续连字符
        if "--" in v:
            raise ValueError(f"name '{v}' 不能包含连续连字符")

        # 长度限制
        if len(v) > 64:
            raise ValueError(f"name '{v}' 超过最大长度 64 字符")

        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        """验证 description 格式"""
        if not v or not v.strip():
            raise ValueError("description 不能为空")
        if len(v) > 1024:
            raise ValueError(f"description 超过最大长度 1024 字符")
        return v.strip()

    @field_validator("license")
    @classmethod
    def validate_license(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        return v.strip()

    @field_validator("compatibility")
    @classmethod
    def validate_compatibility(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        if len(v) > 500:
            raise ValueError(f"compatibility 超过最大长度 500 字符")
        return v.strip()

    @field_validator("allowed_tools", mode="before")
    @classmethod
    def validate_allowed_tools(cls, v: Any) -> List[str]:
        """验证 allowed-tools 格式：空格分隔"""
        if v is None:
            return []
        if isinstance(v, str):
            # 空格分隔
            return [t.strip() for t in v.split() if t.strip()]
        if isinstance(v, list):
            return [str(t).strip() for t in v if str(t).strip()]
        raise ValueError(f"allowed-tools 必须是字符串或列表，当前类型: {type(v).__name__}")

    # ============================================================
    # 方法
    # ============================================================

    def to_frontmatter_dict(self) -> dict:
        """转换为 frontmatter 字典"""
        data: dict = {}

        data["name"] = self.name
        data["description"] = self.description

        if self.license:
            data["license"] = self.license
        if self.compatibility:
            data["compatibility"] = self.compatibility
        if self.metadata:
            data["metadata"] = self.metadata
        if self.allowed_tools:
            # 空格分隔（Agent Skills 规范）
            data["allowed-tools"] = " ".join(self.allowed_tools)

        return data

    model_config = {"extra": "forbid", "validate_assignment": True}

    def model_post_init(self, __context: Any) -> None:
        """初始化后自动填充 i18n key"""
        if not self.name_key:
            # 直接设置私有属性绕过 validate_assignment
            object.__setattr__(self, "name_key", f"skills.{self.name}.name")
        if not self.description_key:
            object.__setattr__(self, "description_key", f"skills.{self.name}.description")
        if not self.name_en:
            object.__setattr__(self, "name_en", self.name)

    def to_meta_yaml_dict(self) -> dict:
        """输出 skill.meta.yaml 字典（所有元数据字段）"""
        import yaml as _yaml  # noqa: F401 - 在模块顶层已导入
        result: dict = {
            "name": self.name,
            "version": "1.0.0",
            # i18n 多语言字段
            "name_key": self.name_key,
            "name_zh": self.name_zh,
            "name_en": self.name_en,
            "description_key": self.description_key,
            "description_zh": self.description_zh,
            "description_en": self.description_en,
            # 分类与认知阶段
            "category": self.category,
            "cognitive_phase": self.cognitive_phase,
            # 层与来源
            "layer": self.layer or "system",
            "origin": self.origin or "BaiZe",
            # MCP 配置
            "mcp_server": self.mcp_server,
            "mcp_tools": self.mcp_tools or [],
            # 触发与能力
            "triggers": self.triggers or [],
            "capabilities": self.capabilities or [],
            "commands": self.commands or [],
            # 可选字段
            "compatibility": self.compatibility,
            "allowed_tools": self.allowed_tools or [],
            "metadata": self.metadata or {},
        }
        # 移除 None 值（保留空列表，仅移除 None）
        return {k: v for k, v in result.items() if v is not None}

    def to_meta_yaml(self) -> str:
        """输出 skill.meta.yaml 字符串"""
        import yaml
        header = "# BaiZe Skill 元数据\n# 仅供索引器/CLI/API 使用，LLM 不读取此文件\n\n"
        return header + yaml.dump(
            self.to_meta_yaml_dict(),
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )


def parse_skill_md(content: str, file_path: Optional[str] = None) -> Skill:
    """
    解析 SKILL.md 内容为 Skill 对象

    Args:
        content: SKILL.md 文件内容（YAML frontmatter + Markdown body）
        file_path: 文件路径

    Returns:
        Skill 对象

    Raises:
        ValueError: 格式错误
    """
    import yaml

    if not content.startswith("---"):
        raise ValueError("SKILL.md 必须以 --- 开头")

    match = re.match(r"^---\n([\s\S]*?)\n---\n", content)
    if not match:
        raise ValueError("YAML frontmatter 未正确闭合（缺少 --- 结束标记）")

    frontmatter_text = match.group(1)
    markdown_body = content[match.end():].strip()

    try:
        fm = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError as e:
        raise ValueError(f"YAML frontmatter 解析失败: {e}")

    if not isinstance(fm, dict):
        raise ValueError("YAML frontmatter 根元素必须是字典")

    # 必需字段检查
    if "name" not in fm:
        raise ValueError("frontmatter 必须包含 name 字段")
    if "description" not in fm:
        raise ValueError("frontmatter 必须包含 description 字段")

    # 解析 allowed-tools（可能是字符串或列表）
    allowed_tools = fm.get("allowed-tools", [])
    if isinstance(allowed_tools, str):
        allowed_tools = [t.strip() for t in allowed_tools.split() if t.strip()]

    skill = Skill(
        name=fm["name"],
        description=fm["description"],
        license=fm.get("license"),
        compatibility=fm.get("compatibility"),
        metadata=fm.get("metadata", {}),
        allowed_tools=allowed_tools,
        markdown_body=markdown_body,
        file_path=file_path,
    )

    if file_path:
        skill.skill_dir = os.path.dirname(file_path)

    return skill


def skill_to_md(skill: Skill, include_frontmatter: bool = True) -> str:
    """
    将 Skill 对象序列化为 SKILL.md 格式

    Args:
        skill: Skill 对象
        include_frontmatter: 是否包含 YAML frontmatter

    Returns:
        SKILL.md 格式字符串
    """
    if not include_frontmatter:
        return skill.markdown_body or ""

    fm = skill.to_frontmatter_dict()
    import yaml

    fm_str = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    body = skill.markdown_body or ""

    return f"---\n{fm_str}---\n\n{body}"
