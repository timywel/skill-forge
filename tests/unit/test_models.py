"""
Skill 模型单元测试
"""

import pytest
from pathlib import Path
import tempfile

from skill_forge.models.skill import Skill, parse_skill_md, skill_to_md
from skill_forge.models.validation import (
    IssueCode,
    IssueSeverity,
    ValidationIssue,
    ValidationResult,
)


class TestSkillModel:
    """Skill 模型测试"""

    def test_valid_skill_minimal(self):
        """测试最小有效 Skill"""
        skill = Skill(
            name="my-skill",
            description="测试技能",
            markdown_body="## Instructions\n1. 执行任务",
        )
        assert skill.name == "my-skill"
        assert skill.description == "测试技能"

    def test_name_with_spaces(self):
        """测试 name 包含空格"""
        with pytest.raises(ValueError, match="kebab-case"):
            Skill(
                name="test skill",
                description="测试",
                markdown_body="## Instructions\n1. 执行",
            )

    def test_name_with_underscore(self):
        """测试 name 包含下划线"""
        with pytest.raises(ValueError, match="kebab-case"):
            Skill(
                name="test_skill",
                description="测试",
                markdown_body="## Instructions\n1. 执行",
            )

    def test_name_consecutive_hyphens(self):
        """测试 name 包含连续连字符"""
        with pytest.raises(ValueError, match="连续连字符"):
            Skill(
                name="test--skill",
                description="测试",
                markdown_body="## Instructions\n1. 执行",
            )

    def test_name_too_long(self):
        """测试 name 过长"""
        long_name = "a" * 65
        with pytest.raises(ValueError, match="64"):
            Skill(
                name=long_name,
                description="测试",
                markdown_body="## Instructions\n1. 执行",
            )

    def test_description_too_long(self):
        """测试 description 过长"""
        long_desc = "x" * 1025
        with pytest.raises(ValueError, match="1024"):
            Skill(
                name="test-skill",
                description=long_desc,
                markdown_body="## Instructions\n1. 执行",
            )

    def test_allowed_tools_list(self):
        """测试 allowed-tools 工具列表"""
        skill = Skill(
            name="test-skill",
            description="测试",
            markdown_body="## Instructions\n1. 执行",
            allowed_tools=["Read", "Bash", "Glob"],
        )
        assert skill.allowed_tools == ["Read", "Bash", "Glob"]

    def test_allowed_tools_string(self):
        """测试 allowed-tools 接受空格分隔字符串"""
        skill = Skill(
            name="test-skill",
            description="测试",
            markdown_body="## Instructions\n1. 执行",
            allowed_tools="Read Bash Glob",
        )
        assert skill.allowed_tools == ["Read", "Bash", "Glob"]

    def test_frontmatter_to_dict(self):
        """测试 frontmatter 导出为字典"""
        skill = Skill(
            name="test-skill",
            description="测试",
            allowed_tools=["Read"],
            license="MIT",
        )
        fm = skill.to_frontmatter_dict()
        assert fm["name"] == "test-skill"
        assert fm["description"] == "测试"
        assert fm["allowed-tools"] == "Read"
        assert fm["license"] == "MIT"

    def test_parse_skill_md(self):
        """测试解析 SKILL.md 格式"""
        content = """---
name: code-reviewer
description: 代码审查工具
allowed-tools: Read Glob
---

## Instructions
1. 审查代码
2. 生成报告
"""
        skill = parse_skill_md(content, "/fake/path/SKILL.md")
        assert skill.name == "code-reviewer"
        assert skill.description == "代码审查工具"
        assert "Read" in skill.allowed_tools
        assert "## Instructions" in (skill.markdown_body or "")

    def test_parse_skill_md_with_yaml_list(self):
        """测试解析 allowed-tools 为 YAML 列表格式"""
        content = """---
name: test-skill
description: 测试
allowed-tools:
  - Read
  - Glob
---

## Instructions
1. 执行
"""
        skill = parse_skill_md(content)
        assert "Read" in skill.allowed_tools
        assert "Glob" in skill.allowed_tools

    def test_skill_to_md(self):
        """测试将 Skill 序列化为 SKILL.md"""
        skill = Skill(
            name="my-skill",
            description="测试技能",
            allowed_tools=["Read"],
            markdown_body="## Instructions\n1. 执行任务",
        )
        md = skill_to_md(skill)
        assert md.startswith("---\n")
        assert "name: my-skill" in md
        assert "description: 测试技能" in md
        assert "## Instructions" in md
        assert "---\n" in md

    def test_parse_skill_md_without_closing(self):
        """测试 frontmatter 未正确闭合"""
        content = """---
name: test
未闭合

## Instructions
1. 执行
"""
        with pytest.raises(ValueError, match="未正确闭合"):
            parse_skill_md(content)

    def test_parse_skill_md_without_name(self):
        """测试缺少 name 字段"""
        content = """---
description: 测试
---

## Instructions
1. 执行
"""
        with pytest.raises(ValueError, match="name"):
            parse_skill_md(content)

    def test_parse_skill_md_without_description(self):
        """测试缺少 description 字段"""
        content = """---
name: test-skill
---

## Instructions
1. 执行
"""
        with pytest.raises(ValueError, match="description"):
            parse_skill_md(content)

    def test_metadata_field(self):
        """测试 metadata 字段"""
        skill = Skill(
            name="test-skill",
            description="测试",
            metadata={"author": "test", "version": "1.0"},
            markdown_body="## Instructions\n1. 执行",
        )
        fm = skill.to_frontmatter_dict()
        assert fm["metadata"]["author"] == "test"
        assert fm["metadata"]["version"] == "1.0"


class TestValidationResult:
    """验证结果模型测试"""

    def test_add_error(self):
        """测试添加错误"""
        result = ValidationResult(path="test.md", valid=True)
        result.add_issue(ValidationIssue(
            code=IssueCode.E101,
            severity=IssueSeverity.ERROR,
            message="name 字段格式错误",
        ))
        assert result.error_count == 1
        assert result.valid is False

    def test_add_warning(self):
        """测试添加警告"""
        result = ValidationResult(path="test.md", valid=True)
        result.add_issue(ValidationIssue(
            code=IssueCode.W101,
            severity=IssueSeverity.WARNING,
            message="markdown body 为空",
        ))
        assert result.warning_count == 1
        assert result.valid is True

    def test_add_suggestion(self):
        """测试添加建议"""
        result = ValidationResult(path="test.md", valid=True)
        result.add_issue(ValidationIssue(
            code=IssueCode.W103,
            severity=IssueSeverity.SUGGESTION,
            message="建议包含 ## Instructions 节",
        ))
        assert result.suggestion_count == 1
        assert result.valid is True

    def test_to_dict(self):
        """测试转换为字典"""
        result = ValidationResult(
            path="test.md",
            valid=False,
            skill_name="test-skill",
        )
        result.add_issue(ValidationIssue(
            code=IssueCode.E101,
            severity=IssueSeverity.ERROR,
            message="name 字段格式错误",
        ))

        d = result.to_dict()
        assert d["path"] == "test.md"
        assert d["valid"] is False
        assert d["skill_name"] == "test-skill"
        assert len(d["errors"]) == 1

    def test_batch_validation_result(self):
        """测试批量验证结果"""
        from skill_forge.models.validation import BatchValidationResult

        batch = BatchValidationResult()
        batch.total = 3
        batch.passed = 2
        batch.failed = 1

        assert batch.pass_rate == pytest.approx(66.7, 0.1)

        d = batch.to_dict()
        assert d["total"] == 3
        assert d["passed"] == 2
