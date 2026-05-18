"""
YAML 工具函数

提供 YAML 解析、格式化、验证等功能
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


class YAMLFormatError(Exception):
    """YAML 格式错误"""
    def __init__(self, message: str, line_number: Optional[int] = None):
        self.message = message
        self.line_number = line_number
        super().__init__(self._format())

    def _format(self) -> str:
        if self.line_number:
            return f"YAML 格式错误（第 {self.line_number} 行）: {self.message}"
        return f"YAML 格式错误: {self.message}"


@dataclass
class FormatIssue:
    """格式问题"""
    line_number: int
    column: int
    message: str
    severity: str = "error"


@dataclass
class ParseResult:
    """解析结果"""
    data: Optional[Dict[str, Any]] = None
    raw_content: str = ""
    line_offsets: List[int] = field(default_factory=list)  # 每行的字节偏移量
    format_issues: List[FormatIssue] = field(default_factory=list)
    yaml_error: Optional[str] = None
    yaml_valid: bool = True

    @property
    def has_format_issues(self) -> bool:
        return len(self.format_issues) > 0


def safe_load(path: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    安全加载 YAML 文件

    Args:
        path: 文件路径

    Returns:
        (data, error): 解析后的数据或错误信息
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data, None
    except yaml.YAMLError as e:
        return None, str(e)
    except FileNotFoundError:
        return None, f"文件不存在: {path}"
    except Exception as e:
        return None, f"读取文件失败: {e}"


def safe_dump(data: Dict[str, Any], path: Optional[str] = None) -> str:
    """
    安全保存 YAML 文件

    Args:
        data: 要保存的数据
        path: 文件路径（可选）

    Returns:
        YAML 字符串
    """

    class LiteralStr(str):
        """用于强制 literal block style 的字符串子类"""
        pass

    def literal_str_representer(dumper, value):
        return dumper.represent_scalar('tag:yaml.org,2002:str', str(value), style='|')

    yaml.add_representer(LiteralStr, literal_str_representer)

    result = yaml.dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        indent=2,
        width=120,
    )
    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write(result)
    return result


def parse_yaml_content(content: str) -> ParseResult:
    """
    解析 YAML 内容并进行格式检查

    Args:
        content: YAML 内容

    Returns:
        ParseResult 对象
    """
    result = ParseResult(raw_content=content)

    # 构建行偏移表
    offset = 0
    for line in content.split("\n"):
        result.line_offsets.append(offset)
        offset += len(line) + 1  # +1 for newline

    # 检查格式问题
    result.format_issues = check_yaml_format(content)

    # 解析 YAML
    try:
        data = yaml.safe_load(content)
        result.data = data
    except yaml.YAMLError as e:
        result.yaml_valid = False
        result.yaml_error = str(e)

        # 尝试提取行号
        if hasattr(e, "problem_mark") and e.problem_mark:
            result.yaml_error += f" (第 {e.problem_mark.line + 1} 行)"

    return result


def check_yaml_format(content: str) -> List[FormatIssue]:
    """
    检查 YAML 格式问题

    Args:
        content: YAML 内容

    Returns:
        格式问题列表
    """
    issues: List[FormatIssue] = []
    lines = content.split("\n")

    for line_num, line in enumerate(lines, 1):
        col = len(line) - len(line.lstrip())
        indent = col

        # E302: 检测 Tab 缩进
        if "\t" in line and not line.strip().startswith("#"):
            issues.append(FormatIssue(
                line_number=line_num,
                column=1,
                message="使用了 Tab 缩进，应使用 2 空格",
                severity="error",
            ))

        # E303: 检查缩进是否为 2 的倍数
        stripped = line.lstrip()
        if stripped and indent > 0:
            if indent % 2 != 0:
                issues.append(FormatIssue(
                    line_number=line_num,
                    column=indent,
                    message=f"缩进应为 2 的倍数，当前为 {indent} 空格",
                    severity="error",
                ))

        # E304: 引号检查（区分撇号和引号）
        # 在 YAML 中，撇号（'s, n't, 're 等）不应被视为引号对
        # 跳过包含 | 或 > 的行（可能是多行字符串）
        if "|" not in line and ">" not in line and not stripped.startswith("#"):
            in_single = False
            in_double = False
            j = 0
            while j < len(line):
                char = line[j]

                if char == "'":
                    before_is_alpha = (j > 0 and line[j - 1].isalpha())
                    after_is_alpha = (j + 1 < len(line) and line[j + 1].isalpha())
                    after_is_followed_by_quote = (j + 1 < len(line) and line[j + 1] == "'")
                    after_is_boundary = (j + 1 >= len(line)) or (
                        not line[j + 1].isalpha() and line[j + 1] not in ("_", "-")
                    )
                    is_contraction = (before_is_alpha and after_is_alpha) or (
                        in_single and before_is_alpha and after_is_boundary and not after_is_followed_by_quote
                    )

                    if is_contraction:
                        j += 1
                        continue

                    if in_single and j + 1 < len(line) and line[j + 1] == "'":
                        j += 2
                        continue

                    if not in_double:
                        in_single = not in_single
                elif char == '"' and not in_single:
                    in_double = not in_double
                elif char == "\\" and (in_single or in_double):
                    if j + 1 < len(line):
                        j += 2
                        continue
                j += 1

            if in_single or in_double:
                issues.append(FormatIssue(
                    line_number=line_num,
                    column=1,
                    message="引号未闭合",
                    severity="error",
                ))

        # E305: 检查列表项格式
        if stripped and not stripped.startswith("#"):
            if stripped.startswith("-"):
                after_dash = stripped[1:].lstrip()
                if after_dash and not after_dash.startswith('"') and not after_dash.startswith("'"):
                    pass

    return issues


def get_line_at_offset(content: str, offset: int) -> Tuple[int, int]:
    """
    获取指定偏移量对应的行号和列号

    Args:
        content: 内容
        offset: 字节偏移量

    Returns:
        (行号, 列号)（从 1 开始）
    """
    lines = content[:offset].split("\n")
    line_num = len(lines)
    col = len(lines[-1]) + 1 if lines else 1
    return line_num, col


def normalize_yaml(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    规范化 YAML 数据

    - 移除空值
    - 标准化列表
    - 移除注释
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if value is not None:
                normalized = normalize_yaml(value)
                if normalized is not None:
                    result[key] = normalized
        return result
    elif isinstance(data, list):
        return [normalize_yaml(item) for item in data if item is not None]
    elif isinstance(data, str) and not data.strip():
        return None
    return data
