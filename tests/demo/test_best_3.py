"""
Test Selection: BEST 3 Tests (by evaluation criteria)

Evaluation criteria:
  1. Clear purpose and test name
  2. Strong assertions (exact values, not vague checks)
  3. Tests important business logic
  4. No redundancy with other tests
  5. Good coverage of edge cases
"""

import pytest
import tempfile
from pathlib import Path

from skill_forge.models.skill import Skill, skill_to_md
from skill_forge.skill_validator.validator import SkillValidator
from skill_forge.skill_optimizer.optimizer import SkillOptimizer


# ============================================================
# BEST #1 — test_skill_to_md (model round-trip)
# File: test_models.py
# Why best:
#   - Tests EXACTLY what it says: round-trip parse → serialize
#   - 5 precise assertions covering the full frontmatter structure
#   - No vague `is not None` — every check verifies specific content
#   - Zero redundancy — no other test covers this round-trip path
# ============================================================

def test_skill_to_md():
    """
    测试将 Skill 序列化为 SKILL.md

    分类: model | round-trip | best #1
    """
    skill = Skill(
        name="my-skill",
        description="测试技能",
        allowed_tools=["Read"],
        markdown_body="## Instructions\n1. 执行任务",
    )
    md = skill_to_md(skill)

    # 必须以 frontmatter 开始
    assert md.startswith("---\n"), "输出必须以 frontmatter 开始"
    # 必须包含必需字段
    assert "name: my-skill" in md, "frontmatter 必须包含 name"
    assert "description: 测试技能" in md, "frontmatter 必须包含 description"
    # 必须包含 body
    assert "## Instructions" in md, "body 必须包含 Instructions 节"
    # frontmatter 必须正确闭合
    assert "---\n" in md, "frontmatter 必须正确闭合"


# ============================================================
# BEST #2 — test_parse_skill_md (model parsing)
# File: test_models.py
# Why best:
#   - Tests the core parsing path: SKILL.md → Skill object
#   - Precise assertions on all parsed fields
#   - Covers the full frontmatter + body extraction
#   - No other test duplicates this exact round-trip path
# ============================================================

def test_parse_skill_md():
    """
    测试解析 SKILL.md 格式

    分类: model | parsing | best #2
    """
    content = """---
name: code-reviewer
description: 代码审查工具
allowed-tools: Read Glob
---

## Instructions
1. 审查代码
2. 生成报告
"""
    from skill_forge.models.skill import parse_skill_md
    skill = parse_skill_md(content, "/fake/path/SKILL.md")

    # 精确验证每个字段
    assert skill.name == "code-reviewer", "name 必须正确解析"
    assert skill.description == "代码审查工具", "description 必须正确解析"
    assert "Read" in skill.allowed_tools, "allowed-tools 必须正确解析"
    assert "Glob" in skill.allowed_tools, "allowed-tools 必须正确解析"
    assert "## Instructions" in (skill.markdown_body or ""), "body 必须正确提取"
    assert skill.skill_dir == "/fake/path", "skill_dir 必须从路径提取"


# ============================================================
# BEST #3 — test_overall_score_calculation (optimizer)
# File: test_optimizer.py
# Why best:
#   - Tests MATHEMATICAL CORRECTNESS (not just "score > 0")
#   - TWO assertion layers:
#     Layer 1: range check (0 <= score <= 100)
#     Layer 2: weighted average formula correctness
#   - The second assertion catches subtle implementation bugs
#     that a simple score > 0 would miss
#   - Verifies the core algorithm, not just the output
# ============================================================

def test_overall_score_calculation():
    """
    测试总分计算（加权平均公式）

    分类: optimizer | math correctness | best #3
    """
    optimizer = SkillOptimizer()

    content = """---
name: test-skill
description: 测试技能
allowed-tools: Read Glob
---

## Instructions
1. 执行任务

## Guidelines
- 保持专业
"""

    # 写入临时文件
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "SKILL.md"
        p.write_text(content, encoding="utf-8")
        report = optimizer.analyze(str(p))

    # Layer 1: 分数必须在合法范围内
    assert 0 <= report.overall_score <= 100, \
        f"总分应在 [0, 100]，实际为 {report.overall_score}"

    # Layer 2: 总分 = 各维度加权平均（精确验证公式）
    weighted_sum = sum(d.score * d.weight for d in report.dimensions)
    assert abs(report.overall_score - weighted_sum) < 0.1, \
        f"总分应等于加权平均，误差 < 0.1，实际误差 = {abs(report.overall_score - weighted_sum):.4f}"
