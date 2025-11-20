"""Language auto-detection for source code files."""

from pathlib import Path
from typing import Literal

LanguageType = Literal["rust", "typescript", "python", "java", "sql", "prisma"]


class LanguageDetector:
    """Auto-detect source code language from file extensions and content."""

    EXTENSION_MAP: dict[str, LanguageType] = {
        ".rs": "rust",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".py": "python",
        ".java": "java",
        ".sql": "sql",
        ".prisma": "prisma",
    }

    @classmethod
    def detect(cls, file_path: str) -> LanguageType | None:
        """Detect language from file path and content."""
        path = Path(file_path)

        # Extension-based detection
        ext = path.suffix.lower()
        if ext in cls.EXTENSION_MAP:
            return cls.EXTENSION_MAP[ext]

        # Content-based detection for ambiguous cases
        try:
            content = path.read_text()
        except (UnicodeDecodeError, OSError):
            return None

        if "diesel::table!" in content or "use sea_orm" in content:
            return "rust"
        if "model " in content and "@" in content:  # Prisma syntax
            return "prisma"
        if "CREATE FUNCTION" in content or "CREATE OR REPLACE FUNCTION" in content:
            return "sql"
        if "interface " in content and ":" in content:  # TypeScript interface
            return "typescript"
        if "class " in content and ("def " in content or "self." in content):  # Python class
            return "python"
        if "public class " in content or "import java." in content:  # Java class
            return "java"

        return None
