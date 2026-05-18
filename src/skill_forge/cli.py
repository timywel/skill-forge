"""
Skill Forge CLI

命令行接口实现
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .config import get_config
from .models.validation import BatchValidationResult, ValidationResult
from .skill_validator.validator import SkillValidator
from .skill_validator.reporter import Reporter
from .skill_converter.nl_converter import NLConverter
from .skill_converter.agent_converter import AgentConverter
from .skill_converter.normalize_converter import NormalizeConverter
from .skill_optimizer.optimizer import SkillOptimizer
from .llm.test_client import TestLLMClient
from .utils.yaml_utils import safe_load, safe_dump


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog="skill-forge",
        description="Skill 规范检验、转换与优化工具链",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # 全局选项
    parser.add_argument(
        "--config", "-c",
        help="配置文件路径",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["json", "yaml", "markdown"],
        default="yaml",
        help="输出格式（默认: yaml）",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出",
    )
    parser.add_argument(
        "--output", "-o",
        help="输出文件路径（默认输出到标准输出）",
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # ============================================================
    # validate 命令
    # ============================================================
    validate_parser = subparsers.add_parser(
        "validate",
        help="验证 SKILL.md 或 skill.yaml 文件",
    )
    validate_parser.add_argument(
        "path",
        help="SKILL.md/skill.yaml 文件路径或目录（批量模式）",
    )
    validate_parser.add_argument(
        "--batch", "-b",
        action="store_true",
        help="批量验证目录中的所有 skill 文件",
    )

    # ============================================================
    # convert 命令
    # ============================================================
    convert_parser = subparsers.add_parser(
        "convert",
        help="转换各种格式为标准 SKILL.md",
    )
    convert_parser.add_argument(
        "type",
        choices=["nl", "agent", "normalize", "migrate"],
        help="转换类型",
    )
    convert_parser.add_argument(
        "--input", "-i",
        required=True,
        help="输入路径或内容",
    )
    convert_parser.add_argument(
        "--output", "-o",
        help="输出文件路径（默认输出到标准输出）",
    )
    convert_parser.add_argument(
        "--name", "-n",
        help="生成的 skill 名称",
    )
    convert_parser.add_argument(
        "--argument-hint", "-a",
        help="参数提示，如 '[issue-number]' 或 '[filename]'",
    )
    convert_parser.add_argument(
        "--tags",
        help="建议的标签（逗号分隔）",
    )
    convert_parser.add_argument(
        "--test-llm",
        action="store_true",
        help="使用测试用 LLM（nl 转换模式）",
    )

    # v3.1.0 新增：多语言 + 元数据参数
    convert_parser.add_argument(
        "--locale",
        choices=["en", "zh", "both"],
        default="both",
        help="生成语言版本（默认: both）",
    )
    convert_parser.add_argument(
        "--no-zh",
        action="store_true",
        help="跳过 SKILL.zh.md 生成",
    )
    convert_parser.add_argument(
        "--no-meta",
        action="store_true",
        help="跳过 skill.meta.yaml 生成",
    )
    convert_parser.add_argument(
        "--category",
        help="覆盖自动推断的 category",
    )
    convert_parser.add_argument(
        "--cognitive-phase",
        help="覆盖自动推断的 cognitive_phase",
    )
    convert_parser.add_argument(
        "--layer",
        choices=["system", "user"],
        default="system",
        help="覆盖 layer（默认: system）",
    )

    # ============================================================
    # optimize 命令
    # ============================================================
    optimize_parser = subparsers.add_parser(
        "optimize",
        help="优化 SKILL.md 质量",
    )
    optimize_parser.add_argument(
        "path",
        help="SKILL.md 文件路径",
    )
    optimize_parser.add_argument(
        "--level", "-l",
        type=int,
        choices=[0, 1, 2, 3],
        default=1,
        help="优化级别（0: 仅分析, 1: 自动修复, 2: 建议, 3: LLM 增强）",
    )
    optimize_parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="自动修复问题",
    )
    optimize_parser.add_argument(
        "--test-llm",
        action="store_true",
        help="使用测试用 LLM（level 3）",
    )

    # ============================================================
    # quality 命令
    # ============================================================
    quality_parser = subparsers.add_parser(
        "quality",
        help="评估 SKILL.md 质量",
    )
    quality_parser.add_argument(
        "path",
        help="SKILL.md 文件路径",
    )

    # ============================================================
    # migrate 命令（新增）
    # ============================================================
    migrate_parser = subparsers.add_parser(
        "migrate",
        help="将旧版 skill.yaml 迁移到 SKILL.md",
    )
    migrate_parser.add_argument(
        "path",
        help="skill.yaml 文件路径",
    )
    migrate_parser.add_argument(
        "--output", "-o",
        help="输出文件路径（默认输出到标准输出）",
    )
    migrate_parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="自动修复并保存",
    )

    return parser


def cmd_validate(args: argparse.Namespace) -> int:
    """执行验证命令"""
    config = get_config(args.config)
    validator = SkillValidator()
    reporter = Reporter(format=args.format)

    if Path(args.path).is_dir():
        # 批量验证
        batch = _validate_batch(args.path, validator)
        content = reporter.generate_batch(batch)

        if args.verbose:
            print(f"批量验证: {batch.total} 个文件")
            print(f"通过: {batch.passed}, 失败: {batch.failed}")
            if batch.migration_needed > 0:
                print(f"需要迁移: {batch.migration_needed}")
    else:
        # 单个文件验证
        result = validator.validate_file(args.path)
        content = reporter.generate(result)

        if args.verbose:
            status = "✅ 通过" if result.valid else "❌ 未通过"
            fmt = result.file_format
            print(f"验证 {args.path} [{fmt}]: {status}")

    _output(content, args)

    return 0


def cmd_convert(args: argparse.Namespace) -> int:
    """执行转换命令"""
    output_path = args.output

    try:
        if args.type == "nl":
            # 自然语言转换
            llm = None
            if args.test_llm:
                try:
                    llm = TestLLMClient()
                    if not llm.health_check():
                        print("⚠️  警告: 测试用 LLM 不可用，将使用模拟模式", file=sys.stderr)
                        llm = None
                except Exception:
                    print("⚠️  警告: 无法连接到测试用 LLM", file=sys.stderr)
                    llm = None

            converter = NLConverter()
            result = converter.convert(
                args.input,
                llm=llm,
                argument_hint=args.argument_hint,
                tags=_parse_tags(args.tags),
            )
            content = result.get("skill_md", "")

        elif args.type == "agent":
            # Agent 转换
            converter = AgentConverter()
            result = converter.convert(args.input, name=args.name)
            content = result.get("skill_md", "")

        elif args.type in ("normalize", "migrate"):
            # 标准化/迁移转换
            converter = NormalizeConverter()
            result = converter.convert(args.input)
            base_skill = converter._create_base_skill(result)
            content = converter._skill_to_md(base_skill)

        else:
            print(f"❌ 不支持的转换类型: {args.type}", file=sys.stderr)
            return 1

        # 输出结果
        if output_path:
            Path(output_path).write_text(content, encoding="utf-8")
            print(f"✅ 已保存到: {output_path}")
        else:
            _output(content, args)

        return 0

    except Exception as e:
        print(f"❌ 转换失败: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_optimize(args: argparse.Namespace) -> int:
    """执行优化命令"""
    optimizer = SkillOptimizer()

    # 获取 LLM
    llm = None
    if args.level >= 3 or args.test_llm:
        try:
            llm = TestLLMClient()
            if not llm.health_check():
                print("⚠️  警告: 测试用 LLM 不可用", file=sys.stderr)
                llm = None
        except Exception:
            print("⚠️  警告: 无法连接到测试用 LLM", file=sys.stderr)
            llm = None

    try:
        report = optimizer.optimize(
            args.path,
            level=args.level,
            auto_fix=args.auto_fix,
            llm=llm,
        )

        # 输出报告
        import json
        report_dict = report.to_dict()

        if args.format == "json":
            content = json.dumps(report_dict, ensure_ascii=False, indent=2)
        elif args.format == "markdown":
            content = _format_quality_markdown(report_dict)
        else:
            content = _format_yaml(report_dict)

        _output(content, args)

        if report.optimization_changes:
            print(f"\n📊 质量评分: {report.overall_score:.1f}/100")
            print(f"🔧 完成 {len(report.optimization_changes)} 项优化")
        elif report.migration_needed:
            print(f"\n⚠️  需要迁移: {args.path} 使用旧版 skill.yaml 格式")
            print(f"💡 使用 'skill-forge migrate {args.path}' 进行迁移")

        return 0

    except Exception as e:
        print(f"❌ 优化失败: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_quality(args: argparse.Namespace) -> int:
    """执行质量评估命令"""
    optimizer = SkillOptimizer()

    try:
        report = optimizer.analyze(args.path)

        # 输出报告
        import json
        report_dict = report.to_dict()

        if args.format == "json":
            content = json.dumps(report_dict, ensure_ascii=False, indent=2)
        elif args.format == "markdown":
            content = _format_quality_markdown(report_dict)
        else:
            content = _format_yaml(report_dict)

        _output(content, args)

        return 0

    except Exception as e:
        print(f"❌ 质量评估失败: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_migrate(args: argparse.Namespace) -> int:
    """执行迁移命令"""
    output_path = args.output

    try:
        converter = NormalizeConverter()
        result = converter.convert(args.path)
        base_skill = converter._create_base_skill(result)
        content = converter._skill_to_md(base_skill)

        if args.auto_fix and not output_path:
            # 自动保存
            new_path = args.path.replace(".yaml", ".md").replace(".yml", ".md")
            Path(new_path).write_text(content, encoding="utf-8")
            print(f"✅ 已迁移并保存到: {new_path}")
        elif output_path:
            Path(output_path).write_text(content, encoding="utf-8")
            print(f"✅ 已迁移并保存到: {output_path}")
        else:
            _output(content, args)

        return 0

    except Exception as e:
        print(f"❌ 迁移失败: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


# ============================================================
# 辅助函数
# ============================================================

def _validate_batch(dir_path: str, validator: SkillValidator) -> BatchValidationResult:
    """批量验证目录中的所有 skill 文件"""
    batch = BatchValidationResult()

    path = Path(dir_path)
    if not path.is_dir():
        return batch

    for skill_file in path.rglob("SKILL.md"):
        batch.total += 1
        result = validator.validate_file(str(skill_file))
        batch.results.append(result)
        if result.valid:
            batch.passed += 1
        else:
            batch.failed += 1
        # 检查是否需要迁移
        if result.file_format == "skill.yaml":
            batch.migration_needed += 1

    # 也检查旧版 skill.yaml
    for yaml_file in path.rglob("skill.yaml"):
        # 跳过已经是 SKILL.md 的同名文件
        md_path = yaml_file.with_suffix(".md")
        if md_path.exists():
            continue
        batch.total += 1
        result = validator.validate_file(str(yaml_file))
        batch.results.append(result)
        if result.valid:
            batch.passed += 1
        else:
            batch.failed += 1
        batch.migration_needed += 1

    return batch


def _format_yaml(data: dict) -> str:
    """格式化为 YAML"""
    return safe_dump(data)


def _format_quality_markdown(report: dict) -> str:
    """格式化质量报告为 Markdown"""
    lines = [
        "# Skill 质量报告",
        "",
        f"**Skill 名称**: {report['skill_name']}",
        f"**文件路径**: {report['file_path']}",
        f"**文件格式**: {report['file_format']}",
        f"**总分**: {report['overall_score']:.1f}/100",
        "",
        "## 各维度评分",
        "",
    ]

    for dim in report.get("dimensions", []):
        score = dim["score"]
        bar = "█" * int(score / 10) + "░" * (10 - int(score / 10))
        lines.append(f"| {dim['name']:<15} | {bar} | {score:>5.1f} |")
        if dim.get("issues"):
            for issue in dim["issues"][:3]:
                lines.append(f"  - ⚠️  {issue}")
        lines.append("")

    if report.get("suggestions"):
        lines.append("## 优化建议")
        lines.append("")
        for suggestion in report["suggestions"]:
            lines.append(f"- {suggestion}")
        lines.append("")

    if report.get("migration_needed"):
        lines.append("## ⚠️ 迁移提示")
        lines.append("")
        lines.append(f"检测到旧版 skill.yaml 格式，建议迁移到 SKILL.md。")
        lines.append(f"运行 `skill-forge migrate {report['file_path']}` 进行迁移。")
        lines.append("")

    return "\n".join(lines)


def _parse_tags(tags_str: Optional[str]) -> List[str]:
    """解析逗号分隔的标签"""
    if not tags_str:
        return []
    return [t.strip() for t in tags_str.split(",") if t.strip()]


def _output(content: str, args: argparse.Namespace) -> None:
    """输出内容"""
    if args.output:
        Path(args.output).write_text(content, encoding="utf-8")
        print(f"✅ 已保存到: {args.output}")
    else:
        print(content)


def main(argv: Optional[List[str]] = None) -> int:
    """CLI 入口函数"""
    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    # 根据命令调用对应的处理函数
    commands = {
        "validate": cmd_validate,
        "convert": cmd_convert,
        "optimize": cmd_optimize,
        "quality": cmd_quality,
        "migrate": cmd_migrate,
    }

    handler = commands.get(args.command)
    if handler:
        try:
            return handler(args)
        except Exception as e:
            print(f"❌ 错误: {e}", file=sys.stderr)
            if getattr(args, "verbose", False):
                import traceback
                traceback.print_exc()
            return 1

    return 0
