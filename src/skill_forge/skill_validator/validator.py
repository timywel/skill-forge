"""
Skill 验证器

基于 Agent Skills 规范 (https://agentskills.io/specification)

验证规则：
- name: 必需，kebab-case，最大 64 字符
- description: 必需，最大 1024 字符
- license/compatibility/metadata/allowed-tools: 可选
- allowed-tools: 空格分隔列表
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models.skill import Skill, parse_skill_md
from ..models.validation import (
    IssueCode,
    IssueSeverity,
    ValidationIssue,
    ValidationResult,
)

# 已知工具列表
KNOWN_TOOLS = {
    "Read", "Glob", "Grep", "Bash", "Edit", "Write",
    "WebFetch", "WebSearch",
    "Agent", "TaskCreate", "TaskGet", "TaskList", "TaskUpdate",
    "AskUserQuestion", "TaskStop",
    "ExitPlanMode", "TaskOutput",
}

# 危险工具
DANGEROUS_TOOLS = {"Bash", "Write", "Edit"}


class SkillValidator:
    """Skill 验证器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def validate_file(self, path: str) -> ValidationResult:
        """验证单个 SKILL.md 文件"""
        result = ValidationResult(path=path, valid=True)

        p = Path(path)
        # 根据文件名设置 file_format（SKILL.md 或 skill.yaml）
        result.file_format = p.name if p.is_file() else "SKILL.md"
        if not p.exists():
            result.valid = False
            result.add_issue(ValidationIssue(
                code=IssueCode.E304,
                severity=IssueSeverity.ERROR,
                message=f"文件不存在: {path}",
            ))
            return result

        try:
            content = p.read_text(encoding="utf-8")
        except Exception as e:
            result.valid = False
            result.add_issue(ValidationIssue(
                code=IssueCode.E304,
                severity=IssueSeverity.ERROR,
                message=f"读取文件失败: {e}",
            ))
            return result

        return self.validate_content(content, path)

    def validate_content(self, content: str, path: str = "<string>") -> ValidationResult:
        """验证内容字符串"""
        result = ValidationResult(path=path, valid=True)

        if not content.startswith("---"):
            result.valid = False
            result.add_issue(ValidationIssue(
                code=IssueCode.E301,
                severity=IssueSeverity.ERROR,
                message="SKILL.md 必须以 --- 开头",
            ))
            return result

        try:
            skill = parse_skill_md(content)
        except ValueError as e:
            result.valid = False
            result.add_issue(ValidationIssue(
                code=IssueCode.E302,
                severity=IssueSeverity.ERROR,
                message=str(e),
            ))
            return result

        # 填充结果
        result.skill_name = skill.name

        # 验证 markdown body
        self._validate_markdown_body(skill.markdown_body or "", result)

        # 验证 allowed-tools
        self._validate_allowed_tools(skill.allowed_tools, result)

        # 验证动态注入
        self._validate_dynamic_injection(skill.markdown_body or "", result)

        result.valid = result.error_count == 0
        return result

    def _validate_markdown_body(self, body: str, result: ValidationResult) -> None:
        """验证 markdown body 内容"""
        if not body:
            result.add_issue(ValidationIssue(
                code=IssueCode.W101,
                severity=IssueSeverity.WARNING,
                message="markdown body 为空",
                suggestion="添加 ## Instructions 节定义执行步骤",
            ))
            return

        if len(body) < 50:
            result.add_issue(ValidationIssue(
                code=IssueCode.W102,
                severity=IssueSeverity.WARNING,
                message=f"markdown body 过短（{len(body)} 字符），可能内容不足",
            ))

        # 建议包含 Instructions
        if not re.search(r"##\s*instructions", body, re.IGNORECASE):
            result.add_issue(ValidationIssue(
                code=IssueCode.W103,
                severity=IssueSeverity.SUGGESTION,
                message="建议包含 ## Instructions 节",
                suggestion="添加 ## Instructions 节定义执行步骤",
            ))

    def _validate_allowed_tools(self, tools: List[str], result: ValidationResult) -> None:
        """验证 allowed-tools 字段"""
        for tool in tools:
            if not tool.strip():
                continue

            # 检查危险工具
            if tool in DANGEROUS_TOOLS or tool.startswith("Bash") or tool.startswith("Write"):
                result.add_issue(ValidationIssue(
                    code=IssueCode.S101,
                    severity=IssueSeverity.WARNING,
                    message=f"工具 '{tool}' 为高危工具，请确保仅授予必要的权限",
                    suggestion="如非必需，建议移除 Bash/Write/Edit 以提高安全性",
                ))

    def _validate_dynamic_injection(self, body: str, result: ValidationResult) -> None:
        """验证 !`<command>` 动态注入"""
        for i, line in enumerate(body.split("\n"), 1):
            # 查找所有 !`...` 模式
            for match in re.finditer(r"!`([^`]*)`", line):
                command = match.group(1)

                if not command.strip():
                    result.add_issue(ValidationIssue(
                        code=IssueCode.E401,
                        severity=IssueSeverity.ERROR,
                        message="!`<command>` 命令不能为空",
                        line_number=i,
                    ))

                # 危险命令检查
                dangerous = [
                    (r"rm\s+-rf", "rm -rf 可能导致数据丢失"),
                    (r"drop\s+database", "DROP DATABASE 可能导致数据丢失"),
                ]
                for pattern, msg in dangerous:
                    if re.search(pattern, command):
                        result.add_issue(ValidationIssue(
                            code=IssueCode.S101,
                            severity=IssueSeverity.WARNING,
                            message=f"!`<command>` 包含潜在危险命令: {msg}",
                            line_number=i,
                        ))

            # 检查不完整的反引号
            if "!`" in line and line.count("`") % 2 != 0:
                result.add_issue(ValidationIssue(
                    code=IssueCode.E401,
                    severity=IssueSeverity.ERROR,
                    message="!`<command>` 缺少闭合反引号",
                    line_number=i,
                ))
