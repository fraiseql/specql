-- SPECQL Registry Schema
-- PostgreSQL schema for domain, subdomain, and entity registration data

-- Create schema
CREATE SCHEMA IF NOT EXISTS specql_registry;

-- Domain table
CREATE TABLE specql_registry.tb_domain (
    pk_domain SERIAL PRIMARY KEY,
    domain_number VARCHAR(10) NOT NULL UNIQUE,
    domain_name VARCHAR(100) NOT NULL,
    description TEXT,
    multi_tenant BOOLEAN NOT NULL DEFAULT FALSE,
    aliases TEXT[] DEFAULT ARRAY[]::TEXT[]
);

-- Subdomain table
CREATE TABLE specql_registry.tb_subdomain (
    pk_subdomain SERIAL PRIMARY KEY,
    fk_domain INTEGER NOT NULL REFERENCES specql_registry.tb_domain(pk_domain) ON DELETE CASCADE,
    subdomain_number VARCHAR(10) NOT NULL,
    subdomain_name VARCHAR(100) NOT NULL,
    description TEXT,
    next_entity_sequence INTEGER NOT NULL DEFAULT 1,
    UNIQUE(fk_domain, subdomain_number)
);

-- Entity registration table
CREATE TABLE specql_registry.tb_entity_registration (
    pk_entity_registration SERIAL PRIMARY KEY,
    fk_subdomain INTEGER NOT NULL REFERENCES specql_registry.tb_subdomain(pk_subdomain) ON DELETE CASCADE,
    entity_name VARCHAR(100) NOT NULL,
    table_code VARCHAR(20) NOT NULL,
    entity_sequence INTEGER NOT NULL,
    UNIQUE(fk_subdomain, entity_name)
);

-- Indexes for performance
CREATE INDEX idx_tb_domain_domain_number ON specql_registry.tb_domain(domain_number);
CREATE INDEX idx_tb_domain_domain_name ON specql_registry.tb_domain(domain_name);
CREATE INDEX idx_tb_subdomain_fk_domain ON specql_registry.tb_subdomain(fk_domain);
CREATE INDEX idx_tb_entity_registration_fk_subdomain ON specql_registry.tb_entity_registration(fk_subdomain);

-- Comments
COMMENT ON SCHEMA specql_registry IS 'Domain registry for SPECQL entity management';
COMMENT ON TABLE specql_registry.tb_domain IS 'Domain definitions (core, crm, catalog, etc.)';
COMMENT ON TABLE specql_registry.tb_subdomain IS 'Subdomain definitions within domains';
COMMENT ON TABLE specql_registry.tb_entity_registration IS 'Entity registrations with table codes';