#!/usr/bin/env python3
"""
skill-forge CLI 入口

用法:
    skill-forge validate <path> [--batch] [--format json|yaml|markdown]
    skill-forge convert nl --input "..."
    skill-forge convert agent --input <path>
    skill-forge convert normalize --input <path>
    skill-forge optimize <path> [--level 0-3] [--auto-fix]
    skill-forge quality <path>
    skill-forge registry list|add|remove
"""

import sys
from skill_forge.cli import main

if __name__ == "__main__":
    sys.exit(main())
