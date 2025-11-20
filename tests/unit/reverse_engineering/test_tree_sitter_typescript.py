# tests/unit/reverse_engineering/test_tree_sitter_typescript.py

import pytest

from reverse_engineering.typescript.express_extractor import ExpressRouteExtractor
from reverse_engineering.typescript.fastify_extractor import FastifyRouteExtractor
from reverse_engineering.typescript.nextjs_app_extractor import NextJSAppExtractor
from reverse_engineering.typescript.nextjs_pages_extractor import NextJSPagesExtractor
from reverse_engineering.typescript.tree_sitter_typescript_parser import (
    TreeSitterTypeScriptParser,
)


class TestTreeSitterTypeScriptParser:
    """Test tree-sitter based TypeScript parsing"""

    @pytest.fixture
    def parser(self):
        return TreeSitterTypeScriptParser()

    def test_parse_express_routes(self):
        """Test parsing Express.js routes with tree-sitter"""
        extractor = ExpressRouteExtractor()

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
        """

        routes = extractor.extract_routes(code)

        assert len(routes) == 2
        assert routes[0].method == "POST"
        assert routes[0].path == "/contacts"

        assert routes[1].method == "GET"
        assert routes[1].path == "/contacts/:id"

    def test_parse_fastify_routes(self):
        """Test parsing Fastify routes with tree-sitter"""
        extractor = FastifyRouteExtractor()

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

        routes = extractor.extract_routes(code)

        assert len(routes) == 2
        assert routes[0].method == "POST"
        assert routes[0].path == "/contacts"

        assert routes[1].method == "GET"
        assert routes[1].path == "/contacts/:id"

    def test_parse_nextjs_pages_routes(self):
        """Test parsing Next.js Pages Router routes with tree-sitter"""
        extractor = NextJSPagesExtractor()

        code = """
        import type { NextApiRequest, NextApiResponse } from 'next';
        import { PrismaClient } from '@prisma/client';

        const prisma = new PrismaClient();

        export default async function handler(
            req: NextApiRequest,
            res: NextApiResponse
        ) {
            if (req.method === 'POST') {
                const contact = await prisma.contact.create({
                    data: req.body
                });
                res.status(201).json(contact);
            } else if (req.method === 'GET') {
                const contacts = await prisma.contact.findMany();
                res.json(contacts);
            }
        }
        """

        route = extractor.extract_route_from_file("pages/api/contacts.ts", code)

        assert route is not None
        assert route.path == "/api/contacts"
        assert not route.is_dynamic
        assert set(route.methods) == {"POST", "GET"}

    def test_parse_nextjs_app_routes(self):
        """Test parsing Next.js App Router routes with tree-sitter"""
        extractor = NextJSAppExtractor()

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

        route = extractor.extract_route_from_file("app/api/contacts/route.ts", code)

        assert route is not None
        assert route.path == "/api/contacts"
        assert not route.is_dynamic
        assert set(route.methods) == {"GET", "POST"}

    def test_parse_server_actions(self, parser):
        """Test parsing Next.js Server Actions with tree-sitter"""
        code = """
        'use server';

        import { PrismaClient } from '@prisma/client';

        const prisma = new PrismaClient();

        export async function createContact(formData: FormData) {
            const email = formData.get('email') as string;

            const contact = await prisma.contact.create({
                data: { email, status: 'lead' }
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
        """

        ast = parser.parse(code)
        assert ast is not None

        actions = parser.extract_server_actions(ast, code)

        assert len(actions) == 2
        assert actions[0].name == "createContact"
        assert actions[1].name == "updateContactStatus"

    def test_parse_complex_typescript(self, parser):
        """Test parsing complex TypeScript with generics and decorators"""
        code = """
        import express from 'express';
        import { PrismaClient } from '@prisma/client';

        const prisma = new PrismaClient();
        const router = express.Router();

        interface ContactData {
            email: string;
            status: 'lead' | 'customer';
        }

        router.post<{}, ContactData>('/contacts', async (req, res) => {
            const contact = await prisma.contact.create({
                data: {
                    email: req.body.email,
                    status: req.body.status || 'lead'
                }
            });
            res.json(contact);
        });

        export default router;
        """

        ast = parser.parse(code)
        assert ast is not None

        routes = parser.extract_routes(ast, code)

        assert len(routes) == 1
        assert routes[0].method == "POST"
        assert routes[0].path == "/contacts"
        assert routes[0].framework == "express"

    def test_parse_error_handling(self, parser):
        """Test error handling for invalid TypeScript code"""
        invalid_code = """
        import express from 'express'
        const router = express.Router()

        router.get('/contacts', (req, res) => {
            // Missing closing brace and parenthesis
            res.json({ error: 'incomplete' })
        """

        ast = parser.parse(invalid_code)
        # Tree-sitter returns ERROR node for invalid syntax
        assert ast.type == "ERROR"

    def test_empty_code(self, parser):
        """Test parsing empty code"""
        ast = parser.parse("")
        assert ast is not None  # Empty code still produces a valid AST

        routes = parser.extract_routes(ast, "")
        assert len(routes) == 0

    def test_no_routes(self, parser):
        """Test code with no routes"""
        code = """
        import { PrismaClient } from '@prisma/client';

        const prisma = new PrismaClient();

        export async function getContacts() {
            return await prisma.contact.findMany();
        }
        """

        ast = parser.parse(code)
        assert ast is not None

        routes = parser.extract_routes(ast, code)
        assert len(routes) == 0
