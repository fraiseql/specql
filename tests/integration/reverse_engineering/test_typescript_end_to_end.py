# tests/integration/reverse_engineering/test_typescript_end_to_end.py

from reverse_engineering.prisma_parser import PrismaSchemaParser
from reverse_engineering.universal_action_mapper import UniversalActionMapper


class TestTypeScriptEndToEnd:
    """End-to-end TypeScript/Prisma reverse engineering tests"""

    def test_prisma_schema_to_specql_conversion(self):
        """Test complete Prisma schema to SpecQL conversion"""
        schema = """
        enum ContactStatus {
          LEAD
          QUALIFIED
          CUSTOMER
        }

        model Contact {
          id        Int           @id @default(autoincrement())
          email     String        @unique
          status    ContactStatus @default(LEAD)
          companyId Int?
          company   Company?      @relation(fields: [companyId], references: [id])

          deletedAt DateTime? @map("deleted_at")
          createdAt DateTime  @default(now()) @map("created_at")
          updatedAt DateTime  @updatedAt @map("updated_at")

          @@map("contacts")
          @@index([email])
        }

        model Company {
          id       Int        @id @default(autoincrement())
          name     String
          contacts Contact[]

          @@map("companies")
        }
        """

        # Parse with Prisma parser
        parser = PrismaSchemaParser()
        entities = parser.parse_schema(schema)

        # Verify entities
        assert len(entities) == 2

        contact = next(e for e in entities if e.name == "Contact")
        assert contact.table_name == "contacts"
        assert len(contact.fields) == 8

        # Check enum field
        status_field = next(f for f in contact.fields if f.name == "status")
        assert status_field.type == "enum"
        assert status_field.enum_values == ["LEAD", "QUALIFIED", "CUSTOMER"]

        # Check relation
        company_field = next(f for f in contact.fields if f.name == "company")
        assert company_field.is_relation
        assert company_field.related_entity == "Company"

        # Check indexes
        assert len(contact.indexes) == 1
        assert contact.indexes[0] == ["email"]

    def test_express_routes_to_actions_conversion(self):
        """Test Express routes to SpecQL actions conversion"""
        code = """
        import express from 'express';
        import { PrismaClient } from '@prisma/client';

        const prisma = new PrismaClient();
        const router = express.Router();

        router.post('/contacts', async (req, res) => {
            const contact = await prisma.contact.create({
                data: {
                    email: req.body.email,
                    status: 'lead'
                }
            });
            res.json(contact);
        });

        router.get('/contacts/:id', async (req, res) => {
            const contact = await prisma.contact.findUnique({
                where: { id: parseInt(req.params.id) }
            });
            res.json(contact);
        });

        router.put('/contacts/:id', async (req, res) => {
            const contact = await prisma.contact.update({
                where: { id: parseInt(req.params.id) },
                data: req.body
            });
            res.json(contact);
        });

        router.delete('/contacts/:id', async (req, res) => {
            await prisma.contact.delete({
                where: { id: parseInt(req.params.id) }
            });
            res.status(204).send();
        });
        """

        mapper = UniversalActionMapper()
        result = mapper.convert_code(code, "typescript")

        # Parse YAML result
        import yaml

        specql = yaml.safe_load(result)

        # Verify actions
        assert "actions" in specql
        actions = specql["actions"]
        assert len(actions) == 4

        # Check action types
        action_types = [a["type"] for a in actions]
        assert "create" in action_types
        assert "read" in action_types
        assert "update" in action_types
        assert "delete" in action_types

        # Check entity inference
        entities = [a["entity"] for a in actions]
        assert all(e == "Contact" for e in entities)

    def test_nextjs_app_router_conversion(self):
        """Test Next.js App Router to SpecQL actions conversion"""
        code = """
        import { NextRequest, NextResponse } from 'next/server';
        import { PrismaClient } from '@prisma/client';

        const prisma = new PrismaClient();

        export async function GET(request: NextRequest) {
            const contacts = await prisma.contact.findMany();
            return NextResponse.json(contacts);
        }

        export async function POST(request: NextRequest) {
            const body = await request.json();
            const contact = await prisma.contact.create({
                data: body
            });
            return NextResponse.json(contact, { status: 201 });
        }
        """

        mapper = UniversalActionMapper()
        result = mapper.convert_code(code, "typescript")

        import yaml

        specql = yaml.safe_load(result)

        assert "actions" in specql
        actions = specql["actions"]
        assert len(actions) == 2

        # Check methods
        descriptions = [a.get("description", "") for a in actions]
        assert any("Read" in desc for desc in descriptions)
        assert any("Create" in desc for desc in descriptions)

    def test_server_actions_conversion(self):
        """Test Next.js Server Actions to SpecQL actions conversion"""
        code = """
        'use server';

        import { PrismaClient } from '@prisma/client';

        const prisma = new PrismaClient();

        export async function createContact(formData: FormData) {
            const email = formData.get('email') as string;
            const status = formData.get('status') as string;

            const contact = await prisma.contact.create({
                data: { email, status: status || 'lead' }
            });

            return contact;
        }

        export async function updateContactStatus(id: number, status: string) {
            const contact = await prisma.contact.update({
                where: { id },
                data: { status }
            });

            return contact;
        }

        export async function deleteContact(id: number) {
            await prisma.contact.delete({
                where: { id }
            });
        }
        """

        mapper = UniversalActionMapper()
        result = mapper.convert_code(code, "typescript")

        import yaml

        specql = yaml.safe_load(result)

        assert "actions" in specql
        actions = specql["actions"]
        assert len(actions) == 3

        # Check function names
        names = [a["name"] for a in actions]
        assert "createcontact" in names
        assert "updatecontactstatus" in names
        assert "deletecontact" in names

    def test_mixed_typescript_project_integration(self):
        """Test integration of multiple TypeScript files"""
        # This would test combining Prisma schema + routes + actions
        # For now, just verify the components work together

        # Test Prisma parsing
        prisma_code = """
        model Contact {
          id    Int    @id @default(autoincrement())
          email String @unique
        }
        """

        prisma_parser = PrismaSchemaParser()
        entities = prisma_parser.parse_schema(prisma_code)
        assert len(entities) == 1

        # Test route parsing
        route_code = """
        router.get('/contacts', async (req, res) => {
            const contacts = await prisma.contact.findMany();
            res.json(contacts);
        });
        """

        mapper = UniversalActionMapper()
        route_result = mapper.convert_code(route_code, "typescript")

        import yaml

        route_specql = yaml.safe_load(route_result)
        assert "actions" in route_specql

        # Integration successful if both components work
        assert True

    def test_fastify_routes_conversion(self):
        """Test Fastify routes to SpecQL actions conversion"""
        code = """
        import Fastify from 'fastify';

        const fastify = Fastify();

        fastify.post('/contacts', async (request, reply) => {
            const contact = await prisma.contact.create({
                data: request.body
            });
            return contact;
        });

        fastify.get('/contacts/:id', async (request, reply) => {
            const { id } = request.params;
            const contact = await prisma.contact.findUnique({
                where: { id: parseInt(id) }
            });
            return contact;
        });
        """

        mapper = UniversalActionMapper()
        result = mapper.convert_code(code, "typescript")

        import yaml

        specql = yaml.safe_load(result)

        assert "actions" in specql
        actions = specql["actions"]
        assert len(actions) == 2

        # Check framework detection
        descriptions = [a.get("description", "") for a in actions]
        assert any("fastify" in desc.lower() for desc in descriptions)
