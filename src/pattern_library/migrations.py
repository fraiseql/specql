"""Migration utilities for pattern library schema updates"""

import sqlite3
from typing import Dict, List


class MigrationManager:
    """Manages database schema migrations"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db = sqlite3.connect(db_path)
        self._ensure_migrations_table()

    def _ensure_migrations_table(self):
        """Create migrations tracking table if it doesn't exist"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                migration_id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.db.commit()

    def apply_migration(self, migration_id: str, description: str, sql: str) -> bool:
        """
        Apply a migration if not already applied

        Args:
            migration_id: Unique identifier for the migration
            description: Human-readable description
            sql: SQL to execute

        Returns:
            True if migration was applied, False if already applied
        """
        # Check if migration already applied
        cursor = self.db.execute(
            "SELECT migration_id FROM schema_migrations WHERE migration_id = ?",
            (migration_id,)
        )
        if cursor.fetchone():
            return False  # Already applied

        # Apply migration
        self.db.executescript(sql)

        # Record migration
        self.db.execute(
            "INSERT INTO schema_migrations (migration_id, description) VALUES (?, ?)",
            (migration_id, description)
        )
        self.db.commit()

        return True

    def get_applied_migrations(self) -> List[Dict[str, str]]:
        """Get list of applied migrations"""
        cursor = self.db.execute(
            "SELECT migration_id, description, applied_at FROM schema_migrations ORDER BY applied_at"
        )
        return [{"migration_id": row[0], "description": row[1], "applied_at": row[2]} for row in cursor.fetchall()]

    def close(self):
        """Close database connection"""
        self.db.close()


# Example migrations
def migrate_add_performance_indexes(db_path: str):
    """Add performance indexes migration"""
    manager = MigrationManager(db_path)

    sql = """
    -- Add performance indexes
    CREATE INDEX IF NOT EXISTS idx_patterns_name ON patterns(pattern_name);
    CREATE INDEX IF NOT EXISTS idx_languages_name ON languages(language_name);
    CREATE INDEX IF NOT EXISTS idx_implementations_composite ON pattern_implementations(pattern_id, language_id);
    """

    applied = manager.apply_migration(
        migration_id="add_performance_indexes",
        description="Add performance indexes for faster queries",
        sql=sql
    )

    manager.close()
    return applied


def migrate_add_metadata_columns(db_path: str):
    """Add metadata columns migration"""
    manager = MigrationManager(db_path)

    sql = """
    -- Add metadata columns
    ALTER TABLE patterns ADD COLUMN tags TEXT DEFAULT '';
    ALTER TABLE patterns ADD COLUMN author TEXT DEFAULT '';
    ALTER TABLE languages ADD COLUMN documentation_url TEXT DEFAULT '';
    """

    applied = manager.apply_migration(
        migration_id="add_metadata_columns",
        description="Add metadata columns for better organization",
        sql=sql
    )

    manager.close()
    return applied


if __name__ == "__main__":
    # Example usage
    db_path = "pattern_library.db"

    print("Applying performance indexes migration...")
    applied = migrate_add_performance_indexes(db_path)
    print(f"Applied: {applied}")

    print("Applying metadata columns migration...")
    applied = migrate_add_metadata_columns(db_path)
    print(f"Applied: {applied}")

    # Show applied migrations
    manager = MigrationManager(db_path)
    migrations = manager.get_applied_migrations()
    print(f"\nApplied migrations: {len(migrations)}")
    for migration in migrations:
        print(f"  - {migration['migration_id']}: {migration['description']}")
    manager.close()