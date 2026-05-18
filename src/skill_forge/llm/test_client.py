"""
测试用 LLM 客户端

连接到本地代理 http://127.0.0.1:15721（OpenAI 兼容 / Anthropic 兼容）

用途：开发阶段验证功能，不用于生产环境
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from .slots import LLMCallable, LLMResponse


class TestLLMClient(LLMCallable):
    """
    测试用 LLM 客户端

    连接到本地代理进行测试（支持 OpenAI 兼容格式）

    用法：
    ```python
    client = TestLLMClient(endpoint="http://127.0.0.1:15721")
    response = client.complete("system prompt", "user message")
    ```
    """

    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:15721",
        timeout: int = 60,
        model: Optional[str] = None,
    ):
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout
        self.model = model

    def complete(self, system: str, user: str) -> str:
        """
        发送补全请求到本地代理（OpenAI 兼容格式）

        Args:
            system: 系统提示词
            user: 用户提示词

        Returns:
            LLM 生成的文本

        Raises:
            ConnectionError: 无法连接到代理
            RuntimeError: 请求失败
        """
        # 优先使用 Anthropic SDK（支持 proxy managed auth）
        try:
            import anthropic
            # 绕过系统代理
            env_backup = {}
            for key in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "all_proxy", "ALL_PROXY", "no_proxy", "NO_PROXY"]:
                env_backup[key] = os.environ.pop(key, None)

            try:
                client = anthropic.Anthropic(
                    base_url=self.endpoint,
                    max_retries=0,
                )
                msg = client.messages.create(
                    model=self.model or "claude-sonnet-4-20250514",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": user}],
                    system=system,
                )
                return msg.content[0].text
            finally:
                # 恢复环境变量
                for key, val in env_backup.items():
                    if val is not None:
                        os.environ[key] = val
        except ImportError:
            pass
        except Exception as e:
            # 回退到 requests
            pass

        # 回退到 requests（OpenAI 兼容格式）
        import requests

        payload = {
            "model": self.model or "default",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": 2000,
            "temperature": 0.3,
        }

        try:
            response = requests.post(
                f"{self.endpoint}/v1/chat/completions",
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise RuntimeError(f"LLM 代理错误: {data['error']}")

            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            return ""

        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"无法连接到 LLM 代理 {self.endpoint}。"
                "请确保本地代理正在运行。"
            )
        except requests.exceptions.Timeout:
            raise RuntimeError(f"LLM 代理请求超时（{self.timeout}秒）")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"LLM 代理请求失败: {e}")

    def complete_json(
        self,
        system: str,
        user: str,
        schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        发送 JSON 补全请求

        Args:
            system: 系统提示词
            user: 用户提示词
            schema: JSON Schema（可选）

        Returns:
            解析后的 JSON 对象
        """
        payload = {
            "model": self.model or "default",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": 2000,
            "temperature": 0.3,
        }
        if schema:
            payload["schema"] = schema

        try:
            response = requests.post(
                f"{self.endpoint}/v1/chat/completions",
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise RuntimeError(f"LLM 代理错误: {data['error']}")

            choices = data.get("choices", [])
            content = choices[0].get("message", {}).get("content", "") if choices else ""

            # 尝试从 markdown 代码块中提取 JSON
            import re
            for pattern in [r"```json\s*([\s\S]*?)\s*```", r"```\s*([\s\S]*?)\s*```"]:
                m = re.search(pattern, content)
                if m:
                    content = m.group(1).strip()
                    break

            return json.loads(content)

        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"无法连接到 LLM 代理 {self.endpoint}。"
                "请确保本地代理正在运行。"
            )
        except requests.exceptions.Timeout:
            raise RuntimeError(f"LLM 代理请求超时（{self.timeout}秒）")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"LLM 代理请求失败: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM 返回的 JSON 格式无效: {e}")

    def health_check(self) -> bool:
        """
        检查代理是否可用

        Returns:
            是否可用
        """
        try:
            response = requests.get(
                f"{self.endpoint}/v1/models",
                timeout=5,
            )
            return response.status_code == 200
        except Exception:
            return False


def create_test_llm(endpoint: str = "http://127.0.0.1:15721") -> TestLLMClient:
    """
    创建测试用 LLM 客户端的便捷函数

    Args:
        endpoint: 代理端点

    Returns:
        TestLLMClient 实例
    """
    return TestLLMClient(endpoint=endpoint)
