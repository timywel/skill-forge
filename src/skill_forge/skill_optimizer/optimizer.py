"""
Skill 优化器

基于 Agent Skills 规范 (https://agentskills.io/specification)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..llm.slots import (
    ConversionContext,
    LLMSlotEx,
    OptimizationContext,
    OptimizationChange,
)
from ..models.skill import Skill, parse_skill_md, skill_to_md


@dataclass
class QualityDimension:
    """质量维度"""
    name: str
    score: float  # 0-100
    weight: float
    issues: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.score = max(0.0, min(100.0, self.score))


@dataclass
class QualityReport:
    """质量报告"""
    skill_name: str
    file_path: str
    overall_score: float  # 0-100
    dimensions: List[QualityDimension]
    optimization_changes: List[OptimizationChange] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_name": self.skill_name,
            "file_path": self.file_path,
            "overall_score": self.overall_score,
            "dimensions": [
                {"name": d.name, "score": d.score, "weight": d.weight, "issues": d.issues}
                for d in self.dimensions
            ],
            "optimization_changes": [c.to_dict() for c in self.optimization_changes],
            "suggestions": self.suggestions,
        }


class SkillOptimizer:
    """Skill 优化器"""

    DEFAULT_WEIGHTS = {
        "frontmatter": 0.25,
        "body": 0.35,
        "tools": 0.20,
        "security": 0.20,
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.weights = self.config.get("weights", self.DEFAULT_WEIGHTS)

    def analyze(self, path: str) -> QualityReport:
        """分析 Skill 质量"""
        try:
            content = Path(path).read_text(encoding="utf-8")
        except Exception:
            return QualityReport(
                skill_name="Unknown",
                file_path=path,
                overall_score=0.0,
                dimensions=[],
                suggestions=[f"无法读取文件: {path}"],
            )

        try:
            skill = parse_skill_md(content, path)
        except ValueError:
            return QualityReport(
                skill_name="Unknown",
                file_path=path,
                overall_score=0.0,
                dimensions=[],
                suggestions=["SKILL.md 格式错误"],
            )

        skill_name = skill.name or "unknown"

        dimensions = []
        dimensions.append(self._analyze_frontmatter(skill))
        dimensions.append(self._analyze_body(skill))
        dimensions.append(self._analyze_tools(skill))
        dimensions.append(self._analyze_security(skill))

        overall_score = sum(d.score * d.weight for d in dimensions)

        return QualityReport(
            skill_name=skill_name,
            file_path=path,
            overall_score=overall_score,
            dimensions=dimensions,
        )

    def optimize(
        self,
        path: str,
        level: int = 1,
        auto_fix: bool = False,
        llm: Optional[LLMSlotEx] = None,
    ) -> QualityReport:
        """优化 Skill"""
        ctx = OptimizationContext(level=level, auto_fix=auto_fix, llm=llm)
        report = self.analyze(path)

        if level == 0:
            return report

        if level >= 1 and auto_fix:
            report = self._auto_fix(path, report, ctx)

        if level >= 3 and llm:
            report = self._llm_enhance(path, report, llm)

        report.suggestions = self._generate_suggestions(report)
        return report

    def _auto_fix(self, path: str, report: QualityReport, ctx: OptimizationContext) -> QualityReport:
        """自动修复简单问题"""
        try:
            content = Path(path).read_text(encoding="utf-8")
            skill = parse_skill_md(content, path)

            # 确保必需字段
            if not skill.description:
                ctx.add_change("frontmatter", "description", "", "缺少必需字段")
                return report

            # 确保 body 有内容
            if not skill.markdown_body:
                ctx.add_change("body", "markdown_body", "", "body 为空")
                return report

            # 确保有 Instructions 节
            body = skill.markdown_body or ""
            if not re.search(r"##\s*instructions", body, re.IGNORECASE):
                skill.markdown_body = f"## Instructions\n\n{body}"

            # 写回
            new_content = skill_to_md(skill)
            Path(path).write_text(new_content, encoding="utf-8")
            ctx.add_change("format", "content", "improved", "已自动修复")
            return self.analyze(path)

        except Exception:
            return report

    def _llm_enhance(self, path: str, report: QualityReport, llm: LLMSlotEx) -> QualityReport:
        """LLM 增强优化"""
        try:
            content = Path(path).read_text(encoding="utf-8")
            skill = parse_skill_md(content, path)
            body = skill.markdown_body or ""

            analysis = "\n".join([
                f"- {d.name}: {d.score:.0f}/100 - {'; '.join(d.issues[:3]) if d.issues else '无问题'}"
                for d in report.dimensions
            ])

            requirements = []
            for d in report.dimensions:
                if d.score < 80:
                    requirements.append(f"- {d.name}: {', '.join(d.issues[:2])}")

            system = f"""你是一个 Skill 优化专家。基于以下分析，改进 Skill 的 markdown body。

当前维度评分：
{analysis}

需要改进的维度：
{chr(10).join(requirements) if requirements else '无'}

请改进 markdown body 内容，保持现有结构，修复发现的问题。"""
            user = f"当前 body:\n{body}"

            improved = llm.complete(system, user).strip()

            # 清理 markdown 代码块
            if improved.startswith("```markdown"):
                improved = improved[12:]
            elif improved.startswith("```md"):
                improved = improved[5:]
            if improved.startswith("```"):
                improved = improved[3:]
            if improved.endswith("```"):
                improved = improved[:-3]
            improved = improved.strip()

            if improved and improved != body:
                skill.markdown_body = improved
                new_content = skill_to_md(skill)
                Path(path).write_text(new_content, encoding="utf-8")
                return self.analyze(path)

        except Exception as e:
            report.suggestions.append(f"LLM 增强优化失败: {str(e)}")

        return report

    def _analyze_frontmatter(self, skill: Skill) -> QualityDimension:
        """分析 frontmatter 质量"""
        score = 100.0
        issues = []

        if not skill.name:
            issues.append("缺少 name 字段")
            score -= 30.0
        elif len(skill.name) < 3:
            issues.append("name 可能过短")
            score -= 10.0

        if not skill.description:
            issues.append("缺少 description 字段")
            score -= 30.0
        elif len(skill.description or "") < 10:
            issues.append("description 可能过短")
            score -= 10.0
        elif len(skill.description or "") > 1024:
            issues.append("description 超过 1024 字符限制")
            score -= 10.0

        return QualityDimension(
            name="frontmatter",
            score=score,
            weight=self.weights.get("frontmatter", 0.25),
            issues=issues,
        )

    def _analyze_body(self, skill: Skill) -> QualityDimension:
        """分析 markdown body 质量"""
        score = 100.0
        issues = []

        body = skill.markdown_body or ""

        if not body:
            issues.append("markdown body 为空")
            return QualityDimension(
                name="body",
                score=0.0,
                weight=self.weights.get("body", 0.35),
                issues=issues,
            )

        if len(body) < 50:
            issues.append("body 过短")
            score -= 20.0

        if not re.search(r"##\s*instructions", body, re.IGNORECASE):
            issues.append("建议包含 ## Instructions 节")
            score -= 15.0

        return QualityDimension(
            name="body",
            score=score,
            weight=self.weights.get("body", 0.35),
            issues=issues,
        )

    def _analyze_tools(self, skill: Skill) -> QualityDimension:
        """分析工具配置"""
        score = 100.0
        issues = []

        tools = skill.allowed_tools or []
        if not tools:
            issues.append("未定义 allowed-tools")
            score = 80.0

        # 检查危险工具
        dangerous = {"Bash", "Write", "Edit"}
        has_dangerous = any(t in dangerous or t.startswith("Bash") for t in tools)
        if has_dangerous:
            issues.append("使用了危险工具，请确保已限制权限")
            score -= 15.0

        return QualityDimension(
            name="tools",
            score=score,
            weight=self.weights.get("tools", 0.20),
            issues=issues,
        )

    def _analyze_security(self, skill: Skill) -> QualityDimension:
        """分析安全性"""
        score = 100.0
        issues = []

        body = skill.markdown_body or ""
        dangerous_patterns = [
            (r"rm\s+-rf", "rm -rf 可能导致数据丢失"),
            (r"drop\s+database", "DROP DATABASE 可能导致数据丢失"),
        ]
        for pattern, msg in dangerous_patterns:
            if re.search(pattern, body):
                issues.append(f"检测到潜在危险操作: {msg}")
                score -= 15.0

        return QualityDimension(
            name="security",
            score=score,
            weight=self.weights.get("security", 0.20),
            issues=issues,
        )

    def _generate_suggestions(self, report: QualityReport) -> List[str]:
        """生成优化建议"""
        suggestions = []
        for d in report.dimensions:
            if d.score < 60:
                suggestions.append(f"【{d.name}】{'; '.join(d.issues[:2])}")
        if report.overall_score < 60:
            suggestions.append("整体质量较低，建议进行全面优化（level 3 + LLM）")
        return suggestions
