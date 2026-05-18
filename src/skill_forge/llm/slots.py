"""
LLM 集成槽位设计

设计原则：skill-forge 不管理 LLM 调用，只暴露接口槽位，由调用方注入。

使用场景：
1. nl_converter: 自然语言 → Skill（需要 LLM 生成 Definition）
2. optimizer.def_improver: Definition 改进（需要 LLM 重写）
3. optimizer.scorer: 质量评分增强（可选）

测试阶段：使用本地代理 http://127.0.0.1:15721
生产阶段：由 Agent 通过项目中间层 LLM API 注入
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TypeVar

from pydantic import BaseModel, Field


@dataclass
class LLMResponse:
    """LLM 响应"""
    content: str
    model: Optional[str] = None
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None


class LLMCallable(ABC):
    """
    LLM 调用接口抽象类

    由调用方实现，用于注入 LLM 能力。

    示例：
    ```python
    class MyLLM(LLMCallable):
        def complete(self, system: str, user: str) -> str:
            # 调用实际的 LLM
            return llm_client.chat(system, user)

        def complete_json(self, system: str, user: str, schema: dict) -> dict:
            response = self.complete(system, user)
            return json.loads(response)
    ```

    或者使用简单的函数：
    ```python
    def my_llm(system: str, user: str) -> str:
        return llm_client.complete(system, user)

    converter.convert(input, llm=my_llm)
    ```
    """

    @abstractmethod
    def complete(self, system: str, user: str) -> str:
        """
        生成文本补全

        Args:
            system: 系统提示词
            user: 用户提示词

        Returns:
            LLM 生成的文本
        """
        ...

    def complete_json(
        self,
        system: str,
        user: str,
        schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        生成 JSON 格式的响应

        Args:
            system: 系统提示词
            user: 用户提示词
            schema: JSON Schema（可选，用于验证）

        Returns:
            解析后的 JSON 对象
        """
        content = self.complete(system, user)

        # 尝试从 markdown 代码块中提取 JSON
        json_match = None
        for pattern in [r"```json\s*([\s\S]*?)\s*```", r"```\s*([\s\S]*?)\s*```"]:
            m = __import__("re").search(pattern, content)
            if m:
                json_match = m.group(1).strip()
                break

        if not json_match:
            json_match = content.strip()

        try:
            return json.loads(json_match)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM 返回的 JSON 格式无效: {e}\n原始内容: {content[:200]}")

    def complete_yaml(self, system: str, user: str) -> str:
        """
        生成 YAML 格式的响应

        默认实现：直接调用 complete 并期望返回 YAML 字符串

        Args:
            system: 系统提示词
            user: 用户提示词

        Returns:
            YAML 字符串
        """
        return self.complete(system, user)


# 类型别名：支持函数或 LLMCallable 实例
T = TypeVar("T")
LLMSlot = Callable[[str, str], str]  # (system, user) -> str
LLMSlotEx = LLMCallable  # 完整接口


@dataclass
class ConversionContext:
    """
    转化上下文

    存储转化过程中的元数据和状态
    """
    # 源类型
    source_type: str = ""  # "nl", "agent", "plugin", "workflow", "normalize"

    # 原始输入
    raw_input: str = ""

    # 源文件路径（如果是文件转化）
    source_path: Optional[str] = None

    # 目标路径（输出位置）
    target_path: Optional[str] = None

    # 转化选项
    options: Dict[str, Any] = field(default_factory=dict)

    # LLM 能力（由调用方注入）
    llm: Optional[LLMSlotEx] = None

    # 解析的中间结果
    intermediate: Dict[str, Any] = field(default_factory=dict)

    # 警告和提示
    warnings: List[str] = field(default_factory=list)

    def add_warning(self, msg: str) -> None:
        """添加警告"""
        self.warnings.append(msg)

    def has_llm(self) -> bool:
        """是否提供了 LLM 能力"""
        return self.llm is not None

    def require_llm(self, feature: str) -> None:
        """要求 LLM 能力，如果没有则抛出异常"""
        if not self.has_llm():
            raise ValueError(
                f"功能 '{feature}' 需要 LLM 能力。"
                "请通过 llm 参数提供 LLM 实现。"
                "示例: converter.convert(input, llm=my_llm_function)"
            )


@dataclass
class OptimizationContext:
    """
    优化上下文

    存储优化过程中的元数据和状态
    """
    # 优化级别 0-3
    level: int = 1

    # 是否自动修复
    auto_fix: bool = False

    # 质量分数（优化前）
    original_score: Optional[float] = None

    # 质量分数（优化后）
    optimized_score: Optional[float] = None

    # LLM 能力（可选）
    llm: Optional[LLMSlotEx] = None

    # 优化记录
    changes: List["OptimizationChange"] = field(default_factory=list)

    def add_change(
        self,
        field_name: str,
        original: str,
        optimized: str,
        reason: str,
    ) -> None:
        """记录一次优化变更"""
        self.changes.append(OptimizationChange(
            field_name=field_name,
            original=original,
            optimized=optimized,
            reason=reason,
        ))

    def has_llm(self) -> bool:
        """是否提供了 LLM 能力"""
        return self.llm is not None


@dataclass
class OptimizationChange:
    """优化变更记录"""
    field_name: str
    original: str
    optimized: str
    reason: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "field": self.field_name,
            "original": self.original[:50] + "..." if len(self.original) > 50 else self.original,
            "optimized": self.optimized[:50] + "..." if len(self.optimized) > 50 else self.optimized,
            "reason": self.reason,
        }
