"""
tests/unit/test_multilang_generation.py
SKILL.md + SKILL.zh.md 双语言生成验证
"""

from __future__ import annotations
import os
import tempfile
import pytest
from skill_forge.skill_converter.converter import convert_skill_file, ConvertResult


SAMPLE_SKILL_MD = """\
---
name: code-generate
description: Automatically generate code and corresponding tests based on technical specifications.
license: Apache-2.0
---

## Instructions

1. Read technical specifications
2. Generate code template
3. Generate corresponding test cases
"""


@pytest.fixture
def skill_file(tmp_path) -> str:
    """创建临时 SKILL.md 文件"""
    p = tmp_path / "SKILL.md"
    p.write_text(SAMPLE_SKILL_MD, encoding="utf-8")
    return str(p)


@pytest.fixture
def output_dir(tmp_path) -> str:
    """创建输出目录"""
    d = tmp_path / "output"
    d.mkdir()
    return str(d)


class TestConvertSkillFile:
    """测试 convert_skill_file() 三文件生成"""

    def test_generates_all_three_files(self, skill_file, output_dir):
        """默认应生成 SKILL.md + SKILL.zh.md + skill.meta.yaml"""
        result = convert_skill_file(skill_file, output_dir)

        assert result.success, f"错误: {result.errors}"
        assert "SKILL.md" in result.files
        assert "SKILL.zh.md" in result.files
        assert "skill.meta.yaml" in result.files

        assert os.path.exists(os.path.join(output_dir, "SKILL.md"))
        assert os.path.exists(os.path.join(output_dir, "SKILL.zh.md"))
        assert os.path.exists(os.path.join(output_dir, "skill.meta.yaml"))

    def test_skill_md_has_correct_frontmatter(self, skill_file, output_dir):
        """SKILL.md 应保留原始 frontmatter"""
        result = convert_skill_file(skill_file, output_dir)
        assert result.success

        content = open(os.path.join(output_dir, "SKILL.md"), encoding="utf-8").read()
        assert "name: code-generate" in content
        assert "Automatically generate code" in content
        assert "Apache-2.0" in content

    def test_skill_zh_md_generated(self, skill_file, output_dir):
        """SKILL.zh.md 应包含英文 name 和 description"""
        result = convert_skill_file(skill_file, output_dir)
        assert result.success

        content = open(os.path.join(output_dir, "SKILL.zh.md"), encoding="utf-8").read()
        assert "name: code-generate" in content  # name 不变
        assert "---" in content

    def test_no_zh_skips_zh_file(self, skill_file, output_dir):
        """--no-zh 应跳过 SKILL.zh.md 生成"""
        result = convert_skill_file(skill_file, output_dir, generate_zh=False)
        assert result.success
        assert "SKILL.zh.md" not in result.files
        assert not os.path.exists(os.path.join(output_dir, "SKILL.zh.md"))

    def test_no_meta_skips_meta_file(self, skill_file, output_dir):
        """--no-meta 应跳过 skill.meta.yaml 生成"""
        result = convert_skill_file(skill_file, output_dir, generate_meta=False)
        assert result.success
        assert "skill.meta.yaml" not in result.files
        assert not os.path.exists(os.path.join(output_dir, "skill.meta.yaml"))

    def test_result_has_skill_object(self, skill_file, output_dir):
        """result.skill 应包含解析的 Skill 对象"""
        result = convert_skill_file(skill_file, output_dir)
        assert result.skill is not None
        assert result.skill.name == "code-generate"

    def test_invalid_input_returns_error(self, tmp_path, output_dir):
        """无效输入应返回错误，不崩溃"""
        bad_file = str(tmp_path / "bad.md")
        open(bad_file, "w").write("no frontmatter here")
        result = convert_skill_file(bad_file, output_dir)
        assert not result.success
        assert len(result.errors) > 0
