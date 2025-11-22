# ==============================================================================
# Reverse Project Tests
# ==============================================================================

import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from cli.main import app


@pytest.fixture
def runner():
    """CLI runner fixture."""
    return CliRunner()


def test_reverse_django_project(runner):
    """Reverse engineering a Django project processes models.py files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create Django project structure
        project = Path(tmpdir) / "myproject"
        project.mkdir()
        (project / "manage.py").touch()

        app_dir = project / "myapp"
        app_dir.mkdir()
        models = app_dir / "models.py"
        models.write_text("""
from django.db import models

class Contact(models.Model):
    email = models.EmailField()
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'myapp'
""")

        output_dir = Path(tmpdir) / "output"
        output_dir.mkdir()

        result = runner.invoke(app, ["reverse", "project", str(project), "-o", str(output_dir)])

        assert result.exit_code == 0
        assert (output_dir / "contact.yaml").exists()


def test_reverse_rust_project(runner):
    """Reverse engineering a Rust project processes schema.rs files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create Rust project structure
        project = Path(tmpdir) / "myproject"
        project.mkdir()
        (project / "Cargo.toml").write_text("""
[package]
name = "myproject"
version = "0.1.0"

[dependencies]
diesel = "2.0"
""")

        src_dir = project / "src"
        src_dir.mkdir()
        schema = src_dir / "schema.rs"
        schema.write_text("""
use diesel::prelude::*;

#[derive(Queryable, Insertable)]
#[table_name = "contacts"]
pub struct Contact {
    pub id: i32,
    pub email: String,
    pub name: String,
    pub created_at: NaiveDateTime,
}
""")

        output_dir = Path(tmpdir) / "output"
        output_dir.mkdir()

        result = runner.invoke(app, ["reverse", "project", str(project), "-o", str(output_dir)])

        assert result.exit_code == 0
        assert (output_dir / "contact.yaml").exists()


def test_reverse_prisma_project(runner):
    """Reverse engineering a Prisma project processes .prisma files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create Prisma project structure
        project = Path(tmpdir) / "myproject"
        project.mkdir()
        (project / "package.json").write_text("""
{
  "name": "myproject",
  "dependencies": {
    "prisma": "^4.0.0"
  }
}
""")

        schema = project / "schema.prisma"
        schema.write_text("""
model Contact {
  id        Int      @id @default(autoincrement())
  email     String
  name      String
  createdAt DateTime @default(now())
}
""")

        output_dir = Path(tmpdir) / "output"
        output_dir.mkdir()

        result = runner.invoke(app, ["reverse", "project", str(project), "-o", str(output_dir)])

        assert result.exit_code == 0
        assert (output_dir / "contact.yaml").exists()


def test_reverse_project_preview_no_output(runner):
    """Preview mode shows plan without generating files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create Django project structure
        project = Path(tmpdir) / "myproject"
        project.mkdir()
        (project / "manage.py").touch()

        app_dir = project / "myapp"
        app_dir.mkdir()
        models = app_dir / "models.py"
        models.write_text("""
from django.db import models

class Contact(models.Model):
    email = models.EmailField()
""")

        output_dir = Path(tmpdir) / "output"
        output_dir.mkdir()

        result = runner.invoke(
            app, ["reverse", "project", str(project), "-o", str(output_dir), "--preview"]
        )

        assert result.exit_code == 0
        assert "models.py" in result.output
        assert not (output_dir / "contact.yaml").exists()


def test_reverse_project_explicit_framework(runner):
    """--framework overrides auto-detection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create generic project structure
        project = Path(tmpdir) / "myproject"
        project.mkdir()

        # No Django manage.py, but we'll force django framework
        app_dir = project / "myapp"
        app_dir.mkdir()
        models = app_dir / "models.py"
        models.write_text("""
from django.db import models

class Contact(models.Model):
    email = models.EmailField()
""")

        output_dir = Path(tmpdir) / "output"
        output_dir.mkdir()

        result = runner.invoke(
            app, ["reverse", "project", str(project), "-o", str(output_dir), "--framework=django"]
        )

        assert result.exit_code == 0
        assert (output_dir / "contact.yaml").exists()


def test_reverse_sql_project(runner):
    """Reverse engineering a SQL project processes .sql files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create SQL project structure (FraiseQL-style)
        project = Path(tmpdir) / "myproject"
        project.mkdir()

        db_dir = project / "db" / "schema"
        db_dir.mkdir(parents=True)
        schema = db_dir / "contact.sql"
        schema.write_text("""
CREATE TABLE crm.tb_contact (
    pk_contact SERIAL PRIMARY KEY,
    id UUID DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    name TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
""")

        output_dir = Path(tmpdir) / "output"
        output_dir.mkdir()

        result = runner.invoke(app, ["reverse", "project", str(project), "-o", str(output_dir)])

        assert result.exit_code == 0
        assert "sql" in result.output.lower()  # Detected as SQL project
        assert (output_dir / "contact.yaml").exists()


def test_reverse_sql_project_root_files(runner):
    """Reverse engineering a SQL project with .sql files in root."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create SQL project with files in root
        project = Path(tmpdir) / "myproject"
        project.mkdir()

        schema = project / "schema.sql"
        schema.write_text("""
CREATE TABLE public.tb_user (
    pk_user SERIAL PRIMARY KEY,
    id UUID DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    username TEXT
);
""")

        output_dir = Path(tmpdir) / "output"
        output_dir.mkdir()

        result = runner.invoke(app, ["reverse", "project", str(project), "-o", str(output_dir)])

        assert result.exit_code == 0
        assert "sql" in result.output.lower()
        assert (output_dir / "user.yaml").exists()


def test_reverse_project_mixed_languages(runner):
    """Handles projects with multiple languages gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create mixed project
        project = Path(tmpdir) / "mixed_project"
        project.mkdir()

        # Add Python file
        models = project / "models.py"
        models.write_text("""
from django.db import models

class Contact(models.Model):
    email = models.EmailField()
""")

        # Add SQL file
        schema = project / "schema.sql"
        schema.write_text("""
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT
);
""")

        output_dir = Path(tmpdir) / "output"
        output_dir.mkdir()

        result = runner.invoke(app, ["reverse", "project", str(project), "-o", str(output_dir)])

        assert result.exit_code == 0
        # Should process files it can handle
        assert (output_dir / "contact.yaml").exists() or (output_dir / "users.yaml").exists()


def test_reverse_project_empty_directory(runner):
    """Handles empty project directory by detecting as unknown."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create empty project
        project = Path(tmpdir) / "empty_project"
        project.mkdir()

        output_dir = Path(tmpdir) / "output"
        output_dir.mkdir()

        result = runner.invoke(app, ["reverse", "project", str(project), "-o", str(output_dir)])

        # Should fail because project type cannot be detected
        assert result.exit_code != 0
        assert "unknown" in result.output.lower() or "could not detect" in result.output.lower()


def test_reverse_project_invalid_framework(runner):
    """Shows error for invalid framework specification."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project = Path(tmpdir) / "project"
        project.mkdir()

        output_dir = Path(tmpdir) / "output"
        output_dir.mkdir()

        result = runner.invoke(
            app, ["reverse", "project", str(project), "--framework=invalid", "-o", str(output_dir)]
        )

        assert result.exit_code != 0
        assert "invalid" in result.output.lower() or "unknown" in result.output.lower()
