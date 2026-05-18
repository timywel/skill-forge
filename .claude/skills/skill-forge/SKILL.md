---
name: skill-forge
description: Skill 规范检验、转换与优化工具。验证 SKILL.md 是否符合 Agent Skills 标准，转换各种格式为标准 SKILL.md，评估和优化 Skill 质量。
license: MIT
compatibility: Requires Python 3.10+
metadata:
  author: AI Product Lab
  version: "0.1.0"
allowed-tools: Read Glob Grep Bash Edit Write
---

# Skill Forge

Skill 规范检验、转换与优化工具链。

规范遵循 [Agent Skills Specification](https://agentskills.io/specification)。

## 功能

- **Validator（验证器）**：验证 SKILL.md 是否符合 Agent Skills 标准
- **Converter（转化器）**：将 Agent、自然语言转换为标准 SKILL.md
- **Optimizer（优化器）**：分析 Skill 质量并提供优化建议

## 使用方法

```bash
# 验证单个文件
skill-forge validate <path>

# 批量验证
skill-forge validate --batch <dir>

# 自然语言转换
skill-forge convert nl --input "创建一个代码审查技能"

# Agent 转换
skill-forge convert agent --input <path>

# 质量评分
skill-forge quality <path>

# 优化
skill-forge optimize <path> --level 2
```

## 项目结构

```
skill-forge/
├── src/skill_forge/           # 源代码
│   ├── skill_validator/       # 验证器
│   ├── skill_converter/       # 转化器
│   ├── skill_optimizer/       # 优化器
│   └── models/                # 数据模型
└── tests/                     # 测试
```

## LLM 集成

skill-forge 不管理 LLM 调用，只暴露接口槽位：

```python
from skill_forge.llm.slots import LLMCallable

def my_llm(system: str, user: str) -> str:
    return response

from skill_forge.skill_optimizer import SkillOptimizer
optimizer = SkillOptimizer()
result = optimizer.optimize("path/to/SKILL.md", llm=my_llm)
```
