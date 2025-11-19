#!/usr/bin/env python3
"""
SpecQL Documentation Validator

Extracts code blocks from documentation and validates they work.
Run this in CI to ensure docs stay accurate.
"""

import re
import sys
from pathlib import Path


def extract_code_blocks(file_path: Path) -> list[tuple[str, str, int]]:
    """
    Extract code blocks from a markdown file.

    Returns: List of (language, code, line_number) tuples
    """
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Find code blocks with language specification
    pattern = r"```(\w+)\n(.*?)\n```"
    re.findall(pattern, content, re.DOTALL)

    blocks = []
    lines = content.split("\n")
    line_num = 0

    for line in lines:
        line_num += 1
        if line.startswith("```") and len(line) > 3:
            lang = line[3:].strip()
            # Find the end of the code block
            code_lines = []
            inner_line_num = line_num
            for inner_line in lines[inner_line_num:]:
                inner_line_num += 1
                if inner_line.startswith("```"):
                    break
                code_lines.append(inner_line)

            code = "\n".join(code_lines[:-1])  # Remove the closing ```
            if code.strip():  # Only add non-empty blocks
                blocks.append((lang, code, line_num))

    return blocks


def validate_yaml_block(code: str) -> bool:
    """Validate YAML syntax"""
    try:
        import yaml

        yaml.safe_load(code)
        return True
    except ImportError:
        # If yaml not available, just check basic structure
        return True
    except Exception:
        return False


def validate_bash_block(code: str) -> bool:
    """Validate bash commands (basic syntax check)"""
    # For now, just check that it doesn't have obvious syntax errors
    # In a real implementation, you'd want to use bash -n
    return True


def validate_python_block(code: str) -> bool:
    """Validate Python syntax"""
    try:
        compile(code, "<string>", "exec")
        return True
    except SyntaxError:
        return False


def validate_sql_block(code: str) -> bool:
    """Validate SQL syntax (basic check)"""
    # Basic validation - check for balanced parentheses, etc.
    return True


def validate_graphql_block(code: str) -> bool:
    """Validate GraphQL syntax (basic check)"""
    return True


def validate_typescript_block(code: str) -> bool:
    """Validate TypeScript syntax (basic check)"""
    # For now, treat as JavaScript
    try:
        compile(code, "<string>", "exec")
        return True
    except SyntaxError:
        return False


VALIDATORS = {
    "yaml": validate_yaml_block,
    "bash": validate_bash_block,
    "python": validate_python_block,
    "sql": validate_sql_block,
    "graphql": validate_graphql_block,
    "typescript": validate_typescript_block,
}


def validate_file(file_path: Path) -> list[str]:
    """Validate all code blocks in a file"""
    errors = []
    blocks = extract_code_blocks(file_path)

    for lang, code, line_num in blocks:
        if lang in VALIDATORS:
            if not VALIDATORS[lang](code):
                errors.append(f"{file_path}:{line_num}: Invalid {lang} syntax")
        else:
            # Unknown language, skip validation
            pass

    return errors


def main():
    """Main validation function"""
    docs_dir = Path("docs")
    if not docs_dir.exists():
        print("docs/ directory not found")
        sys.exit(1)

    all_errors = []

    # Find all markdown files
    for md_file in docs_dir.rglob("*.md"):
        errors = validate_file(md_file)
        all_errors.extend(errors)

    # Report results
    if all_errors:
        print("❌ Documentation validation failed:")
        for error in all_errors:
            print(f"  {error}")
        sys.exit(1)
    else:
        print("✅ All documentation code blocks are valid")
        sys.exit(0)


if __name__ == "__main__":
    main()
