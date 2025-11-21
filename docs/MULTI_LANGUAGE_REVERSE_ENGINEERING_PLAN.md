# Multi-Language Reverse Engineering Implementation Plan

**Version**: 1.0
**Date**: 2025-11-21
**Status**: Planning
**Methodology**: Phased TDD (RED → GREEN → REFACTOR → QA)

---

## Executive Summary

This plan connects the existing backend parsers to the CLI `reverse` commands for Python, TypeScript, Rust, and Java. The reverse engineering module already has comprehensive parsers - they just need CLI integration following the same pattern used for `reverse sql`.

### Current State

| Language | CLI Status | Backend Parser | Ready for Integration |
|----------|------------|----------------|----------------------|
| SQL | **Stable** | `table_parser.py`, `algorithmic_parser.py` | Done |
| Python | Stub | `python_ast_parser.py` | Yes |
| TypeScript | Stub | `typescript_parser.py`, `prisma_parser.py` | Yes |
| Rust | Stub | `rust_parser.py`, `seaorm_parser.py` | Yes |
| Java | Not in CLI | `java/java_parser.py` | Needs CLI command |

### Target State

All language reverse commands fully integrated with 10+ tests each.

---

## Task 1: Python Reverse Engineering

**Priority**: High
**Effort**: 3 hours
**Location**: `src/cli/commands/reverse/python.py`

### Backend Parsers Available

- `reverse_engineering/python_ast_parser.py` - `PythonASTParser` class
  - Supports: Dataclasses, Pydantic, Django, SQLAlchemy
  - Returns: `ParsedEntity` with fields, methods, patterns
  - Uses Python's built-in `ast` module (no external dependencies)

- `reverse_engineering/python_to_specql_mapper.py` - Maps to SpecQL YAML

### Implementation Steps

#### Phase 1.1: RED - Write Failing Tests

Create `tests/unit/cli/commands/reverse/test_python.py`:

```python
"""Tests for reverse python CLI command."""

import pytest
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import patch, MagicMock


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def sample_django_model():
    return '''
from django.db import models

class Contact(models.Model):
    email = models.CharField(max_length=255)
    company = models.ForeignKey("Company", on_delete=models.CASCADE)
    status = models.CharField(max_length=50, default="lead")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "contacts"
'''


@pytest.fixture
def sample_pydantic_model():
    return '''
from pydantic import BaseModel
from typing import Optional

class Contact(BaseModel):
    email: str
    company_id: Optional[int] = None
    status: str = "lead"
'''


@pytest.fixture
def sample_sqlalchemy_model():
    return '''
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"))
'''


def test_reverse_python_requires_files():
    """reverse python should require file arguments."""
    from cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["reverse", "python"])

    assert result.exit_code != 0
    assert "Missing argument" in result.output


def test_reverse_python_requires_output_dir():
    """reverse python should require output directory."""
    from cli.main import app

    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("models.py").write_text("class Foo: pass")
        result = runner.invoke(app, ["reverse", "python", "models.py"])

        assert result.exit_code != 0


def test_reverse_python_parses_django_model(cli_runner, sample_django_model):
    """reverse python should parse Django models."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("models.py").write_text(sample_django_model)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "python", "models.py", "-o", "out/"]
        )

        assert result.exit_code == 0
        yaml_files = list(Path("out/").glob("*.yaml"))
        assert len(yaml_files) >= 1

        # Check YAML content
        yaml_content = yaml_files[0].read_text()
        assert "Contact" in yaml_content or "contact" in yaml_content


def test_reverse_python_parses_pydantic_model(cli_runner, sample_pydantic_model):
    """reverse python should parse Pydantic models."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("schemas.py").write_text(sample_pydantic_model)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "python", "schemas.py", "-o", "out/"]
        )

        assert result.exit_code == 0


def test_reverse_python_parses_sqlalchemy_model(cli_runner, sample_sqlalchemy_model):
    """reverse python should parse SQLAlchemy models."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("models.py").write_text(sample_sqlalchemy_model)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "python", "models.py", "-o", "out/"]
        )

        assert result.exit_code == 0


def test_reverse_python_preview_mode(cli_runner, sample_django_model):
    """reverse python --preview should not write files."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("models.py").write_text(sample_django_model)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "python", "models.py", "-o", "out/", "--preview"]
        )

        assert result.exit_code == 0
        yaml_files = list(Path("out/").glob("*.yaml"))
        assert len(yaml_files) == 0


def test_reverse_python_auto_detects_framework(cli_runner, sample_django_model):
    """reverse python should auto-detect the framework."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("models.py").write_text(sample_django_model)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "python", "models.py", "-o", "out/"]
        )

        assert result.exit_code == 0
        assert "django" in result.output.lower() or "Django" in result.output


def test_reverse_python_framework_override(cli_runner, sample_django_model):
    """reverse python --framework should override auto-detection."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("models.py").write_text(sample_django_model)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "python", "models.py", "-o", "out/", "--framework", "sqlalchemy"]
        )

        # Should still work even if framework doesn't match
        assert result.exit_code == 0


def test_reverse_python_multiple_files(cli_runner, sample_django_model):
    """reverse python should handle multiple files."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("contact.py").write_text(sample_django_model)
        Path("task.py").write_text(sample_django_model.replace("Contact", "Task"))
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "python", "contact.py", "task.py", "-o", "out/"]
        )

        assert result.exit_code == 0
```

#### Phase 1.2: GREEN - Implement CLI Integration

Update `src/cli/commands/reverse/python.py`:

```python
"""
Reverse Python subcommand - Convert Django/FastAPI/SQLAlchemy models to SpecQL YAML.

Integrates with:
- PythonASTParser: Parses Python classes using ast module
- Supports: Django, Pydantic, SQLAlchemy, Dataclasses
"""

from pathlib import Path
import yaml

import click

from cli.utils.error_handler import handle_cli_error
from cli.utils.output import output


def _detect_framework(source_code: str) -> str:
    """Auto-detect Python framework from imports and patterns."""
    if "from django" in source_code or "import django" in source_code:
        return "django"
    if "from pydantic" in source_code or "BaseModel" in source_code:
        return "pydantic"
    if "from sqlalchemy" in source_code or "declarative_base" in source_code:
        return "sqlalchemy"
    if "@dataclass" in source_code:
        return "dataclass"
    return "unknown"


def _generate_yaml_from_entity(entity, detected_patterns: list[str]) -> str:
    """Generate SpecQL YAML from ParsedEntity."""
    yaml_dict = {
        "entity": entity.entity_name,
        "schema": entity.namespace or "public",
        "description": entity.docstring or f"Auto-generated from {entity.entity_name}",
        "fields": {},
        "_metadata": {
            "source_language": "python",
            "patterns": detected_patterns,
            "generated_by": "specql-reverse-python",
        },
    }

    # Convert fields
    for field in entity.fields:
        field_type = field.field_type
        if not field.required:
            field_type = f"{field_type}?"
        if field.is_foreign_key and field.foreign_key_target:
            field_type = f"ref({field.foreign_key_target})"
        yaml_dict["fields"][field.field_name] = field_type

    return yaml.dump(yaml_dict, default_flow_style=False, sort_keys=False)


@click.command()
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("-o", "--output-dir", required=True, type=click.Path(), help="Output directory")
@click.option(
    "--framework",
    type=click.Choice(["django", "fastapi", "flask", "sqlalchemy", "pydantic", "dataclass"]),
    help="Framework override (auto-detected if not specified)",
)
@click.option("--preview", is_flag=True, help="Preview without writing")
def python(files, output_dir, framework, preview, **kwargs):
    """Reverse engineer Python models to SpecQL YAML.

    Supports Django, FastAPI, Flask-SQLAlchemy, SQLAlchemy, Pydantic, and dataclasses.

    Examples:

        specql reverse python src/models.py -o entities/

        specql reverse python app/models/ -o entities/ --framework=django

        specql reverse python schemas/*.py -o entities/ --preview
    """
    with handle_cli_error():
        output.info(f"Reversing {len(files)} Python file(s)")

        # Import parser
        try:
            from reverse_engineering.python_ast_parser import PythonASTParser
        except ImportError as e:
            output.error(f"Python parser not available: {e}")
            raise click.Abort() from e

        parser = PythonASTParser()

        # Prepare output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        all_entities = []

        for file_path in files:
            path = Path(file_path)
            output.info(f"  Parsing: {path.name}")

            source_code = path.read_text()

            # Detect or use specified framework
            detected_framework = framework or _detect_framework(source_code)
            output.info(f"    Framework: {detected_framework}")

            # Parse entities
            try:
                entities = parser.parse(source_code, str(path))

                for entity in entities:
                    # Detect patterns
                    patterns = parser.detect_patterns(entity)
                    all_entities.append((entity, patterns, path.name))

            except Exception as e:
                output.warning(f"    Failed to parse: {e}")
                continue

        output.info(f"  Found {len(all_entities)} entity/entities")

        if preview:
            output.info("Preview mode - showing what would be generated:")
            for entity, patterns, source_file in all_entities:
                output.info(f"    {entity.entity_name}.yaml (from {source_file})")
            return

        # Generate YAML files
        generated_files = []
        for entity, patterns, source_file in all_entities:
            yaml_content = _generate_yaml_from_entity(entity, patterns)

            yaml_path = output_path / f"{entity.entity_name.lower()}.yaml"
            yaml_path.write_text(yaml_content)
            generated_files.append(yaml_path.name)
            output.success(f"    Created: {yaml_path.name}")

        output.success(f"Generated {len(generated_files)} file(s)")
```

#### Phase 1.3: REFACTOR & QA

```bash
# Run tests
uv run pytest tests/unit/cli/commands/reverse/test_python.py -v

# Verify CLI help
uv run specql reverse python --help

# Integration test
echo 'from django.db import models
class Contact(models.Model):
    email = models.CharField(max_length=255)
' > /tmp/test_model.py
uv run specql reverse python /tmp/test_model.py -o /tmp/out/ --preview
```

---

## Task 2: TypeScript Reverse Engineering

**Priority**: High
**Effort**: 3 hours
**Location**: `src/cli/commands/reverse/typescript.py`

### Backend Parsers Available

- `reverse_engineering/typescript_parser.py` - `TypeScriptParser` class
  - Extracts: Express routes, Fastify routes, Next.js API routes, Server Actions
  - Uses: `tree-sitter-language-pack` (165+ languages)

- `reverse_engineering/prisma_parser.py` - `PrismaParser` class
  - Parses: Prisma schema files (`.prisma`)
  - Returns: Models with fields, relations, enums

- `reverse_engineering/typescript/` - Framework-specific extractors
  - `express_extractor.py`
  - `fastify_extractor.py`
  - `nextjs_pages_extractor.py`
  - `nextjs_app_extractor.py`

### Implementation Steps

#### Phase 2.1: RED - Write Failing Tests

Create `tests/unit/cli/commands/reverse/test_typescript.py`:

```python
"""Tests for reverse typescript CLI command."""

import pytest
from pathlib import Path
from click.testing import CliRunner


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def sample_prisma_schema():
    return '''
model Contact {
  id        Int      @id @default(autoincrement())
  email     String   @unique
  company   Company  @relation(fields: [companyId], references: [id])
  companyId Int
  status    Status   @default(LEAD)
  createdAt DateTime @default(now())
}

model Company {
  id       Int       @id @default(autoincrement())
  name     String
  contacts Contact[]
}

enum Status {
  LEAD
  QUALIFIED
  CUSTOMER
}
'''


@pytest.fixture
def sample_express_routes():
    return '''
import express from 'express';
const router = express.Router();

router.get('/contacts', getContacts);
router.post('/contacts', createContact);
router.get('/contacts/:id', getContactById);
router.put('/contacts/:id', updateContact);
router.delete('/contacts/:id', deleteContact);

export default router;
'''


@pytest.fixture
def sample_nextjs_app_route():
    return '''
import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  const contacts = await getContacts();
  return NextResponse.json(contacts);
}

export async function POST(request: Request) {
  const body = await request.json();
  const contact = await createContact(body);
  return NextResponse.json(contact);
}
'''


def test_reverse_typescript_requires_files():
    """reverse typescript should require file arguments."""
    from cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["reverse", "typescript"])

    assert result.exit_code != 0
    assert "Missing argument" in result.output


def test_reverse_typescript_parses_prisma_schema(cli_runner, sample_prisma_schema):
    """reverse typescript should parse Prisma schema files."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("schema.prisma").write_text(sample_prisma_schema)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "typescript", "schema.prisma", "-o", "out/"]
        )

        assert result.exit_code == 0
        yaml_files = list(Path("out/").glob("*.yaml"))
        assert len(yaml_files) >= 1


def test_reverse_typescript_parses_express_routes(cli_runner, sample_express_routes):
    """reverse typescript should parse Express routes."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("routes.ts").write_text(sample_express_routes)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "typescript", "routes.ts", "-o", "out/"]
        )

        # Should detect routes even if no entities
        assert result.exit_code == 0


def test_reverse_typescript_parses_nextjs_app_route(cli_runner, sample_nextjs_app_route):
    """reverse typescript should parse Next.js App Router routes."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("route.ts").write_text(sample_nextjs_app_route)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "typescript", "route.ts", "-o", "out/"]
        )

        assert result.exit_code == 0


def test_reverse_typescript_preview_mode(cli_runner, sample_prisma_schema):
    """reverse typescript --preview should not write files."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("schema.prisma").write_text(sample_prisma_schema)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "typescript", "schema.prisma", "-o", "out/", "--preview"]
        )

        assert result.exit_code == 0
        yaml_files = list(Path("out/").glob("*.yaml"))
        assert len(yaml_files) == 0


def test_reverse_typescript_auto_detects_file_type(cli_runner, sample_prisma_schema):
    """reverse typescript should auto-detect Prisma vs TypeScript."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("schema.prisma").write_text(sample_prisma_schema)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "typescript", "schema.prisma", "-o", "out/"]
        )

        assert result.exit_code == 0
        assert "prisma" in result.output.lower() or "Prisma" in result.output
```

#### Phase 2.2: GREEN - Implement CLI Integration

Update `src/cli/commands/reverse/typescript.py`:

```python
"""
Reverse TypeScript subcommand - Convert TypeScript/Prisma to SpecQL YAML.

Integrates with:
- PrismaParser: Parses .prisma schema files
- TypeScriptParser: Extracts Express/Fastify/Next.js routes
"""

from pathlib import Path
import yaml

import click

from cli.utils.error_handler import handle_cli_error
from cli.utils.output import output


def _is_prisma_file(file_path: Path) -> bool:
    """Check if file is a Prisma schema."""
    return file_path.suffix == ".prisma"


def _generate_yaml_from_prisma_model(model) -> str:
    """Generate SpecQL YAML from Prisma model."""
    yaml_dict = {
        "entity": model.name,
        "schema": "public",
        "description": f"Auto-generated from Prisma model {model.name}",
        "fields": {},
        "_metadata": {
            "source_language": "prisma",
            "generated_by": "specql-reverse-typescript",
        },
    }

    for field in model.fields:
        field_type = _map_prisma_type(field.type_name, field.is_relation)
        if field.is_optional:
            field_type = f"{field_type}?"
        if field.is_relation and field.relation_name:
            field_type = f"ref({field.relation_name})"
        yaml_dict["fields"][field.name] = field_type

    return yaml.dump(yaml_dict, default_flow_style=False, sort_keys=False)


def _map_prisma_type(prisma_type: str, is_relation: bool = False) -> str:
    """Map Prisma types to SpecQL types."""
    type_map = {
        "String": "text",
        "Int": "integer",
        "BigInt": "bigint",
        "Float": "float",
        "Decimal": "decimal",
        "Boolean": "boolean",
        "DateTime": "timestamp",
        "Json": "json",
        "Bytes": "binary",
    }
    return type_map.get(prisma_type, "text")


@click.command()
@click.argument("files", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("-o", "--output-dir", required=True, type=click.Path(), help="Output directory")
@click.option(
    "--framework",
    type=click.Choice(["express", "fastify", "nextjs", "prisma"]),
    help="Framework override (auto-detected if not specified)",
)
@click.option("--preview", is_flag=True, help="Preview without writing")
def typescript(files, output_dir, framework, preview, **kwargs):
    """Reverse engineer TypeScript/Prisma to SpecQL YAML.

    Supports Prisma schemas, Express routes, Fastify routes, and Next.js.

    Examples:

        specql reverse typescript prisma/schema.prisma -o entities/

        specql reverse typescript src/routes/*.ts -o entities/

        specql reverse typescript app/api/**/route.ts -o entities/
    """
    with handle_cli_error():
        output.info(f"Reversing {len(files)} TypeScript/Prisma file(s)")

        # Prepare output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        all_entities = []
        all_routes = []

        for file_path in files:
            path = Path(file_path)
            output.info(f"  Parsing: {path.name}")

            if _is_prisma_file(path):
                # Parse Prisma schema
                try:
                    from reverse_engineering.prisma_parser import PrismaParser

                    parser = PrismaParser()
                    source_code = path.read_text()
                    models = parser.parse(source_code)

                    output.info(f"    Detected: Prisma schema ({len(models)} models)")
                    all_entities.extend((model, path.name) for model in models)

                except ImportError:
                    output.warning("    Prisma parser not available (needs tree-sitter)")
                except Exception as e:
                    output.warning(f"    Failed to parse Prisma: {e}")
            else:
                # Parse TypeScript routes
                try:
                    from reverse_engineering.typescript_parser import TypeScriptParser

                    parser = TypeScriptParser()
                    source_code = path.read_text()

                    # Try different route extractors based on content
                    routes = []

                    # Express/Fastify routes
                    routes.extend(parser.extract_routes(source_code))

                    # Next.js App Router
                    if "route.ts" in str(path) or "route.js" in str(path):
                        routes.extend(parser.extract_nextjs_app_routes(source_code, str(path)))

                    # Next.js Pages Router
                    if "/pages/api/" in str(path):
                        routes.extend(parser.extract_nextjs_pages_routes(source_code, str(path)))

                    # Server Actions
                    routes.extend(parser.extract_server_actions(source_code))

                    if routes:
                        output.info(f"    Detected: {len(routes)} route(s)")
                        all_routes.extend((route, path.name) for route in routes)
                    else:
                        output.info("    No routes found")

                except ImportError as e:
                    output.warning(f"    TypeScript parser not available: {e}")
                except Exception as e:
                    output.warning(f"    Failed to parse TypeScript: {e}")

        output.info(f"  Found {len(all_entities)} model(s), {len(all_routes)} route(s)")

        if preview:
            output.info("Preview mode - showing what would be generated:")
            for model, source_file in all_entities:
                output.info(f"    {model.name.lower()}.yaml (from {source_file})")
            return

        # Generate YAML for Prisma models
        generated_files = []
        for model, source_file in all_entities:
            yaml_content = _generate_yaml_from_prisma_model(model)
            yaml_path = output_path / f"{model.name.lower()}.yaml"
            yaml_path.write_text(yaml_content)
            generated_files.append(yaml_path.name)
            output.success(f"    Created: {yaml_path.name}")

        # TODO: Generate YAML for routes as actions

        output.success(f"Generated {len(generated_files)} file(s)")
```

---

## Task 3: Rust Reverse Engineering

**Priority**: Medium
**Effort**: 4 hours
**Location**: `src/cli/commands/reverse/rust.py`

### Backend Parsers Available

- `reverse_engineering/rust_parser.py` - `RustParser` class
  - Parses: Structs, Diesel tables, SeaORM entities, route handlers
  - Supports: Actix-web, Rocket, Axum, Warp, Tide frameworks
  - Uses: `tree-sitter-language-pack` (165+ languages)

- `reverse_engineering/seaorm_parser.py` - `SeaORMParser` class
  - Parses: SeaORM entity definitions

- `reverse_engineering/rust/` - Framework-specific extractors
  - `axum_extractor.py`
  - `rocket_extractor.py`
  - `actix_extractor.py`

### Implementation Steps

#### Phase 3.1: RED - Write Failing Tests

Create `tests/unit/cli/commands/reverse/test_rust.py`:

```python
"""Tests for reverse rust CLI command."""

import pytest
from pathlib import Path
from click.testing import CliRunner


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def sample_diesel_model():
    return '''
use diesel::prelude::*;

#[derive(Queryable, Insertable)]
#[table_name = "contacts"]
pub struct Contact {
    pub id: i32,
    pub email: String,
    pub company_id: Option<i32>,
    pub status: String,
    pub created_at: NaiveDateTime,
}
'''


@pytest.fixture
def sample_seaorm_model():
    return '''
use sea_orm::entity::prelude::*;

#[derive(Clone, Debug, PartialEq, DeriveEntityModel)]
#[sea_orm(table_name = "contacts")]
pub struct Model {
    #[sea_orm(primary_key)]
    pub id: i32,
    pub email: String,
    pub company_id: Option<i32>,
    pub status: String,
}
'''


@pytest.fixture
def sample_actix_routes():
    return '''
use actix_web::{get, post, web, HttpResponse};

#[get("/contacts")]
async fn get_contacts() -> HttpResponse {
    HttpResponse::Ok().json(vec![])
}

#[post("/contacts")]
async fn create_contact(body: web::Json<ContactInput>) -> HttpResponse {
    HttpResponse::Created().json(body.into_inner())
}

#[get("/contacts/{id}")]
async fn get_contact(path: web::Path<i32>) -> HttpResponse {
    HttpResponse::Ok().json(Contact::default())
}
'''


def test_reverse_rust_requires_files():
    """reverse rust should require file arguments."""
    from cli.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["reverse", "rust"])

    assert result.exit_code != 0
    assert "Missing argument" in result.output


def test_reverse_rust_parses_diesel_model(cli_runner, sample_diesel_model):
    """reverse rust should parse Diesel models."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("models.rs").write_text(sample_diesel_model)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "rust", "models.rs", "-o", "out/"]
        )

        assert result.exit_code == 0


def test_reverse_rust_parses_seaorm_model(cli_runner, sample_seaorm_model):
    """reverse rust should parse SeaORM models."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("entity.rs").write_text(sample_seaorm_model)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "rust", "entity.rs", "-o", "out/"]
        )

        assert result.exit_code == 0


def test_reverse_rust_parses_actix_routes(cli_runner, sample_actix_routes):
    """reverse rust should parse Actix-web routes."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("routes.rs").write_text(sample_actix_routes)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "rust", "routes.rs", "-o", "out/"]
        )

        assert result.exit_code == 0


def test_reverse_rust_preview_mode(cli_runner, sample_diesel_model):
    """reverse rust --preview should not write files."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("models.rs").write_text(sample_diesel_model)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "rust", "models.rs", "-o", "out/", "--preview"]
        )

        assert result.exit_code == 0
        yaml_files = list(Path("out/").glob("*.yaml"))
        assert len(yaml_files) == 0


def test_reverse_rust_orm_option(cli_runner, sample_diesel_model):
    """reverse rust --orm should specify ORM type."""
    from cli.main import app

    with cli_runner.isolated_filesystem():
        Path("models.rs").write_text(sample_diesel_model)
        Path("out").mkdir()

        result = cli_runner.invoke(
            app, ["reverse", "rust", "models.rs", "-o", "out/", "--orm", "diesel"]
        )

        assert result.exit_code == 0
```

#### Phase 3.2: GREEN - Implement CLI Integration

Similar pattern to Python and TypeScript - integrate with `RustParser` and `RustReverseEngineeringService`.

---

## Task 4: Java Reverse Engineering (New CLI Command)

**Priority**: Low
**Effort**: 4 hours
**Location**: `src/cli/commands/reverse/java.py` (new file)

### Backend Parsers Available

- `reverse_engineering/java/java_parser.py` - `JavaParser` class
  - Parses: JPA/Hibernate entities
  - Uses: JDT (Java Development Tools) bridge

- `reverse_engineering/java/jpa_to_specql.py` - Converter

### Implementation Steps

1. Create `src/cli/commands/reverse/java.py`
2. Register in `src/cli/commands/reverse/__init__.py`
3. Add to reverse group in `src/cli/main.py`
4. Write tests in `tests/unit/cli/commands/reverse/test_java.py`

---

## Testing Checklist

After implementing each language:

```bash
# Run language-specific tests
uv run pytest tests/unit/cli/commands/reverse/test_python.py -v
uv run pytest tests/unit/cli/commands/reverse/test_typescript.py -v
uv run pytest tests/unit/cli/commands/reverse/test_rust.py -v
uv run pytest tests/unit/cli/commands/reverse/test_java.py -v

# Run all CLI tests
uv run pytest tests/unit/cli/ -v

# Verify CLI help
uv run specql reverse --help
uv run specql reverse python --help
uv run specql reverse typescript --help
uv run specql reverse rust --help

# Integration smoke tests
uv run specql reverse python /path/to/django/models.py -o /tmp/out/ --preview
uv run specql reverse typescript /path/to/schema.prisma -o /tmp/out/ --preview
```

---

## Success Criteria

### Phase 1: Python (Task 1)
- [x] `specql reverse python` parses Django models
- [x] `specql reverse python` parses Pydantic models
- [x] `specql reverse python` parses SQLAlchemy models
- [x] 10+ tests passing (19 tests)
- [x] Status updated to Stable

### Phase 2: TypeScript (Task 2)
- [x] `specql reverse typescript` parses Prisma schemas
- [x] `specql reverse typescript` parses Express routes
- [x] `specql reverse typescript` parses Next.js routes
- [x] 10+ tests passing (17 tests)
- [x] Status updated to Stable

### Phase 3: Rust (Task 3)
- [x] `specql reverse rust` parses Diesel models
- [x] `specql reverse rust` parses SeaORM entities
- [x] `specql reverse rust` parses Actix-web routes
- [x] 10+ tests passing (16 tests)
- [x] Status updated to Stable

### Phase 4: Java (Task 4)
- [ ] `specql reverse java` command exists
- [ ] Parses JPA/Hibernate entities
- [ ] 8+ tests passing
- [ ] Status updated to Stable

---

## Dependencies

| Language | Required Packages | Notes |
|----------|-------------------|-------|
| Python | None (uses `ast`) | Built-in Python AST module |
| TypeScript | `tree-sitter-language-pack` | Already in `[reverse]` extra |
| Prisma | `tree-sitter-language-pack` | Already in `[reverse]` extra |
| Rust | `tree-sitter-language-pack` | Already in `[reverse]` extra |
| Java | JDT bridge | May require Java runtime |

**Note**: `tree-sitter-language-pack` is already installed as part of the `[reverse]` extra and supports 165+ languages. No regex fallbacks needed.

---

## File Structure After Implementation

```
src/cli/commands/reverse/
├── __init__.py
├── sql.py         # Stable (done)
├── python.py      # To implement
├── typescript.py  # To implement
├── rust.py        # To implement
├── java.py        # To create
└── project.py     # Beta (auto-detection)

tests/unit/cli/commands/reverse/
├── __init__.py
├── test_sql.py           # 17 tests (done)
├── test_python.py        # To create (~10 tests)
├── test_typescript.py    # To create (~10 tests)
├── test_rust.py          # To create (~10 tests)
└── test_java.py          # To create (~8 tests)
```

---

**Document Version**: 1.0
**Last Updated**: 2025-11-21
**Next Agent**: Start with Task 1 (Python reverse engineering)
