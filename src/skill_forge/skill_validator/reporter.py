"""
验证报告生成器

生成 JSON/Markdown/YAML 格式的验证报告
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..models.validation import ValidationResult, BatchValidationResult


class Reporter:
    """
    验证报告生成器

    支持多种输出格式：JSON、Markdown、YAML
    """

    def __init__(self, format: str = "yaml"):
        """
        初始化报告生成器

        Args:
            format: 输出格式 (json|yaml|markdown)
        """
        self.format = format.lower()

    def generate(self, result: ValidationResult) -> str:
        """生成单个验证结果的报告"""
        if self.format == "json":
            return self._generate_json(result)
        elif self.format == "markdown":
            return self._generate_markdown(result)
        elif self.format == "yaml":
            return self._generate_yaml(result)
        else:
            return self._generate_text(result)

    def generate_batch(self, batch: BatchValidationResult) -> str:
        """生成批量验证结果的报告"""
        if self.format == "json":
            return self._generate_batch_json(batch)
        elif self.format == "markdown":
            return self._generate_batch_markdown(batch)
        elif self.format == "yaml":
            return self._generate_batch_yaml(batch)
        else:
            return self._generate_batch_text(batch)

    def _generate_json(self, result: ValidationResult) -> str:
        """生成 JSON 格式报告"""
        return json.dumps(result.to_dict(), ensure_ascii=False, indent=2)

    def _generate_markdown(self, result: ValidationResult) -> str:
        """生成 Markdown 格式报告"""
        lines = [
            "# Skill 验证报告",
            "",
            f"**文件**: `{result.path}`",
            f"**文件格式**: {result.file_format}",
            f"**Skill 名称**: {result.skill_name or 'N/A'}",
            f"**验证状态**: {'✅ 通过' if result.valid else '❌ 未通过'}",
            "",
        ]

        # 迁移提示
        if result.migration_count > 0:
            lines.append(f"⚠️ **迁移建议**: {result.migration_count} 项")
            lines.append("")

        lines.append(f"问题统计: **{result.error_count}** 错误, **{result.warning_count}** 警告, **{result.suggestion_count}** 建议")
        lines.append("")

        if result.errors:
            lines.append("## 错误")
            lines.append("")
            for err in result.errors:
                lines.append(f"- ❌ `{err.code.value}` {err.message}")
                if err.line_number:
                    lines.append(f"  - 行号: {err.line_number}")
                if err.suggestion:
                    lines.append(f"  - 建议: {err.suggestion}")
            lines.append("")

        if result.warnings:
            lines.append("## 警告")
            lines.append("")
            for warn in result.warnings:
                lines.append(f"- ⚠️ `{warn.code.value}` {warn.message}")
                if warn.suggestion:
                    lines.append(f"  - 建议: {warn.suggestion}")
            lines.append("")

        if result.suggestions:
            lines.append("## 建议")
            lines.append("")
            for sug in result.suggestions:
                lines.append(f"- 💡 `{sug.code.value}` {sug.message}")
            lines.append("")

        # 迁移建议
        if result.migrations:
            lines.append("## 迁移建议")
            lines.append("")
            lines.append("以下问题与旧版 skill.yaml 格式相关，建议迁移到 SKILL.md：")
            lines.append("")
            for mig in result.migrations:
                lines.append(f"- 🔄 `{mig.code.value}` {mig.message}")
                if mig.suggestion:
                    lines.append(f"  - 建议: {mig.suggestion}")
            lines.append("")
            lines.append(f"运行 `skill-forge migrate {result.path}` 进行迁移。")
            lines.append("")

        return "\n".join(lines)

    def _generate_yaml(self, result: ValidationResult) -> str:
        """生成 YAML 格式报告"""
        import yaml

        data = {
            "path": result.path,
            "file_format": result.file_format,
            "skill_name": result.skill_name,
            "valid": result.valid,
            "summary": {
                "errors": result.error_count,
                "warnings": result.warning_count,
                "suggestions": result.suggestion_count,
                "migrations": result.migration_count,
            },
        }

        if result.errors:
            data["errors"] = [
                {
                    "code": e.code.value,
                    "message": e.message,
                    "line_number": e.line_number,
                    "suggestion": e.suggestion,
                }
                for e in result.errors
            ]

        if result.warnings:
            data["warnings"] = [
                {
                    "code": w.code.value,
                    "message": w.message,
                    "line_number": w.line_number,
                    "suggestion": w.suggestion,
                }
                for w in result.warnings
            ]

        if result.suggestions:
            data["suggestions"] = [
                {
                    "code": s.code.value,
                    "message": s.message,
                }
                for s in result.suggestions
            ]

        if result.migrations:
            data["migrations"] = [
                {
                    "code": m.code.value,
                    "message": m.message,
                    "suggestion": m.suggestion,
                }
                for m in result.migrations
            ]

        return yaml.dump(data, allow_unicode=True, default_flow_style=False, indent=2)

    def _generate_text(self, result: ValidationResult) -> str:
        """生成纯文本格式报告"""
        lines = [
            "=" * 60,
            "Skill 验证报告",
            "=" * 60,
            f"文件: {result.path}",
            f"文件格式: {result.file_format}",
            f"Skill 名称: {result.skill_name or 'N/A'}",
            f"状态: {'✅ 通过' if result.valid else '❌ 未通过'}",
            f"问题: {result.error_count} 错误, {result.warning_count} 警告, {result.suggestion_count} 建议",
            "=" * 60,
            "",
        ]

        if result.errors:
            lines.append("【错误】")
            for err in result.errors:
                loc = f"(行 {err.line_number})" if err.line_number else ""
                lines.append(f"  ❌ {err.code.value} {loc} {err.message}")
                if err.suggestion:
                    lines.append(f"     → {err.suggestion}")
            lines.append("")

        if result.warnings:
            lines.append("【警告】")
            for warn in result.warnings:
                loc = f"(行 {warn.line_number})" if warn.line_number else ""
                lines.append(f"  ⚠️  {warn.code.value} {loc} {warn.message}")
                if warn.suggestion:
                    lines.append(f"     → {warn.suggestion}")
            lines.append("")

        if result.suggestions:
            lines.append("【建议】")
            for sug in result.suggestions:
                lines.append(f"  💡 {sug.code.value} {sug.message}")

        if result.migrations:
            lines.append("")
            lines.append("【迁移建议】")
            for mig in result.migrations:
                lines.append(f"  🔄 {mig.code.value} {mig.message}")

        return "\n".join(lines)

    def _generate_batch_json(self, batch: BatchValidationResult) -> str:
        """生成批量 JSON 报告"""
        return json.dumps(batch.to_dict(), ensure_ascii=False, indent=2)

    def _generate_batch_markdown(self, batch: BatchValidationResult) -> str:
        """生成批量 Markdown 报告"""
        lines = [
            "# Skill 批量验证报告",
            "",
            f"**总计**: {batch.total} 个文件",
            f"**通过**: ✅ {batch.passed}",
            f"**失败**: ❌ {batch.failed}",
            f"**通过率**: {batch.pass_rate:.1f}%",
            "",
        ]

        if batch.migration_needed > 0:
            lines.append(f"⚠️ **需要迁移**: {batch.migration_needed} 个文件（旧版 skill.yaml 格式）")
            lines.append("")

        for result in batch.results:
            status = "✅" if result.valid else "❌"
            fmt = result.file_format
            lines.append(f"## {status} `{result.path}` [{fmt}]")
            lines.append("")

            if result.errors:
                lines.append("**错误:**")
                for err in result.errors:
                    lines.append(f"- ❌ `{err.code.value}` {err.message}")
                lines.append("")

            if result.warnings:
                lines.append("**警告:**")
                for warn in result.warnings:
                    lines.append(f"- ⚠️ `{warn.code.value}` {warn.message}")
                lines.append("")

            if result.migrations:
                lines.append("**迁移建议:**")
                for mig in result.migrations:
                    lines.append(f"- 🔄 `{mig.code.value}` {mig.message}")
                lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def _generate_batch_yaml(self, batch: BatchValidationResult) -> str:
        """生成批量 YAML 报告"""
        import yaml

        data = {
            "total": batch.total,
            "passed": batch.passed,
            "failed": batch.failed,
            "migration_needed": batch.migration_needed,
            "pass_rate": f"{batch.pass_rate:.1f}%",
            "results": [
                {
                    "path": r.path,
                    "file_format": r.file_format,
                    "valid": r.valid,
                    "skill_name": r.skill_name,
                    "errors": [e.code.value for e in r.errors],
                    "warnings": [w.code.value for w in r.warnings],
                    "migrations": [m.code.value for m in r.migrations],
                }
                for r in batch.results
            ],
        }

        return yaml.dump(data, allow_unicode=True, default_flow_style=False, indent=2)

    def _generate_batch_text(self, batch: BatchValidationResult) -> str:
        """生成批量纯文本报告"""
        lines = [
            "=" * 60,
            "Skill 批量验证报告",
            "=" * 60,
            f"总计: {batch.total} | 通过: {batch.passed} | 失败: {batch.failed} | 通过率: {batch.pass_rate:.1f}%",
            "=" * 60,
            "",
        ]

        for result in batch.results:
            status = "✅" if result.valid else "❌"
            lines.append(f"{status} {result.path} [{result.file_format}]")
            if result.skill_name:
                lines.append(f"   名称: {result.skill_name}")
            if result.errors:
                lines.append(f"   错误: {', '.join(e.code.value for e in result.errors)}")
            if result.warnings:
                lines.append(f"   警告: {', '.join(w.code.value for w in result.warnings)}")
            if result.migrations:
                lines.append(f"   迁移: {', '.join(m.code.value for m in result.migrations)}")
            lines.append("")

        return "\n".join(lines)


def save_report(content: str, path: str) -> None:
    """保存报告到文件"""
    Path(path).write_text(content, encoding="utf-8")


def print_report(content: str) -> None:
    """打印报告到标准输出"""
    print(content)
