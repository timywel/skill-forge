"""
优化器单元测试
"""

import pytest
from pathlib import Path
import tempfile

from skill_forge.skill_optimizer.optimizer import SkillOptimizer


class TestSkillOptimizer:
    """Skill 优化器测试"""

    @pytest.fixture
    def optimizer(self):
        """创建优化器实例"""
        return SkillOptimizer()

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    def test_analyze_minimal_skill_md(self, optimizer, temp_dir):
        """测试分析最小 SKILL.md"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: my-skill
description: 测试技能
---

## Instructions
1. 执行任务
""", encoding="utf-8")

        report = optimizer.analyze(str(skill_md))
        assert report.skill_name == "my-skill"
        assert report.overall_score >= 0
        assert len(report.dimensions) == 4  # 4 个维度

    def test_analyze_full_skill_md(self, optimizer, temp_dir):
        """测试分析完整 SKILL.md"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: code-reviewer
description: 深入分析代码质量、安全性和性能，提供可操作的改进建议
allowed-tools: Read Glob Grep Bash
---

## Instructions
1. 分析代码
2. 生成报告

## Guidelines
- 保持客观
- 提供具体建议
""", encoding="utf-8")

        report = optimizer.analyze(str(skill_md))
        assert report.skill_name == "code-reviewer"
        assert report.overall_score > 50  # 应该获得较高分数

    def test_optimize_level_0(self, optimizer, temp_dir):
        """测试 Level 0 优化（仅分析）"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: test-skill
description: 测试技能
---

## Instructions
1. 执行
""", encoding="utf-8")

        report = optimizer.optimize(str(skill_md), level=0)
        assert report.skill_name == "test-skill"
        assert len(report.optimization_changes) == 0  # level 0 不修改

    def test_optimize_level_1_no_fix(self, optimizer, temp_dir):
        """测试 Level 1 不自动修复"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: test-skill
description: 测试技能
---

## Instructions
1. 执行
""", encoding="utf-8")

        report = optimizer.optimize(str(skill_md), level=1, auto_fix=False)
        assert len(report.optimization_changes) == 0

    def test_analyze_frontmatter_dimension(self, optimizer, temp_dir):
        """测试 frontmatter 维度分析"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: test-skill
description: 测试技能描述
---

## Instructions
1. 执行
""", encoding="utf-8")

        report = optimizer.analyze(str(skill_md))
        dim = next((d for d in report.dimensions if d.name == "frontmatter"), None)
        assert dim is not None
        assert dim.score >= 50  # 有 description 所以分不低

    def test_analyze_frontmatter_missing_name(self, optimizer, temp_dir):
        """测试 frontmatter 维度 - 缺少 name"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
description: 测试
---

## Instructions
1. 执行
""", encoding="utf-8")

        report = optimizer.analyze(str(skill_md))
        # 缺少 name 时 parse_skill_md 抛出 ValueError，返回空维度
        assert report.overall_score == 0.0
        assert len(report.dimensions) == 0

    def test_analyze_body_dimension(self, optimizer, temp_dir):
        """测试 body 维度分析"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: test-skill
description: 测试技能
---

## Instructions
1. 执行任务
""", encoding="utf-8")

        report = optimizer.analyze(str(skill_md))
        dim = next((d for d in report.dimensions if d.name == "body"), None)
        assert dim is not None
        assert dim.score >= 50  # 有完整节结构

    def test_analyze_body_empty(self, optimizer, temp_dir):
        """测试 body 为空"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: test-skill
description: 测试
---

""", encoding="utf-8")

        report = optimizer.analyze(str(skill_md))
        dim = next((d for d in report.dimensions if d.name == "body"), None)
        assert dim is not None
        assert dim.score < 50  # 空 body 应该低分

    def test_analyze_tools_dimension(self, optimizer, temp_dir):
        """测试工具维度分析"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: test-skill
description: 测试
allowed-tools: Read Glob
---

## Instructions
1. 执行
""", encoding="utf-8")

        report = optimizer.analyze(str(skill_md))
        dim = next((d for d in report.dimensions if d.name == "tools"), None)
        assert dim is not None

    def test_analyze_tools_dangerous(self, optimizer, temp_dir):
        """测试工具维度 - 危险工具"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: test-skill
description: 测试
allowed-tools: Bash
---

## Instructions
1. 执行
""", encoding="utf-8")

        report = optimizer.analyze(str(skill_md))
        dim = next((d for d in report.dimensions if d.name == "tools"), None)
        assert dim is not None
        assert any("危险" in i for i in dim.issues)

    def test_analyze_security_dimension(self, optimizer, temp_dir):
        """测试安全维度分析"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: test-skill
description: 测试
allowed-tools: Bash
---

## Instructions
执行 rm -rf 命令删除文件
""", encoding="utf-8")

        report = optimizer.analyze(str(skill_md))
        dim = next((d for d in report.dimensions if d.name == "security"), None)
        assert dim is not None
        assert len(dim.issues) > 0

    def test_optimize_suggestions(self, optimizer, temp_dir):
        """测试生成优化建议"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: test-skill
description: 测试
---

## Instructions
1. 执行
""", encoding="utf-8")

        report = optimizer.optimize(str(skill_md), level=2)
        assert isinstance(report.suggestions, list)

    def test_overall_score_calculation(self, optimizer, temp_dir):
        """测试总分计算"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: test-skill
description: 测试技能
allowed-tools: Read Glob
---

## Instructions
1. 执行任务

## Guidelines
- 保持专业
""", encoding="utf-8")

        report = optimizer.analyze(str(skill_md))
        assert 0 <= report.overall_score <= 100
        weighted_sum = sum(d.score * d.weight for d in report.dimensions)
        assert abs(report.overall_score - weighted_sum) < 0.1

    def test_quality_report_to_dict(self, optimizer, temp_dir):
        """测试质量报告导出为字典"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: test-skill
description: 测试
---

## Instructions
1. 执行
""", encoding="utf-8")

        report = optimizer.analyze(str(skill_md))
        d = report.to_dict()
        assert "skill_name" in d
        assert "overall_score" in d
        assert "dimensions" in d
        assert isinstance(d["dimensions"], list)

    def test_analyze_tools_no_allowed_tools(self, optimizer, temp_dir):
        """测试未定义 allowed-tools"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: test-skill
description: 测试
---

## Instructions
1. 执行
""", encoding="utf-8")

        report = optimizer.analyze(str(skill_md))
        dim = next((d for d in report.dimensions if d.name == "tools"), None)
        assert dim is not None
        assert dim.score == 80.0  # 未定义时为 80

    def test_analyze_description_missing(self, optimizer, temp_dir):
        """测试缺少 description"""
        skill_md = temp_dir / "SKILL.md"
        skill_md.write_text("""---
name: test-skill
---

## Instructions
1. 执行
""", encoding="utf-8")

        report = optimizer.analyze(str(skill_md))
        # 缺少 description 时返回空维度（parse_skill_md 抛出 ValueError）
        assert report.overall_score == 0.0
        assert len(report.dimensions) == 0
