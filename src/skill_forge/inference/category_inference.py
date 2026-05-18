"""
Skill 字段自动推断模块（v3.1.0 新增）

根据 skill name / description 推断：
- category: 技能分类
- cognitive_phase: 认知阶段
- triggers: 触发关键词列表
"""

from __future__ import annotations
from typing import List


# ===========================================================================
# category 推断
# ===========================================================================

# 分类关键词映射（从高优先级到低优先级）
_CATEGORY_RULES: list[tuple[str, list[str]]] = [
    ("test",      ["test", "测试", "validate", "验证", "qa", "e2e", "unit test"]),
    ("quality",   ["quality", "质量", "lint", "code-review", "review"]),
    ("security",  ["security", "安全", "vulnerability", "漏洞", "pentest"]),
    ("doc",       ["doc", "文档", "readme", "documentation", "comment"]),
    ("infra",     ["infra", "deploy", "部署", "docker", "k8s", "kubernetes", "ci/cd", "cicd", "pipeline"]),
    ("spec",      ["spec", "规格", "需求", "requirement", "prd"]),
    ("project",   ["project", "项目", "scaffold", "模板", "boilerplate", "template"]),
    ("internet",  ["internet", "web", "browser", "search", "爬虫", "crawl", "scrape"]),
    ("loop",      ["loop", "ralph", "迭代", "反馈", "feedback", "iteration"]),
    ("framework", ["framework", "框架", "react", "vue", "spring", "fastapi", "django"]),
    ("tooling",   ["tool", "工具", "forge", "generate", "scaffold", "cli", "script"]),
    ("process",   ["process", "流程", "workflow", "pipeline", "orchestrat"]),
    ("code",      ["code", "代码", "generate", "生成", "implement", "implement"]),
    ("domain",    ["domain", "领域", "medical", "finance", "legal", "业务"]),
]


def infer_category(name: str, description: str) -> str:
    """从 skill name 和 description 推断 category。

    Returns:
        category 字符串，未匹配时返回 'system'
    """
    text = f"{name} {description}".lower()
    for category, keywords in _CATEGORY_RULES:
        if any(kw in text for kw in keywords):
            return category
    return "system"


# ===========================================================================
# cognitive_phase 推断
# ===========================================================================

def infer_cognitive_phase(description: str) -> str:
    """从 description 推断 cognitive_phase。

    Returns:
        'observer' | 'strategist' | 'executor' | 'critic'
    """
    text = description.lower()

    if any(k in text for k in ["review", "critic", "评审", "审查", "反馈", "evaluate", "assess", "质量控制"]):
        return "critic"
    if any(k in text for k in ["observe", "analyze", "monitor", "分析", "观察", "research", "调研", "collect"]):
        return "observer"
    if any(k in text for k in ["plan", "strategy", "design", "规划", "策略", "roadmap", "架构", "architect"]):
        return "strategist"

    return "executor"


# ===========================================================================
# triggers 推断
# ===========================================================================

# 触发关键词映射：trigger_key → 匹配词列表
_TRIGGER_MAP: list[tuple[str, list[str]]] = [
    ("project-create",  ["project-create", "project create", "创建项目", "new project", "scaffold"]),
    ("feature-generate",["feature-generate", "feature generate", "生成功能", "新功能", "generate feature"]),
    ("code-review",     ["code-review", "code review", "代码审查", "review code", "代码评审"]),
    ("test-generate",   ["test-generate", "test generate", "生成测试", "写测试", "unit test"]),
    ("deploy",          ["deploy", "部署", "发布", "release", "publish"]),
    ("debug",           ["debug", "调试", "fix bug", "故障排查", "troubleshoot"]),
    ("refactor",        ["refactor", "重构", "重构代码", "refactoring", "improve code"]),
    ("document",        ["document", "文档", "写文档", "readme", "documentation"]),
    ("security-audit",  ["security", "安全审查", "漏洞", "vulnerability", "pentest"]),
    ("optimize",        ["optimize", "优化", "performance", "性能", "improve"]),
]


def infer_triggers(name: str, description: str) -> List[str]:
    """从 name 和 description 推断触发关键词列表（最多返回 5 个）。

    Returns:
        触发关键词列表
    """
    text = f"{name} {description}".lower()
    triggers = []
    for trigger_key, keywords in _TRIGGER_MAP:
        if any(kw in text for kw in keywords):
            triggers.append(trigger_key)
        if len(triggers) >= 5:
            break
    return triggers
