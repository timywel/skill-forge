"""
验证结果数据模型

基于 Agent Skills 规范 (https://agentskills.io/specification)

错误码：
- E1xx: 必需字段问题
- E2xx: name 格式问题
- E3xx: YAML/Frontmatter 格式问题
- E4xx: allowed-tools 问题
- W1xx: 内容质量问题
- S1xx: 安全问题
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class IssueSeverity(str, Enum):
    """问题严重程度"""
    ERROR = "error"
    WARNING = "warning"
    SUGGESTION = "suggestion"


class IssueCode(str, Enum):
    """问题代码（基于 Agent Skills 规范）"""

    # === 必需字段问题 (E1xx) ===
    E101 = "E101"  # name 字段缺失
    E102 = "E102"  # name 字段超过最大长度（64字符）
    E103 = "E103"  # name 包含连续连字符
    E104 = "E104"  # description 字段缺失
    E105 = "E105"  # description 超过最大长度（1024字符）

    # === name 格式问题 (E2xx) ===
    E201 = "E201"  # name 不是 kebab-case
    E202 = "E202"  # name 首字符为连字符
    E203 = "E203"  # name 以连字符结尾
    E204 = "E204"  # name 包含非法字符

    # === YAML/Frontmatter 格式问题 (E3xx) ===
    E301 = "E301"  # frontmatter 未正确闭合
    E302 = "E302"  # frontmatter YAML 解析失败
    E303 = "E303"  # frontmatter 根元素不是字典
    E304 = "E304"  # 文件不存在

    # === allowed-tools 问题 (E4xx) ===
    E401 = "E401"  # allowed-tools 格式错误
    E402 = "E402"  # 工具名称包含非法字符

    # === 内容质量问题 (W1xx) ===
    W101 = "W101"  # markdown body 为空
    W102 = "W102"  # markdown body 过短（<50 字符）
    W103 = "W103"  # 缺少 ## Instructions 节
    W104 = "W104"  # description 过短（<10字符）

    # === 安全问题 (S1xx) ###
    S101 = "S101"  # allowed-tools 包含危险工具


class ValidationIssue(BaseModel):
    """单个验证问题"""
    code: IssueCode = Field(..., description="问题代码")
    severity: IssueSeverity = Field(..., description="严重程度")
    message: str = Field(..., description="问题描述")
    field_path: str = Field(default="", description="字段路径")
    suggestion: str = Field(default="", description="修复建议")
    line_number: Optional[int] = Field(default=None, description="问题所在行号")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code.value,
            "severity": self.severity.value,
            "message": self.message,
            "field_path": self.field_path,
            "suggestion": self.suggestion,
            "line_number": self.line_number,
        }


class ValidationResult(BaseModel):
    """验证结果"""
    path: str = Field(..., description="被验证的文件路径")
    valid: bool = Field(default=True, description="是否通过验证")
    skill_name: Optional[str] = Field(default=None, description="Skill 名称")
    file_format: Optional[str] = Field(default=None, description="文件格式（SKILL.md / skill.yaml）")

    # 问题统计
    error_count: int = Field(default=0, description="错误数量")
    warning_count: int = Field(default=0, description="警告数量")
    suggestion_count: int = Field(default=0, description="建议数量")
    migration_count: int = Field(default=0, description="迁移建议数量")

    # 问题列表
    errors: List[ValidationIssue] = Field(default_factory=list)
    warnings: List[ValidationIssue] = Field(default_factory=list)
    suggestions: List[ValidationIssue] = Field(default_factory=list)
    migrations: List[ValidationIssue] = Field(default_factory=list)

    @property
    def total_issues(self) -> int:
        return self.error_count + self.warning_count + self.suggestion_count

    def add_issue(self, issue: ValidationIssue) -> None:
        if issue.severity == IssueSeverity.ERROR:
            self.errors.append(issue)
            self.error_count = len(self.errors)
            self.valid = False
        elif issue.severity == IssueSeverity.WARNING:
            self.warnings.append(issue)
            self.warning_count = len(self.warnings)
        else:
            self.suggestions.append(issue)
            self.suggestion_count = len(self.suggestions)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "valid": self.valid,
            "skill_name": self.skill_name,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "suggestion_count": self.suggestion_count,
            "total_issues": self.total_issues,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "suggestions": [s.to_dict() for s in self.suggestions],
        }

    model_config = {"use_enum_values": True}


class BatchValidationResult(BaseModel):
    """批量验证结果"""
    total: int = Field(default=0)
    passed: int = Field(default=0)
    failed: int = Field(default=0)
    migration_needed: int = Field(default=0, description="需要迁移的文件数量")
    results: List[ValidationResult] = Field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.passed / self.total * 100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": f"{self.pass_rate:.1f}%",
            "results": [r.to_dict() for r in self.results],
        }
