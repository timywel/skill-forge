"""
Skill 验证器单元测试
"""

import pytest
from pathlib import Path
import tempfile

from skill_forge.skill_validator.validator import SkillValidator
from skill_forge.models.validation import IssueCode, IssueSeverity


class TestSkillValidator:
    """Skill 验证器测试"""

    @pytest.fixture
    def validator(self):
        """创建验证器实例"""
        return SkillValidator()

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    def test_valid_minimal_skill_md(self, validator, temp_dir):
        """测试有效的最小 SKILL.md"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: my-skill
description: 测试技能
---

## Instructions
1. 执行任务
""", encoding="utf-8")

        result = validator.validate_file(str(skill_md))
        assert result.valid is True
        assert result.error_count == 0
        assert result.skill_name == "my-skill"

    def test_valid_full_skill_md(self, validator, temp_dir):
        """测试完整的有效 SKILL.md"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: code-reviewer
description: 专业的代码审查工具
allowed-tools: Read Glob Grep Bash
---

## Instructions
1. 分析代码
2. 生成报告

## Guidelines
- 保持客观
- 提供具体建议
""", encoding="utf-8")

        result = validator.validate_file(str(skill_md))
        assert result.valid is True
        assert result.skill_name == "code-reviewer"

    def test_invalid_name_spaces(self, validator, temp_dir):
        """测试无效的 name（包含空格）"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: test skill
description: 测试
---

## Instructions
1. 执行
""", encoding="utf-8")

        result = validator.validate_file(str(skill_md))
        assert result.valid is False

    def test_invalid_name_underscore(self, validator, temp_dir):
        """测试无效的 name（下划线）"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: test_skill
description: 测试
---

## Instructions
1. 执行
""", encoding="utf-8")

        result = validator.validate_file(str(skill_md))
        assert result.valid is False

    def test_name_too_long(self, validator, temp_dir):
        """测试 name 过长"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text(f"""---
name: {"a" * 65}
description: 测试
---

## Instructions
1. 执行
""", encoding="utf-8")

        result = validator.validate_file(str(skill_md))
        assert result.valid is False

    def test_frontmatter_not_closed(self, validator, temp_dir):
        """测试 frontmatter 未正确闭合"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: test-skill
未闭合的 frontmatter

## Instructions
1. 执行
""", encoding="utf-8")

        result = validator.validate_file(str(skill_md))
        assert result.valid is False

    def test_bash_tool_warning(self, validator, temp_dir):
        """测试 Bash 工具警告"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: test-skill
description: 测试
allowed-tools: Bash
---

## Instructions
1. 执行
""", encoding="utf-8")

        result = validator.validate_file(str(skill_md))
        assert result.warning_count > 0
        assert any(w.code == IssueCode.S101 for w in result.warnings)

    def test_empty_markdown_body_warning(self, validator, temp_dir):
        """测试空 markdown body（警告）"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: test-skill
description: 测试技能
---

""", encoding="utf-8")

        result = validator.validate_file(str(skill_md))
        assert result.warning_count >= 1

    def test_yaml_parse_error(self, validator, temp_dir):
        """测试 YAML 解析错误"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: test
  invalid: indentation
---

## Instructions
1. 执行
""", encoding="utf-8")

        result = validator.validate_file(str(skill_md))
        assert result.valid is False

    def test_file_not_found(self, validator):
        """测试文件不存在"""
        result = validator.validate_file("/nonexistent/path/SKILL.md")
        assert result.valid is False

    def test_validate_content(self, validator):
        """测试验证 SKILL.md 内容"""
        content = """---
name: test-skill
description: 测试技能
---

## Instructions
1. 执行任务
"""
        result = validator.validate_content(content)
        assert result.valid is True

    def test_dynamic_injection_empty_command(self, validator, temp_dir):
        """测试动态注入空命令（错误）"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: test-skill
description: 测试
allowed-tools: Bash
---

## Context
空命令: !``
""", encoding="utf-8")

        result = validator.validate_file(str(skill_md))
        assert result.valid is False

    def test_dynamic_injection_incomplete_backtick(self, validator, temp_dir):
        """测试不完整的反引号（错误）"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: test-skill
description: 测试
---

## Context
不完整: !`git branch
""", encoding="utf-8")

        result = validator.validate_file(str(skill_md))
        assert result.valid is False

    def test_allowed_tools_space_delimited(self, validator, temp_dir):
        """测试 allowed-tools 空格分隔格式"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: test-skill
description: 测试
allowed-tools: Read Glob Grep Bash
---

## Instructions
1. 执行
""", encoding="utf-8")

        result = validator.validate_file(str(skill_md))
        assert result.valid is True

    def test_no_frontmatter_starts(self, validator):
        """测试不以 --- 开头"""
        content = """name: test-skill
description: 测试
"""
        result = validator.validate_content(content)
        assert result.valid is False
        assert result.error_count > 0

    def test_description_too_long(self, validator, temp_dir):
        """测试 description 超过 1024 字符"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text(f"""---
name: test-skill
description: {"x" * 1025}
---

## Instructions
1. 执行
""", encoding="utf-8")

        result = validator.validate_file(str(skill_md))
        assert result.valid is False
