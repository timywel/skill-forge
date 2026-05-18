"""
tests/unit/test_meta_yaml.py
skill.meta.yaml 完整性验证测试
"""

from __future__ import annotations
import yaml
import pytest
from skill_forge.models.skill import Skill, parse_skill_md


SAMPLE_MD = """\
---
name: security-audit
description: Perform security audit and vulnerability assessment for code and infrastructure.
license: Apache-2.0
---

## Instructions

Review code for security issues.
"""


@pytest.fixture
def sample_skill() -> Skill:
    return parse_skill_md(SAMPLE_MD)


class TestToMetaYaml:
    """测试 Skill.to_meta_yaml() 输出完整性"""

    def test_meta_yaml_is_valid_yaml(self, sample_skill):
        """to_meta_yaml() 应返回合法 YAML 字符串"""
        output = sample_skill.to_meta_yaml()
        assert isinstance(output, str)
        # 去掉注释行后解析
        data = yaml.safe_load("\n".join(
            line for line in output.splitlines() if not line.startswith("#")
        ))
        assert isinstance(data, dict)

    def test_meta_yaml_has_required_fields(self, sample_skill):
        """to_meta_yaml() 应包含所有必需字段"""
        output = sample_skill.to_meta_yaml()
        data = yaml.safe_load("\n".join(
            line for line in output.splitlines() if not line.startswith("#")
        ))

        required_fields = ["name", "version", "name_key", "description_key"]
        for field in required_fields:
            assert field in data, f"缺少字段: {field}"

    def test_name_key_format(self, sample_skill):
        """name_key 格式应为 skills.{name}.name"""
        assert sample_skill.name_key == "skills.security-audit.name"

    def test_description_key_format(self, sample_skill):
        """description_key 格式应为 skills.{name}.description"""
        assert sample_skill.description_key == "skills.security-audit.description"

    def test_name_en_defaults_to_name(self, sample_skill):
        """name_en 未设置时默认等于 name"""
        assert sample_skill.name_en == sample_skill.name

    def test_meta_yaml_has_header_comment(self, sample_skill):
        """skill.meta.yaml 应以注释头开头"""
        output = sample_skill.to_meta_yaml()
        assert output.startswith("# BaiZe Skill 元数据")

    def test_to_meta_yaml_dict_removes_none_values(self, sample_skill):
        """to_meta_yaml_dict() 应移除 None 值"""
        data = sample_skill.to_meta_yaml_dict()
        # mcp_server 未设置，不应出现 None
        assert data.get("mcp_server") is None or "mcp_server" not in data

    def test_category_set_via_attribute(self):
        """category 属性可正确写入 meta_yaml"""
        skill = parse_skill_md(SAMPLE_MD)
        object.__setattr__(skill, "category", "security")
        data = skill.to_meta_yaml_dict()
        assert data["category"] == "security"

    def test_cognitive_phase_set_via_attribute(self):
        """cognitive_phase 属性可正确写入 meta_yaml"""
        skill = parse_skill_md(SAMPLE_MD)
        object.__setattr__(skill, "cognitive_phase", "critic")
        data = skill.to_meta_yaml_dict()
        assert data["cognitive_phase"] == "critic"

    def test_triggers_set_via_attribute(self):
        """triggers 属性可正确写入 meta_yaml"""
        skill = parse_skill_md(SAMPLE_MD)
        object.__setattr__(skill, "triggers", ["security-audit", "code-review"])
        data = skill.to_meta_yaml_dict()
        assert data["triggers"] == ["security-audit", "code-review"]
