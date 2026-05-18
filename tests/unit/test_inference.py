"""
tests/unit/test_inference.py
推断逻辑验证测试
"""

from __future__ import annotations
import pytest
from skill_forge.inference.category_inference import (
    infer_category,
    infer_cognitive_phase,
    infer_triggers,
)


class TestInferCategory:
    """测试 infer_category()"""

    def test_test_keyword_returns_test(self):
        assert infer_category("unit-test", "Run unit tests for the module") == "test"

    def test_security_keyword_returns_security(self):
        assert infer_category("security-audit", "Detect security vulnerabilities") == "security"

    def test_doc_keyword_returns_doc(self):
        assert infer_category("generate-doc", "Generate documentation for code") == "doc"

    def test_code_keyword_returns_code(self):
        assert infer_category("code-write", "Write and implement code for the feature") == "code"

    def test_infra_keyword_returns_infra(self):
        assert infer_category("deploy-app", "Deploy application to Kubernetes cluster") == "infra"

    def test_unknown_returns_system(self):
        assert infer_category("unknown-skill", "Does something unknown") == "system"

    def test_quality_keyword_returns_quality(self):
        assert infer_category("code-review", "Review code quality") == "quality"

    def test_framework_keyword_returns_framework(self):
        assert infer_category("react-component", "Build React components") == "framework"


class TestInferCognitivePhase:
    """测试 infer_cognitive_phase()"""

    def test_review_keyword_returns_critic(self):
        assert infer_cognitive_phase("Review code for bugs and security issues") == "critic"

    def test_analyze_keyword_returns_observer(self):
        assert infer_cognitive_phase("Analyze codebase and collect metrics") == "observer"

    def test_plan_keyword_returns_strategist(self):
        assert infer_cognitive_phase("Plan and design system architecture") == "strategist"

    def test_default_returns_executor(self):
        assert infer_cognitive_phase("Generate code from specification") == "executor"

    def test_chinese_review_returns_critic(self):
        assert infer_cognitive_phase("对代码进行评审和质量控制") == "critic"

    def test_chinese_analyze_returns_observer(self):
        assert infer_cognitive_phase("分析系统性能并监控指标") == "observer"


class TestInferTriggers:
    """测试 infer_triggers()"""

    def test_returns_list(self):
        result = infer_triggers("code-generate", "Generate code")
        assert isinstance(result, list)

    def test_returns_at_most_5(self):
        result = infer_triggers(
            "full-stack-skill",
            "generate code, review code, deploy, debug, document, test"
        )
        assert len(result) <= 5

    def test_project_create_trigger(self):
        result = infer_triggers("project-scaffold", "Scaffold new project structure")
        assert "project-create" in result

    def test_deploy_trigger(self):
        result = infer_triggers("deploy-tool", "Deploy application to production")
        assert "deploy" in result

    def test_empty_description_returns_empty_or_small_list(self):
        result = infer_triggers("x", "")
        assert isinstance(result, list)
        assert len(result) <= 5

    def test_debug_trigger(self):
        result = infer_triggers("debug-helper", "Help debug and fix bugs")
        assert "debug" in result
