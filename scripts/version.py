#!/usr/bin/env python3
"""
Version management script for SpecQL.

Usage:
    python scripts/version.py                    # Show current version
    python scripts/version.py bump patch         # Bump patch version (0.1.0 -> 0.1.1)
    python scripts/version.py bump minor         # Bump minor version (0.1.0 -> 0.2.0)
    python scripts/version.py bump major         # Bump major version (0.1.0 -> 1.0.0)
    python scripts/version.py set 1.2.3          # Set specific version
"""

import argparse
import re
import sys
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def get_version_file() -> Path:
    """Get the VERSION file path."""
    return get_project_root() / "VERSION"


def read_version() -> str:
    """Read the current version from VERSION file."""
    version_file = get_version_file()
    if not version_file.exists():
        raise FileNotFoundError(f"VERSION file not found at {version_file}")
    return version_file.read_text().strip()


def write_version(version: str) -> None:
    """Write version to VERSION file."""
    version_file = get_version_file()
    version_file.write_text(f"{version}\n")
    print(f"✅ Version updated to {version}")


def parse_version(version: str) -> tuple[int, int, int]:
    """Parse a semantic version string into (major, minor, patch)."""
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version)
    if not match:
        raise ValueError(f"Invalid semantic version: {version}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def bump_version(current: str, part: str) -> str:
    """Bump the specified part of the version."""
    major, minor, patch = parse_version(current)

    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid version part: {part}. Use major, minor, or patch.")

    return f"{major}.{minor}.{patch}"


def validate_version(version: str) -> bool:
    """Validate that a version string is valid semver."""
    try:
        parse_version(version)
        return True
    except ValueError:
        return False


def update_pyproject_toml(version: str) -> None:
    """Update version in pyproject.toml."""
    pyproject_path = get_project_root() / "pyproject.toml"
    content = pyproject_path.read_text()

    # Update version line in [project] section only
    # Match 'version = "..."' in the first few lines (project section)
    lines = content.split('\n')
    updated_lines = []
    in_project_section = False
    version_updated = False

    for line in lines:
        if line.strip().startswith('[project]'):
            in_project_section = True
        elif line.strip().startswith('[') and in_project_section:
            in_project_section = False

        if in_project_section and line.strip().startswith('version = ') and not version_updated:
            # Update the version line, preserving the comment if present
            if '#' in line:
                indent = line[:len(line) - len(line.lstrip())]
                comment_part = line.split('#', 1)[1]
                updated_lines.append(f'{indent}version = "{version}"  # {comment_part}')
            else:
                indent = line[:len(line) - len(line.lstrip())]
                updated_lines.append(f'{indent}version = "{version}"')
            version_updated = True
        else:
            updated_lines.append(line)

    pyproject_path.write_text('\n'.join(updated_lines))
    print("✅ Updated pyproject.toml")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Manage SpecQL version using Semantic Versioning"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Show current version (default)
    subparsers.add_parser("show", help="Show current version")

    # Bump version
    bump_parser = subparsers.add_parser("bump", help="Bump version")
    bump_parser.add_argument(
        "part",
        choices=["major", "minor", "patch"],
        help="Version part to bump"
    )

    # Set specific version
    set_parser = subparsers.add_parser("set", help="Set specific version")
    set_parser.add_argument("version", help="Version to set (e.g., 1.2.3)")

    args = parser.parse_args()

    try:
        current_version = read_version()

        if args.command is None or args.command == "show":
            print(f"Current version: {current_version}")
            return 0

        elif args.command == "bump":
            new_version = bump_version(current_version, args.part)
            print(f"Bumping {args.part} version: {current_version} → {new_version}")
            write_version(new_version)
            update_pyproject_toml(new_version)
            return 0

        elif args.command == "set":
            if not validate_version(args.version):
                print(f"❌ Invalid semantic version: {args.version}", file=sys.stderr)
                print("Version must be in format: MAJOR.MINOR.PATCH (e.g., 1.2.3)", file=sys.stderr)
                return 1

            print(f"Setting version: {current_version} → {args.version}")
            write_version(args.version)
            update_pyproject_toml(args.version)
            return 0

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
