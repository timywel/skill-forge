# -*- coding: utf-8 -*-
"""
测试固件 - 有效的 skill.yaml 示例
"""

VALID_SKILLS = {
    "minimal": """
name: my-skill
description: 这是一个最小的有效 Skill
definition: |
  ## Identity
  - Role: 测试技能

  ## Instructions
  1. 执行任务
  2. 返回结果
""",
    "full": """
name: code-reviewer
description: 深入分析代码质量、安全性和性能，提供可操作的改进建议
version: 1.0.0
author: Claude Code User
tags:
  - code-quality
  - security
  - review

user_invocable: true

parameters:
  - name: path
    description: 要审查的代码路径或文件
    required: true
  - name: severity
    description: 审查严重程度阈值
    required: false
    default: medium

allowed_tools:
  - Read
  - Glob
  - Grep
  - Bash

definition: |
  ## Identity
  - Name: {{name}}
  - Role: 专业代码审查专家
  - Version: {{version}}

  ## Instructions
  1. 分析 {{parameters.path}} 中的代码
  2. 检查代码质量问题
  3. 识别安全漏洞
  4. 生成审查报告

  ## Guidelines
  - 只报告 ≥ {{parameters.severity}} 级别的问题
  - 不修改原始代码
  - 引用具体代码行号
""",
    "with_variables": """
name: test-generator
description: 基于代码自动生成测试用例
version: 1.0.0

parameters:
  - name: language
    description: 编程语言
    required: true
  - name: framework
    description: 测试框架
    required: false
    default: auto

allowed_tools:
  - Read
  - Glob
  - Write

definition: |
  ## Identity
  - Role: 测试生成专家

  ## Context
  {{input}}

  语言: {{parameters.language}}
  框架: {{parameters.framework}}

  ## Instructions
  1. 分析代码结构
  2. 生成测试用例
  3. 输出到 tests/ 目录
""",
}

INVALID_SKILLS = {
    "missing_name": """
description: 缺少 name 字段
definition: |
  ## Identity
  - Role: 测试
""",
    "missing_definition": """
name: test-skill
description: 缺少 definition 字段
""",
    "missing_description": """
name: test-skill
definition: |
  ## Identity
  - Role: 测试
""",
    "invalid_name_uppercase": """
name: Test-Skill
description: 名称包含大写字母
definition: |
  ## Identity
  - Role: 测试
""",
    "invalid_name_spaces": """
name: test skill
description: 名称包含空格
definition: |
  ## Identity
  - Role: 测试
""",
    "invalid_name_special": """
name: test_skill
description: 名称包含下划线
definition: |
  ## Identity
  - Role: 测试
""",
    "empty_definition": """
name: test-skill
description: 测试技能
definition: ""
""",
    "description_too_long": """
name: test-skill
description: "这是一个非常长的描述，" + "x" * 1000
definition: |
  ## Identity
  - Role: 测试
""",
    "invalid_version": """
name: test-skill
description: 测试技能
version: latest
definition: |
  ## Identity
  - Role: 测试
""",
    "parameter_missing_name": """
name: test-skill
description: 测试技能
parameters:
  - description: 缺少 name 字段
definition: |
  ## Identity
  - Role: 测试
""",
    "tool_lowercase": """
name: test-skill
description: 测试技能
allowed_tools:
  - read
  - bash
definition: |
  ## Identity
  - Role: 测试
""",
}
