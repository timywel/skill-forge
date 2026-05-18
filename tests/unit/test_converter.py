"""
转化器单元测试
"""

import pytest
from pathlib import Path
import tempfile

from skill_forge.skill_converter.normalize_converter import NormalizeConverter
from skill_forge.skill_converter.agent_converter import AgentConverter


class TestNormalizeConverter:
    """标准化转化器测试"""

    @pytest.fixture
    def converter(self):
        """创建转化器实例"""
        return NormalizeConverter()

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    def test_convert_skill_md_format(self, converter, temp_dir):
        """测试转换 SKILL.md frontmatter 格式"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: my-skill
description: 测试技能
allowed-tools: Read Glob
---

## Instructions
1. 执行任务
""", encoding="utf-8")

        result = converter.convert(str(skill_md))
        assert result["name"] == "my-skill"
        assert result["description"] == "测试技能"
        assert "markdown_body" in result

    def test_convert_pure_markdown(self, converter):
        """测试转换纯 Markdown 格式"""
        content = """# my-new-skill

## Instructions
1. 执行操作
"""
        result = converter.convert(content)
        assert result["name"] == "my-new-skill"
        assert result["markdown_body"] is not None

    def test_convert_agent_md_format(self, converter, temp_dir):
        """测试转换 Agent 格式"""
        agent_md = temp_dir / "agent.md"
        agent_md.write_text("""# my-agent

## Identity
- Role: 测试 Agent

## Instructions
1. 执行测试任务
2. 返回结果

## Tools
- Read
- Glob
- Bash
""", encoding="utf-8")

        result = converter.convert(str(agent_md))
        assert result["name"] == "my-agent"
        assert "markdown_body" in result

    def test_output_skill_md_via_helper(self, converter, temp_dir):
        """测试通过 _skill_to_md 生成完整 SKILL.md"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: output-test
description: 输出测试
allowed-tools: Read
---

## Instructions
1. 执行
""", encoding="utf-8")

        result = converter.convert(str(skill_md))
        skill_md_str = converter._skill_to_md(result)
        assert skill_md_str.startswith("---\n")
        assert "name: output-test" in skill_md_str
        assert "---\n" in skill_md_str

    def test_file_not_found(self, converter):
        """测试文件不存在时使用字符串内容"""
        result = converter.convert("/nonexistent/path/file.md")
        # 路径不存在则作为字符串内容处理
        assert "name" in result

    def test_normalize_name_kebab_case(self, converter):
        """测试名称标准化为 kebab-case"""
        content = """# test-skill

## Instructions
1. 执行
"""
        result = converter.convert(content)
        assert result["name"] == "test-skill"


class TestAgentConverter:
    """Agent 转化器测试"""

    @pytest.fixture
    def converter(self):
        """创建转化器实例"""
        return AgentConverter()

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    def test_convert_standard_agent_format(self, converter, temp_dir):
        """测试转换标准 Agent 格式"""
        agent_md = temp_dir / "agent.md"
        agent_md.write_text("""# my-agent

## Identity
- Name: My Agent
- Role: 测试 Agent

## Instructions
1. 执行测试任务
2. 返回结果

## Tools
- Read
- Glob
- Grep
""", encoding="utf-8")

        result = converter.convert(str(agent_md))
        assert result["name"] == "my-agent"
        assert "markdown_body" in result
        assert "skill_md" in result

    def test_convert_design_agent_format(self, converter, temp_dir):
        """测试转换 Design Agent 格式（带 emoji）"""
        agent_md = temp_dir / "agent.md"
        agent_md.write_text("""## Your Identity & Memory
- Role: 设计 Agent
- Personality: 创意、严谨

## Your Core Mission
1. 设计任务
2. 交付成果

## Deliverables
- 设计文档
- 原型文件
""", encoding="utf-8")

        result = converter.convert(str(agent_md))
        assert result["name"] is not None
        assert "skill_md" in result

    def test_extract_tools_from_agent(self, converter, temp_dir):
        """测试从 Agent 提取工具列表"""
        agent_md = temp_dir / "agent.md"
        agent_md.write_text("""## Identity
- Role: 测试

## Tools
- Read: 读取文件
- Glob: 搜索文件
- Bash: 执行命令
""", encoding="utf-8")

        result = converter.convert(str(agent_md))
        tools = result.get("allowed_tools", [])
        assert "Read" in tools
        assert "Glob" in tools
        assert "Bash" in tools

    def test_file_not_found(self, converter):
        """测试文件不存在"""
        with pytest.raises(FileNotFoundError):
            converter.convert("/nonexistent/agent.md")

    def test_output_is_skill_md(self, converter, temp_dir):
        """测试输出是 SKILL.md 格式"""
        agent_md = temp_dir / "agent.md"
        agent_md.write_text("""## Identity
- Role: 测试

## Instructions
1. 执行
""", encoding="utf-8")

        result = converter.convert(str(agent_md))
        skill_md = result["skill_md"]
        assert skill_md.startswith("---\n")
        assert "name:" in skill_md

    def test_allowed_tools_default(self, converter, temp_dir):
        """测试工具未声明时使用默认值"""
        agent_md = temp_dir / "agent.md"
        agent_md.write_text("""## Identity
- Role: 测试
""", encoding="utf-8")

        result = converter.convert(str(agent_md))
        tools = result.get("allowed_tools", [])
        assert "Read" in tools
