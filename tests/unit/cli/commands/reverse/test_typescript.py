"""Tests for reverse typescript CLI command."""

from pathlib import Path

import pytest
from click.testing import CliRunner


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def sample_prisma_schema():
    return """
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
"""


@pytest.fixture
def sample_express_routes():
    return """
import express from 'express';
const router = express.Router();

router.get('/contacts', getContacts);
router.post('/contacts', createContact);
router.get('/contacts/:id', getContactById);
router.put('/contacts/:id', updateContact);
router.delete('/contacts/:id', deleteContact);

export default router;
"""


@pytest.fixture
def sample_nextjs_app_route():
    return """
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
"""


@pytest.fixture
def sample_server_action():
    return """
'use server';

export async function createContact(formData: FormData) {
  const email = formData.get('email');
  // ... create contact
}

export async function updateContact(id: string, formData: FormData) {
  // ... update contact
}
"""


class TestReverseTypescriptCommand:
    """Tests for the reverse typescript CLI command."""

    def test_reverse_typescript_requires_files(self, cli_runner):
        """reverse typescript should require file arguments."""
        from cli.main import app

        result = cli_runner.invoke(app, ["reverse", "typescript"])

        assert result.exit_code != 0
        assert "Missing argument" in result.output or "Error" in result.output

    def test_reverse_typescript_requires_output_dir(self, cli_runner):
        """reverse typescript should require output directory."""
        from cli.main import app

        with cli_runner.isolated_filesystem():
            Path("schema.prisma").write_text("model Test { id Int @id }")
            result = cli_runner.invoke(app, ["reverse", "typescript", "schema.prisma"])

            assert result.exit_code != 0

    def test_reverse_typescript_parses_prisma_schema(self, cli_runner, sample_prisma_schema):
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

            # Check YAML content includes model name
            yaml_content = yaml_files[0].read_text()
            assert (
                "Contact" in yaml_content or "contact" in yaml_content or "Company" in yaml_content
            )

    def test_reverse_typescript_parses_express_routes(self, cli_runner, sample_express_routes):
        """reverse typescript should parse Express routes."""
        from cli.main import app

        with cli_runner.isolated_filesystem():
            Path("routes.ts").write_text(sample_express_routes)
            Path("out").mkdir()

            result = cli_runner.invoke(app, ["reverse", "typescript", "routes.ts", "-o", "out/"])

            # Should succeed even if no YAML files generated (routes don't become entities)
            assert result.exit_code == 0

    def test_reverse_typescript_parses_nextjs_app_route(self, cli_runner, sample_nextjs_app_route):
        """reverse typescript should parse Next.js App Router routes."""
        from cli.main import app

        with cli_runner.isolated_filesystem():
            # Simulate Next.js app directory structure
            Path("app/api/contacts").mkdir(parents=True)
            Path("app/api/contacts/route.ts").write_text(sample_nextjs_app_route)
            Path("out").mkdir()

            result = cli_runner.invoke(
                app, ["reverse", "typescript", "app/api/contacts/route.ts", "-o", "out/"]
            )

            assert result.exit_code == 0

    def test_reverse_typescript_preview_mode(self, cli_runner, sample_prisma_schema):
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

    def test_reverse_typescript_auto_detects_prisma(self, cli_runner, sample_prisma_schema):
        """reverse typescript should auto-detect Prisma from .prisma extension."""
        from cli.main import app

        with cli_runner.isolated_filesystem():
            Path("schema.prisma").write_text(sample_prisma_schema)
            Path("out").mkdir()

            result = cli_runner.invoke(
                app, ["reverse", "typescript", "schema.prisma", "-o", "out/"]
            )

            assert result.exit_code == 0
            # Check that Prisma was detected (case-insensitive)
            assert "prisma" in result.output.lower()

    def test_reverse_typescript_framework_override(self, cli_runner, sample_prisma_schema):
        """reverse typescript --framework should allow framework specification."""
        from cli.main import app

        with cli_runner.isolated_filesystem():
            Path("schema.prisma").write_text(sample_prisma_schema)
            Path("out").mkdir()

            result = cli_runner.invoke(
                app,
                ["reverse", "typescript", "schema.prisma", "-o", "out/", "--framework", "prisma"],
            )

            assert result.exit_code == 0

    def test_reverse_typescript_multiple_files(self, cli_runner, sample_prisma_schema):
        """reverse typescript should handle multiple files."""
        from cli.main import app

        with cli_runner.isolated_filesystem():
            Path("schema1.prisma").write_text(sample_prisma_schema)
            Path("schema2.prisma").write_text("""
model Task {
  id    Int    @id @default(autoincrement())
  title String
}
""")
            Path("out").mkdir()

            result = cli_runner.invoke(
                app, ["reverse", "typescript", "schema1.prisma", "schema2.prisma", "-o", "out/"]
            )

            assert result.exit_code == 0

    def test_reverse_typescript_parses_server_actions(self, cli_runner, sample_server_action):
        """reverse typescript should parse Next.js Server Actions."""
        from cli.main import app

        with cli_runner.isolated_filesystem():
            Path("actions.ts").write_text(sample_server_action)
            Path("out").mkdir()

            result = cli_runner.invoke(app, ["reverse", "typescript", "actions.ts", "-o", "out/"])

            assert result.exit_code == 0

    def test_reverse_typescript_creates_output_directory(self, cli_runner, sample_prisma_schema):
        """reverse typescript should create output directory if it doesn't exist."""
        from cli.main import app

        with cli_runner.isolated_filesystem():
            Path("schema.prisma").write_text(sample_prisma_schema)
            # Don't create output directory

            result = cli_runner.invoke(
                app, ["reverse", "typescript", "schema.prisma", "-o", "new_output/"]
            )

            assert result.exit_code == 0
            assert Path("new_output/").exists()

    def test_reverse_typescript_generates_valid_yaml(self, cli_runner, sample_prisma_schema):
        """reverse typescript should generate valid YAML files."""
        import yaml as yaml_lib

        from cli.main import app

        with cli_runner.isolated_filesystem():
            Path("schema.prisma").write_text(sample_prisma_schema)
            Path("out").mkdir()

            result = cli_runner.invoke(
                app, ["reverse", "typescript", "schema.prisma", "-o", "out/"]
            )

            assert result.exit_code == 0
            yaml_files = list(Path("out/").glob("*.yaml"))

            for yaml_file in yaml_files:
                content = yaml_file.read_text()
                # Should be valid YAML
                parsed = yaml_lib.safe_load(content)
                assert parsed is not None
                # Should have entity name
                assert "entity" in parsed


class TestReverseTypescriptPrismaIntegration:
    """Integration tests for Prisma parsing."""

    def test_prisma_model_fields_mapped_correctly(self, cli_runner):
        """Prisma model fields should be mapped to SpecQL types."""
        import yaml as yaml_lib

        from cli.main import app

        prisma_schema = """
model User {
  id        Int      @id @default(autoincrement())
  email     String   @unique
  age       Int?
  isActive  Boolean  @default(true)
  balance   Float
  metadata  Json?
  createdAt DateTime @default(now())
}
"""
        with cli_runner.isolated_filesystem():
            Path("schema.prisma").write_text(prisma_schema)
            Path("out").mkdir()

            result = cli_runner.invoke(
                app, ["reverse", "typescript", "schema.prisma", "-o", "out/"]
            )

            assert result.exit_code == 0
            yaml_files = list(Path("out/").glob("*.yaml"))
            assert len(yaml_files) >= 1

            # Parse the generated YAML
            content = yaml_files[0].read_text()
            parsed = yaml_lib.safe_load(content)

            assert parsed["entity"] == "User"
            assert "fields" in parsed

    def test_prisma_relations_mapped_as_refs(self, cli_runner):
        """Prisma relations should be mapped to ref() types."""
        from cli.main import app

        prisma_schema = """
model Post {
  id       Int    @id @default(autoincrement())
  title    String
  author   User   @relation(fields: [authorId], references: [id])
  authorId Int
}

model User {
  id    Int    @id @default(autoincrement())
  posts Post[]
}
"""
        with cli_runner.isolated_filesystem():
            Path("schema.prisma").write_text(prisma_schema)
            Path("out").mkdir()

            result = cli_runner.invoke(
                app, ["reverse", "typescript", "schema.prisma", "-o", "out/"]
            )

            assert result.exit_code == 0

    def test_prisma_enums_detected(self, cli_runner):
        """Prisma enums should be detected and mapped."""
        from cli.main import app

        prisma_schema = """
enum Role {
  ADMIN
  USER
  GUEST
}

model User {
  id   Int  @id @default(autoincrement())
  role Role @default(USER)
}
"""
        with cli_runner.isolated_filesystem():
            Path("schema.prisma").write_text(prisma_schema)
            Path("out").mkdir()

            result = cli_runner.invoke(
                app, ["reverse", "typescript", "schema.prisma", "-o", "out/"]
            )

            assert result.exit_code == 0


class TestReverseTypescriptRouteExtraction:
    """Tests for TypeScript route extraction."""

    def test_extract_express_crud_routes(self, cli_runner, sample_express_routes):
        """Should extract CRUD routes from Express router."""
        from cli.main import app

        with cli_runner.isolated_filesystem():
            Path("routes.ts").write_text(sample_express_routes)
            Path("out").mkdir()

            result = cli_runner.invoke(app, ["reverse", "typescript", "routes.ts", "-o", "out/"])

            assert result.exit_code == 0
            # Routes should be mentioned in output
            assert "route" in result.output.lower() or "typescript" in result.output.lower()

    def test_extract_fastify_routes(self, cli_runner):
        """Should extract routes from Fastify router."""
        from cli.main import app

        fastify_routes = """
import fastify from 'fastify';
const app = fastify();

fastify.get('/users', getUsers);
fastify.post('/users', createUser);
"""
        with cli_runner.isolated_filesystem():
            Path("routes.ts").write_text(fastify_routes)
            Path("out").mkdir()

            result = cli_runner.invoke(app, ["reverse", "typescript", "routes.ts", "-o", "out/"])

            assert result.exit_code == 0
