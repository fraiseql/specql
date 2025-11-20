# tests/unit/reverse_engineering/test_typescript_parser.py


from reverse_engineering.typescript_parser import TypeScriptParser


class TestTypeScriptParser:
    """Test TypeScript route detection"""

    def test_parse_express_routes(self):
        """Test parsing Express.js routes"""
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

        parser = TypeScriptParser()
        routes = parser.extract_routes(code)

        assert len(routes) == 2
        assert routes[0].method == "POST"
        assert routes[0].path == "/contacts"
        assert routes[0].framework == "express"

    def test_parse_fastify_routes(self):
        """Test parsing Fastify routes"""
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

        parser = TypeScriptParser()
        routes = parser.extract_routes(code)

        assert len(routes) == 2
        assert routes[1].method == "GET"
        assert routes[1].path == "/contacts/:id"


class TestNextJSParser:
    """Test Next.js route detection"""

    def test_parse_nextjs_pages_api_route(self):
        """Test parsing Next.js Pages Router API routes"""
        # File: pages/api/contacts.ts
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

        parser = TypeScriptParser()
        routes = parser.extract_nextjs_pages_routes(code, file_path="pages/api/contacts.ts")

        assert len(routes) == 2
        assert routes[0].method == "POST"
        assert routes[0].path == "/api/contacts"

    def test_parse_nextjs_app_router_route(self):
        """Test parsing Next.js App Router route handlers"""
        # File: app/api/contacts/route.ts
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

        parser = TypeScriptParser()
        routes = parser.extract_nextjs_app_routes(code, file_path="app/api/contacts/route.ts")

        assert len(routes) == 2
        assert routes[0].method == "GET"
        assert routes[1].method == "POST"

    def test_parse_nextjs_server_actions(self):
        """Test parsing Next.js Server Actions"""
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

        parser = TypeScriptParser()
        actions = parser.extract_server_actions(code)

        assert len(actions) == 2
        assert actions[0].name == "createContact"
        assert actions[1].name == "updateContactStatus"
