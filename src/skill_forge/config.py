"""
配置管理

支持两种配置方式：
1. skill-forge.yaml 配置文件
2. 环境变量（SKILL_FORGE_* 前缀）
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class LLMConfig:
    """LLM 配置"""
    # 测试阶段使用的本地代理
    test_endpoint: str = "http://127.0.0.1:15721"
    # 生产阶段由调用方注入，此处仅作占位
    production_endpoint: Optional[str] = None
    # 超时时间（秒）
    timeout: int = 60
    # 最大重试次数
    max_retries: int = 3


@dataclass
class ValidatorConfig:
    """验证器配置"""
    # YAML 缩进检查
    check_indentation: bool = True
    # Tab 检测
    detect_tabs: bool = True
    # 描述长度检查
    min_description_length: int = 10
    max_description_length: int = 1024
    # name 最大长度
    max_name_length: int = 64


@dataclass
class OptimizerConfig:
    """优化器配置"""
    # 默认优化级别 0-3
    default_level: int = 1
    # 自动修复级别
    auto_fix_level: int = 0
    # LLM 改进启用
    llm_enhancement: bool = False
    # 质量评分权重
    quality_weights: dict = field(default_factory=lambda: {
        "frontmatter": 0.25,
        "body": 0.35,
        "tools": 0.20,
        "security": 0.20,
    })


@dataclass
class Config:
    """主配置类"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    validator: ValidatorConfig = field(default_factory=ValidatorConfig)
    optimizer: OptimizerConfig = field(default_factory=OptimizerConfig)
    # 输出格式
    default_format: str = "yaml"
    # 详细输出
    verbose: bool = False

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        """从文件或环境变量加载配置"""
        config = cls()

        # 1. 从文件加载
        if config_path:
            path = Path(config_path)
        else:
            # 查找 skill-forge.yaml
            for candidate in ["skill-forge.yaml", ".skill-forge.yaml", "~/.skill-forge.yaml"]:
                p = Path(candidate).expanduser()
                if p.exists():
                    path = p
                    break
            else:
                path = None

        if path and path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            config = cls._from_dict(data)

        # 2. 从环境变量覆盖
        config._load_from_env()

        return config

    @classmethod
    def _from_dict(cls, data: dict) -> "Config":
        """从字典创建配置"""
        cfg = cls()

        if "llm" in data:
            for key, val in data["llm"].items():
                if hasattr(cfg.llm, key):
                    setattr(cfg.llm, key, val)

        if "validator" in data:
            for key, val in data["validator"].items():
                if hasattr(cfg.validator, key):
                    setattr(cfg.validator, key, val)

        if "optimizer" in data:
            for key, val in data["optimizer"].items():
                if hasattr(cfg.optimizer, key):
                    setattr(cfg.optimizer, key, val)

        if "default_format" in data:
            cfg.default_format = data["default_format"]
        if "verbose" in data:
            cfg.verbose = data["verbose"]

        return cfg

    def _load_from_env(self) -> None:
        """从环境变量加载配置覆盖"""
        prefix = "SKILL_FORGE_"

        # LLM 配置
        if v := os.getenv(f"{prefix}LLM_ENDPOINT"):
            self.llm.test_endpoint = v
        if v := os.getenv(f"{prefix}LLM_TIMEOUT"):
            self.llm.timeout = int(v)
        if v := os.getenv(f"{prefix}LLM_MAX_RETRIES"):
            self.llm.max_retries = int(v)

        # 验证器配置
        if v := os.getenv(f"{prefix}CHECK_INDENTATION"):
            self.validator.check_indentation = v.lower() == "true"

        # 输出配置
        if v := os.getenv(f"{prefix}FORMAT"):
            self.default_format = v
        if v := os.getenv(f"{prefix}VERBOSE"):
            self.verbose = v.lower() == "true"


# 全局配置实例
_config: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """获取全局配置（懒加载单例）"""
    global _config
    if _config is None:
        _config = Config.load(config_path)
    return _config


def reset_config() -> None:
    """重置全局配置（用于测试）"""
    global _config
    _config = None
