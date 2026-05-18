"""
Skill 转换器外观（v3.1.0 新增）

提供统一接口，生成三文件标准输出：
  SKILL.md        - 英文内容（LLM 读取）
  SKILL.zh.md     - 中文内容（LLM 读取）
  skill.meta.yaml - 元数据（索引器/CLI/API 读取）
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml

from ..models.skill import Skill, parse_skill_md, skill_to_md
from ..inference.category_inference import infer_category, infer_cognitive_phase, infer_triggers


@dataclass
class ConvertResult:
    """转换结果"""
    output_dir: str
    files: List[str] = field(default_factory=list)
    skill: Optional[Skill] = None
    errors: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


def convert_skill_file(
    input_path: str,
    output_dir: str,
    *,
    generate_zh: bool = True,
    generate_meta: bool = True,
    category: Optional[str] = None,
    cognitive_phase: Optional[str] = None,
    layer: str = "system",
    origin: str = "BaiZe",
) -> ConvertResult:
    """从 SKILL.md 文件生成标准三文件输出。

    Args:
        input_path: 输入 SKILL.md 路径
        output_dir: 输出目录
        generate_zh: 是否生成 SKILL.zh.md（默认 True）
        generate_meta: 是否生成 skill.meta.yaml（默认 True）
        category: 覆盖推断的 category
        cognitive_phase: 覆盖推断的 cognitive_phase
        layer: layer 字段值（默认 system）
        origin: origin 字段值（默认 BaiZe）

    Returns:
        ConvertResult 实例
    """
    result = ConvertResult(output_dir=output_dir)

    # 读取并解析 SKILL.md
    try:
        content = Path(input_path).read_text(encoding="utf-8")
        skill = parse_skill_md(content, file_path=input_path)
    except Exception as exc:
        result.errors.append(f"解析失败: {exc}")
        return result

    # 自动推断缺失字段
    if not skill.category and not category:
        object.__setattr__(skill, "category", infer_category(skill.name, skill.description))
    elif category:
        object.__setattr__(skill, "category", category)

    if not skill.cognitive_phase and not cognitive_phase:
        object.__setattr__(skill, "cognitive_phase", infer_cognitive_phase(skill.description))
    elif cognitive_phase:
        object.__setattr__(skill, "cognitive_phase", cognitive_phase)

    if not skill.triggers:
        object.__setattr__(skill, "triggers", infer_triggers(skill.name, skill.description))

    object.__setattr__(skill, "layer", layer)
    object.__setattr__(skill, "origin", origin)

    # 填充 description_en（供 meta.yaml 使用）
    if not skill.description_en:
        object.__setattr__(skill, "description_en", skill.description)

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 生成 SKILL.md（英文内容）
    skill_md_path = os.path.join(output_dir, "SKILL.md")
    _write(skill_md_path, skill_to_md(skill))
    result.files.append("SKILL.md")

    # 生成 SKILL.zh.md（中文内容，fallback 使用英文）
    if generate_zh:
        skill_zh_md_path = os.path.join(output_dir, "SKILL.zh.md")
        zh_content = _build_skill_zh_md(skill)
        _write(skill_zh_md_path, zh_content)
        result.files.append("SKILL.zh.md")

    # 生成 skill.meta.yaml（元数据）
    if generate_meta:
        meta_path = os.path.join(output_dir, "skill.meta.yaml")
        _write(meta_path, skill.to_meta_yaml())
        result.files.append("skill.meta.yaml")

    result.skill = skill
    return result


def _build_skill_zh_md(skill: Skill) -> str:
    """构建 SKILL.zh.md 内容（中文内容）。

    如未提供 description_zh，fallback 为英文 description。
    LLM 翻译可选（后续由翻译流程填充）。
    """
    fm: dict = {
        "name": skill.name,
        "description": skill.description_zh or skill.description,
    }
    if skill.license:
        fm["license"] = skill.license

    fm_str = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    body = skill.markdown_body or ""
    return f"---\n{fm_str}---\n\n{body}"


def _write(path: str, content: str) -> None:
    """写入文件"""
    Path(path).write_text(content, encoding="utf-8")
