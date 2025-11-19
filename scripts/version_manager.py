#!/usr/bin/env python3
"""Industrial-Grade Version Manager for SpecQL

Rock-solid, bulletproof version management with:
- Atomic operations
- Complete rollback on any failure
- Pre-flight validation
- Complete logging
- Git workflow integration
- Zero-downtime approach

Adapted from PrintOptim's production system, simplified for SpecQL.
"""

import json
import re
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal


class VersionManager:
    """Version manager with bulletproof atomic operations."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.version_file = self.project_root / "version.json"
        self.legacy_version_file = self.project_root / "VERSION"
        self.pyproject_file = self.project_root / "pyproject.toml"

        # Backup tracking
        self.backup_dir = None
        self.operations_log = []

    def log_operation(self, operation: str, status: str = "SUCCESS", details: str = ""):
        """Log all operations for debugging and rollback."""
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "operation": operation,
            "status": status,
            "details": details,
        }
        self.operations_log.append(entry)
        print(f"🔍 {operation}: {status} {details}")

    def create_backup(self) -> Path:
        """Create atomic backup of all version-related files."""
        self.backup_dir = Path(tempfile.mkdtemp(prefix="version_backup_"))

        files_to_backup = [
            self.version_file,
            self.legacy_version_file,
            self.pyproject_file,
        ]

        for file_path in files_to_backup:
            if file_path.exists():
                backup_path = self.backup_dir / file_path.name
                backup_path.write_text(file_path.read_text())

        self.log_operation("Created backup", "SUCCESS", f"in {self.backup_dir}")
        return self.backup_dir

    def rollback_from_backup(self):
        """Atomic rollback from backup."""
        if not self.backup_dir or not self.backup_dir.exists():
            self.log_operation("Rollback", "FAILED", "No backup directory found")
            return False

        try:
            # Restore all files
            for backup_file in self.backup_dir.glob("*"):
                target_file = self.project_root / backup_file.name
                target_file.write_text(backup_file.read_text())

            # Remove any tags created during failed operation
            if hasattr(self, "_created_tag"):
                subprocess.run(
                    ["git", "tag", "-d", self._created_tag], capture_output=True, check=False
                )

            self.log_operation("Rollback", "SUCCESS", "All changes reverted")
            return True

        except Exception as e:
            self.log_operation("Rollback", "FAILED", str(e))
            return False

    def validate_git_state(self) -> bool:
        """Comprehensive git state validation."""
        try:
            # Check if we're in a git repo
            subprocess.run(["git", "rev-parse", "--git-dir"], capture_output=True, check=True)

            # Check for uncommitted changes (allow version files to be dirty)
            result = subprocess.run(
                ["git", "status", "--porcelain"], capture_output=True, text=True, check=True
            )

            if result.stdout.strip():
                modified_files = [line.strip() for line in result.stdout.strip().split("\n")]

                # Allow version-related files to be dirty (from our changes)
                version_files = {"version.json", "VERSION", "pyproject.toml"}
                non_version_changes = [
                    f for f in modified_files if not any(vf in f for vf in version_files)
                ]

                if non_version_changes:
                    self.log_operation(
                        "Git validation",
                        "WARNING",
                        f"Non-version files modified: {non_version_changes}",
                    )
                    print("⚠️  Warning: You have uncommitted changes")
                    print("   Version bump will proceed, but please commit/stash other changes")

            # Check if we can create tags
            test_tag = f"test-tag-{datetime.now(UTC).timestamp()}"
            result = subprocess.run(["git", "tag", test_tag], capture_output=True, check=False)
            if result.returncode == 0:
                subprocess.run(["git", "tag", "-d", test_tag], capture_output=True, check=False)
            else:
                self.log_operation("Git validation", "FAILED", "Cannot create git tags")
                return False

            self.log_operation("Git state validation", "SUCCESS")
            return True

        except subprocess.CalledProcessError as e:
            self.log_operation("Git validation", "FAILED", str(e))
            return False

    def validate_version_format(self, version: str) -> bool:
        """Validate semantic version format."""
        pattern = r"^(\d+)\.(\d+)\.(\d+)$"
        if not re.match(pattern, version):
            self.log_operation("Version validation", "FAILED", f"Invalid format: {version}")
            return False

        self.log_operation("Version validation", "SUCCESS", version)
        return True

    def parse_version(self, version_str: str) -> tuple[int, int, int]:
        """Parse and validate version string."""
        base_version = version_str.split("-")[0]
        parts = base_version.split(".")

        if len(parts) != 3:
            msg = f"Invalid version format: {version_str}"
            raise ValueError(msg)

        try:
            return (int(parts[0]), int(parts[1]), int(parts[2]))
        except ValueError:
            msg = f"Invalid version format: {version_str}"
            raise ValueError(msg) from None

    def bump_version(self, current: str, bump_type: Literal["major", "minor", "patch"]) -> str:
        """Calculate new version with validation."""
        major, minor, patch = self.parse_version(current)

        if bump_type == "major":
            new_version = f"{major + 1}.0.0"
        elif bump_type == "minor":
            new_version = f"{major}.{minor + 1}.0"
        else:  # patch
            new_version = f"{major}.{minor}.{patch + 1}"

        if not self.validate_version_format(new_version):
            msg = f"Generated invalid version: {new_version}"
            raise ValueError(msg)

        return new_version

    def get_current_version(self) -> str:
        """Get current version from version.json or fall back to VERSION file."""
        # Try version.json first
        if self.version_file.exists():
            try:
                with open(self.version_file) as f:
                    data = json.load(f)
                    version = data.get("version", "0.1.0")
            except (json.JSONDecodeError, KeyError):
                self.log_operation(
                    "Version read", "WARNING", "Invalid version.json, using VERSION file"
                )
                version = self.get_version_from_legacy()
        else:
            version = self.get_version_from_legacy()

        if not self.validate_version_format(version):
            msg = f"Current version is invalid: {version}"
            raise ValueError(msg)

        return version

    def get_version_from_legacy(self) -> str:
        """Get version from legacy VERSION file."""
        if self.legacy_version_file.exists():
            return self.legacy_version_file.read_text().strip()
        return self.get_version_from_pyproject()

    def get_version_from_pyproject(self) -> str:
        """Extract version from pyproject.toml."""
        try:
            if not self.pyproject_file.exists():
                return "0.1.0"

            with open(self.pyproject_file) as f:
                content = f.read()

            match = re.search(r'^version = "([^"]*)"', content, re.MULTILINE)
            if match:
                return match.group(1)
            return "0.1.0"
        except FileNotFoundError:
            return "0.1.0"

    def get_git_info(self) -> dict:
        """Get current git information."""
        try:
            commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
            branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
            return {"commit": commit[:8], "branch": branch}
        except subprocess.CalledProcessError:
            return {"commit": "unknown", "branch": "unknown"}

    def update_version_file(self, new_version: str) -> bool:
        """Atomically update version.json."""
        try:
            git_info = self.get_git_info()
            commit = git_info["commit"]
            branch = git_info["branch"]

            now = datetime.now(UTC)

            # Create new version data
            version_data = {
                "version": new_version,
                "commit": commit,
                "branch": branch,
                "timestamp": now.isoformat(),
                "environment": "development",
            }

            # Atomic write
            temp_file = self.version_file.with_suffix(".tmp")
            with open(temp_file, "w") as f:
                json.dump(version_data, f, indent=2)
                f.write("\n")  # Add newline at end for pre-commit hook compatibility

            temp_file.replace(self.version_file)

            self.log_operation("Version file update", "SUCCESS", new_version)
            return True

        except Exception as e:
            self.log_operation("Version file update", "FAILED", str(e))
            return False

    def update_legacy_version_file(self, new_version: str) -> bool:
        """Update legacy VERSION file for backwards compatibility."""
        try:
            temp_file = self.legacy_version_file.with_suffix(".tmp")
            temp_file.write_text(f"{new_version}\n")
            temp_file.replace(self.legacy_version_file)

            self.log_operation("Legacy VERSION file update", "SUCCESS", new_version)
            return True
        except Exception as e:
            self.log_operation("Legacy VERSION file update", "FAILED", str(e))
            return False

    def update_pyproject_toml(self, new_version: str) -> bool:
        """Atomically update pyproject.toml version."""
        try:
            with open(self.pyproject_file) as f:
                content = f.read()

            # Replace version line
            new_content = re.sub(
                r'^version = "[^"]*"', f'version = "{new_version}"', content, flags=re.MULTILINE
            )

            if new_content == content:
                self.log_operation("PyProject update", "FAILED", "Version line not found")
                return False

            # Atomic write
            temp_file = self.pyproject_file.with_suffix(".tmp")
            with open(temp_file, "w") as f:
                f.write(new_content)

            temp_file.replace(self.pyproject_file)

            self.log_operation("PyProject update", "SUCCESS", new_version)
            return True

        except Exception as e:
            self.log_operation("PyProject update", "FAILED", str(e))
            return False

    def create_git_tag(self, version: str) -> bool:
        """Create git tag with validation."""
        tag_name = f"v{version}"

        try:
            # Check if tag exists
            result = subprocess.run(
                ["git", "tag", "-l", tag_name], capture_output=True, text=True, check=True
            )

            if result.stdout.strip():
                self.log_operation("Git tag", "FAILED", f"Tag {tag_name} already exists")
                return False

            # Create annotated tag
            message = f"Release {version}"
            subprocess.run(["git", "tag", "-a", tag_name, "-m", message], check=True)

            # Track for potential rollback
            self._created_tag = tag_name

            self.log_operation("Git tag", "SUCCESS", tag_name)
            return True

        except subprocess.CalledProcessError as e:
            self.log_operation("Git tag", "FAILED", str(e))
            return False

    def run_industrial_bump(self, bump_type: Literal["major", "minor", "patch"]) -> bool:
        """Version bump with complete atomicity and rollback.

        Returns True on success, False on any failure (with automatic rollback).
        """
        print(f"📦 VERSION MANAGER - {bump_type.upper()} BUMP")
        print("=" * 60)

        try:
            # Phase 1: Pre-flight validation
            print("📋 Phase 1: Pre-flight Validation")

            if not self.validate_git_state():
                print("❌ Git state validation failed")
                return False

            current_version = self.get_current_version()
            new_version = self.bump_version(current_version, bump_type)

            print(f"📊 Version transition: {current_version} → {new_version}")

            # Phase 2: Create atomic backup
            print("\n💾 Phase 2: Creating Atomic Backup")
            self.create_backup()

            # Phase 3: Execute atomic operations
            print("\n⚙️  Phase 3: Executing Atomic Operations")

            if not self.update_version_file(new_version):
                print("❌ Version file update failed - rolling back")
                self.rollback_from_backup()
                return False

            if not self.update_legacy_version_file(new_version):
                print("❌ Legacy VERSION file update failed - rolling back")
                self.rollback_from_backup()
                return False

            if not self.update_pyproject_toml(new_version):
                print("❌ PyProject update failed - rolling back")
                self.rollback_from_backup()
                return False

            if not self.create_git_tag(new_version):
                print("❌ Git tag creation failed - rolling back")
                self.rollback_from_backup()
                return False

            # Phase 4: Final validation
            print("\n✅ Phase 4: Final Validation")

            # Verify the changes took effect
            if self.get_current_version() != new_version:
                print("❌ Version verification failed - rolling back")
                self.rollback_from_backup()
                return False

            print("\n🎉 VERSION BUMP SUCCESSFUL")
            print(f"✨ Version: {current_version} → {new_version}")
            print(f"🏷️  Git tag: v{new_version}")

            print("\n📋 Next Steps:")
            print("   git add version.json VERSION pyproject.toml")
            print(f"   git commit -m 'chore: bump version to {new_version}'")
            print("   git push --tags")
            print(f"\n💡 Or push the tag to trigger release: git push origin v{new_version}")

            return True

        except Exception as e:
            print(f"❌ CRITICAL ERROR: {e}")
            print("🔄 Initiating emergency rollback...")
            self.rollback_from_backup()
            return False


def main():
    """CLI entry point for industrial version manager."""
    import argparse

    parser = argparse.ArgumentParser(description="SpecQL Industrial Version Manager")
    parser.add_argument("bump_type", choices=["major", "minor", "patch"], help="Version bump type")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done without making changes"
    )

    args = parser.parse_args()

    if args.dry_run:
        print(f"🧪 DRY RUN: Would perform {args.bump_type} version bump")
        manager = VersionManager()
        current = manager.get_current_version()
        new_version = manager.bump_version(current, args.bump_type)
        print(f"📊 Would bump: {current} → {new_version}")
        return

    manager = VersionManager()
    success = manager.run_industrial_bump(args.bump_type)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
