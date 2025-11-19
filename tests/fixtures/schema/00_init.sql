-- Initialize test database with required extensions and base schemas

-- Install required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- Create base schemas (framework schemas)
CREATE SCHEMA IF NOT EXISTS common;
CREATE SCHEMA IF NOT EXISTS app;
CREATE SCHEMA IF NOT EXISTS core;

-- Create app.mutation_result type (required for all actions)
-- This is the standard return type for FraiseQL mutations
CREATE TYPE app.mutation_result AS (
    success BOOLEAN,
    error_code TEXT,
    error_message TEXT,
    object_data JSONB,
    _meta JSONB
);

-- Test tenant schema and data for multi-tenant tests
CREATE SCHEMA IF NOT EXISTS management;

CREATE TABLE IF NOT EXISTS management.tb_tenant (
    pk_tenant INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    id UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    identifier TEXT NOT NULL UNIQUE,
    name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    created_by UUID,
    updated_by UUID
);

-- Insert test tenant for integration tests
INSERT INTO management.tb_tenant (id, identifier, name)
VALUES (
    '550e8400-e29b-41d4-a716-446655440000'::UUID,
    'test-tenant',
    'Test Tenant'
)
ON CONFLICT (identifier) DO NOTHING;

-- Create test user (for audit trails)
CREATE TABLE IF NOT EXISTS management.tb_user (
    pk_user INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    id UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    identifier TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- Insert test user
INSERT INTO management.tb_user (id, identifier, email)
VALUES (
    '660e8400-e29b-41d4-a716-446655440001'::UUID,
    'test-user',
    'test@example.com'
)
ON CONFLICT (identifier) DO NOTHING;

-- Grant permissions on schemas (needed for RLS)
GRANT USAGE ON SCHEMA common, app, core, management TO postgres;
GRANT ALL ON ALL TABLES IN SCHEMA common, app, core, management TO postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA common, app, core, management TO postgres;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA common, app, core, management TO postgres;
