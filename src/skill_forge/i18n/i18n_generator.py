"""
Skill i18n key 生成器（v3.1.0 新增）

功能：
- 从 Skill 对象列表生成 zh.json / en.json 中的 i18n 条目
- 只增不覆盖策略（write-only-if-missing）
- 按 key 前缀排序后写入

i18n key 格式：
  skills.{name}.name
  skills.{name}.description
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from ..models.skill import Skill


class I18nStats:
    """i18n 生成统计"""

    def __init__(self) -> None:
        self.skills_processed: int = 0
        self.name_keys_added: int = 0
        self.desc_keys_added: int = 0
        self.skipped: int = 0

    @property
    def total_added(self) -> int:
        return self.name_keys_added + self.desc_keys_added

    def __repr__(self) -> str:
        return (
            f"I18nStats(skills={self.skills_processed}, "
            f"name_keys_added={self.name_keys_added}, "
            f"desc_keys_added={self.desc_keys_added}, "
            f"skipped={self.skipped})"
        )


class I18nGenerator:
    """Skill i18n key 生成器

    使用方式（完整流程）：
        gen = I18nGenerator(zh_path, en_path)
        gen.load()
        stats = gen.process_skills(skills)
        gen.save()

    或简化版：
        gen = I18nGenerator(zh_path, en_path)
        stats = gen.generate(skills)
    """

    def __init__(self, zh_path: str, en_path: str) -> None:
        self.zh_path = Path(zh_path)
        self.en_path = Path(en_path)
        self.zh_data: Dict[str, str] = {}
        self.en_data: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # 公共方法
    # ------------------------------------------------------------------

    def load(self) -> None:
        """加载现有的 i18n JSON 文件"""
        if self.zh_path.exists():
            with open(self.zh_path, encoding="utf-8") as f:
                self.zh_data = json.load(f)
        if self.en_path.exists():
            with open(self.en_path, encoding="utf-8") as f:
                self.en_data = json.load(f)

    def add_skill(self, skill: "Skill") -> Dict[str, bool]:
        """为单个 skill 添加 i18n 条目（只增不覆盖）。

        Returns:
            {'name_key': bool, 'description_key': bool} 表示是否新增
        """
        result: Dict[str, bool] = {"name_key": False, "description_key": False}

        name_key = skill.name_key or f"skills.{skill.name}.name"
        desc_key = skill.description_key or f"skills.{skill.name}.description"

        # name_key: 只在 zh.json 中不存在时添加
        if name_key not in self.zh_data:
            zh_name = getattr(skill, "name_zh", None) or getattr(skill, "name_en", None) or skill.name
            en_name = getattr(skill, "name_en", None) or skill.name
            self.zh_data[name_key] = zh_name
            self.en_data[name_key] = en_name
            result["name_key"] = True

        # description_key
        if desc_key not in self.zh_data:
            zh_desc = (
                getattr(skill, "description_zh", None)
                or getattr(skill, "description_en", None)
                or skill.description
            )
            en_desc = getattr(skill, "description_en", None) or skill.description
            self.zh_data[desc_key] = zh_desc
            self.en_data[desc_key] = en_desc
            result["description_key"] = True

        return result

    def process_skills(self, skills: List["Skill"]) -> I18nStats:
        """批量处理 skill 列表，返回统计结果"""
        stats = I18nStats()
        for skill in skills:
            result = self.add_skill(skill)
            if result["name_key"]:
                stats.name_keys_added += 1
            else:
                stats.skipped += 1
            if result["description_key"]:
                stats.desc_keys_added += 1
            else:
                stats.skipped += 1
            stats.skills_processed += 1
        return stats

    def save(self) -> None:
        """保存 i18n 文件（按 key 排序写入）"""
        self.zh_data = dict(sorted(self.zh_data.items()))
        self.en_data = dict(sorted(self.en_data.items()))

        self.zh_path.parent.mkdir(parents=True, exist_ok=True)
        self.en_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.zh_path, "w", encoding="utf-8") as f:
            json.dump(self.zh_data, f, ensure_ascii=False, indent=2)
            f.write("\n")

        with open(self.en_path, "w", encoding="utf-8") as f:
            json.dump(self.en_data, f, ensure_ascii=False, indent=2)
            f.write("\n")

    def generate(self, skills: List["Skill"]) -> I18nStats:
        """完整流程：加载 → 处理 → 保存"""
        self.load()
        stats = self.process_skills(skills)
        self.save()
        return stats
