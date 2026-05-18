"""
Test Selection: WORST 3 Tests (by evaluation criteria)

Evaluation criteria:
  1. Clear purpose and test name
  2. Strong assertions (exact values, not vague checks)
  3. Tests important business logic
  4. No redundancy with other tests
  5. Good coverage of edge cases

Why these are worst:
  - All 3 use vague "is not None" / ">= 0" assertions that pass even on broken code
  - None verify actual behavior or edge cases
  - Each is redundant with better tests in the same file
"""

import pytest
import tempfile
from pathlib import Path

from skill_forge.skill_converter.normalize_converter import NormalizeConverter


# ============================================================
# WORST #1 — test_file_not_found (NormalizeConverter)
# File: test_converter.py
# Why worst:
#   - Assertion `"name" in result or result.get("name") == ""` is trivially true
#     The or-condition ALWAYS passes: either "name" key exists, or it's ""
#   - Zero actual verification of how the converter handles missing files
#   - Would pass even if the code silently returned garbage
#   - Completely redundant: the error handling path is not the core business logic
# ============================================================

def test_file_not_found():
    """
    测试文件不存在

    分类: converter | error handling | worst #1
    """
    converter = NormalizeConverter()
    result = converter.convert("/nonexistent/path/file.md")
    # 断言太弱：永远通过
    assert "name" in result or result.get("name") == ""


# ============================================================
# WORST #2 — test_normalize_name_kebab_case (NormalizeConverter)
# File: test_converter.py
# Why worst:
#   - Only checks that the output is not None
#     This is the weakest possible assertion — equivalent to "it ran without crashing"
#   - Zero verification that kebab-case normalization actually worked
#   - Should assert the exact output value
# ============================================================

def test_normalize_name_kebab_case():
    """
    测试名称标准化为 kebab-case

    分类: converter | normalization | worst #2
    """
    converter = NormalizeConverter()
    content = """# Test Skill

## Instructions
1. 执行
"""
    result = converter.convert(content)
    # 仅检查 key 存在，不验证 kebab-case 标准化
    assert result["name"] is not None


# ============================================================
# WORST #3 — test_extract_tools_from_agent (AgentConverter)
# File: test_converter.py
# Why worst:
#   - Only checks `in` for tool names — too loose
#   - Zero edge cases: no empty tools, no duplicate tools
#   - Does NOT verify tool count, order, or exact values
#   - The actual business logic (tool extraction from markdown) is not tested
# ============================================================

def test_extract_tools_from_agent():
    """
    测试从 Agent 提取工具列表

    分类: converter | extraction | worst #3
    """
    converter = NormalizeConverter()
    content = """## Identity
- Role: 测试

## Tools
- Read: 读取文件
- Glob: 搜索文件
- Bash: 执行命令
"""
    result = converter.convert(content)
    tools = result.get("allowed_tools", [])
    # 仅检查包含，不验证提取的完整性
    assert "Read" in tools
    assert "Glob" in tools
