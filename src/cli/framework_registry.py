"""
Framework Registry - Configuration for supported frameworks and their patterns
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class FrameworkConfig:
    """Configuration for a specific framework"""

    name: str
    language: str
    file_extensions: list[str]
    parser_class: Any  # Type hint for parser class
    pattern_enhancers: list[str]  # Patterns to automatically apply


class FrameworkRegistry:
    """Registry of supported frameworks and their configurations"""

    FRAMEWORKS = {
        "diesel": FrameworkConfig(
            name="diesel",
            language="rust",
            file_extensions=[".rs"],
            parser_class=None,  # Will be set dynamically
            pattern_enhancers=["soft_delete", "audit_trail"],
        ),
        "seaorm": FrameworkConfig(
            name="seaorm",
            language="rust",
            file_extensions=[".rs"],
            parser_class=None,  # Will be set dynamically
            pattern_enhancers=["soft_delete", "audit_trail", "multi_tenant"],
        ),
        "prisma": FrameworkConfig(
            name="prisma",
            language="typescript",
            file_extensions=[".prisma"],
            parser_class=None,  # Will be set dynamically
            pattern_enhancers=["soft_delete", "audit_trail"],
        ),
        "sqlalchemy": FrameworkConfig(
            name="sqlalchemy",
            language="python",
            file_extensions=[".py"],
            parser_class=None,  # Will be set dynamically
            pattern_enhancers=["soft_delete", "audit_trail"],
        ),
        "django": FrameworkConfig(
            name="django",
            language="python",
            file_extensions=[".py"],
            parser_class=None,  # Will be set dynamically
            pattern_enhancers=["soft_delete", "audit_trail"],
        ),
        "spring": FrameworkConfig(
            name="spring",
            language="java",
            file_extensions=[".java"],
            parser_class=None,  # Will be set dynamically
            pattern_enhancers=["audit_trail", "multi_tenant"],
        ),
        "hibernate": FrameworkConfig(
            name="hibernate",
            language="java",
            file_extensions=[".java"],
            parser_class=None,  # Will be set dynamically
            pattern_enhancers=["audit_trail", "versioning"],
        ),
    }

    @classmethod
    def get_framework(cls, name: str) -> FrameworkConfig | None:
        """Get framework configuration by name"""
        return cls.FRAMEWORKS.get(name)

    @classmethod
    def detect_framework(cls, file_path: str) -> str | None:
        """Auto-detect framework from file content"""
        content = Path(file_path).read_text()

        if "diesel::table!" in content:
            return "diesel"
        elif "use sea_orm" in content:
            return "seaorm"
        elif "generator client" in content:
            return "prisma"
        elif "from sqlalchemy" in content or "import sqlalchemy" in content:
            return "sqlalchemy"
        elif "from django.db" in content or "import django" in content:
            return "django"
        elif "@Entity" in content and "javax.persistence" in content:
            return "hibernate"
        elif "@Entity" in content and "jakarta.persistence" in content:
            return "spring"

        return None

    @classmethod
    def detect_framework_from_project(cls, project_path: str) -> str | None:
        """Auto-detect framework from project structure"""
        path = Path(project_path)

        # Check for common framework indicators
        if (path / "Cargo.toml").exists():
            cargo_content = (path / "Cargo.toml").read_text()
            if "diesel" in cargo_content:
                return "diesel"
            elif "sea-orm" in cargo_content:
                return "seaorm"

        elif (path / "package.json").exists():
            package_content = (path / "package.json").read_text()
            if "prisma" in package_content:
                return "prisma"

        elif (path / "requirements.txt").exists():
            req_content = (path / "requirements.txt").read_text()
            if "sqlalchemy" in req_content:
                return "sqlalchemy"
            elif "django" in req_content:
                return "django"

        elif (path / "pom.xml").exists() or (path / "build.gradle").exists():
            return "spring"  # Default to Spring for Java projects

        return None

    @classmethod
    def get_supported_frameworks(cls) -> list[str]:
        """Get list of supported framework names"""
        return list(cls.FRAMEWORKS.keys())
