-- Create app schema
CREATE SCHEMA IF NOT EXISTS app;

-- ============================================================================
-- MUTATION RESULT TYPE
-- Standard output type for all mutations
-- ============================================================================
CREATE TYPE app.mutation_result AS (
    id UUID,
    updated_fields TEXT[],
    status TEXT,
    message TEXT,
    object_data JSONB,
    extra_metadata JSONB
);

COMMENT ON TYPE app.mutation_result IS
'Standard mutation result for all operations.
Returns entity data, status, and optional metadata.

@fraiseql:composite
name: MutationResult
tier: 1
storage: composite';

COMMENT ON COLUMN app.mutation_result.id IS
'Unique identifier of the affected entity.

@fraiseql:field
name: id
type: UUID!
required: true';

COMMENT ON COLUMN app.mutation_result.updated_fields IS
'Fields that were modified in this mutation.

@fraiseql:field
name: updatedFields
type: [String]
required: false';

COMMENT ON COLUMN app.mutation_result.status IS
'Operation status indicator.
Values: success, failed:error_code

@fraiseql:field
name: status
type: String!
required: true';

COMMENT ON COLUMN app.mutation_result.message IS
'Human-readable success or error message.

@fraiseql:field
name: message
type: String
required: false';

COMMENT ON COLUMN app.mutation_result.object_data IS
'Complete entity data after mutation.

@fraiseql:field
name: object
type: JSON
required: false';

COMMENT ON COLUMN app.mutation_result.extra_metadata IS
'Additional metadata including side effects and impact information.

@fraiseql:field
name: extra
type: JSON
required: false';

-- ============================================================================
-- AUDIT LOG TABLE: app.tb_mutation_audit_log
-- Comprehensive audit trail for all mutations across the application
-- ============================================================================
CREATE TABLE app.tb_mutation_audit_log (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Multi-tenancy
    tenant_id UUID NOT NULL,

    -- User context
    user_id UUID,

    -- Entity context
    entity_type TEXT NOT NULL,
    entity_id UUID NOT NULL,

    -- Operation details
    operation TEXT NOT NULL,  -- 'INSERT', 'UPDATE', 'DELETE', 'NOOP'
    status TEXT NOT NULL,     -- 'success', 'failed:*'

    -- Data changes
    updated_fields TEXT[],
    message TEXT,
    object_data JSONB,

    -- Additional context
    extra_metadata JSONB,
    error_context JSONB,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes for performance
CREATE INDEX idx_mutation_audit_tenant ON app.tb_mutation_audit_log(tenant_id);
CREATE INDEX idx_mutation_audit_entity ON app.tb_mutation_audit_log(entity_type, entity_id);
CREATE INDEX idx_mutation_audit_created ON app.tb_mutation_audit_log(created_at);

-- Comments
COMMENT ON TABLE app.tb_mutation_audit_log IS 'Comprehensive audit trail for all mutations across the application';
COMMENT ON COLUMN app.tb_mutation_audit_log.id IS 'Unique identifier for this audit log entry';
COMMENT ON COLUMN app.tb_mutation_audit_log.tenant_id IS 'Tenant that performed the operation';
COMMENT ON COLUMN app.tb_mutation_audit_log.user_id IS 'User who performed the operation';
COMMENT ON COLUMN app.tb_mutation_audit_log.entity_type IS 'Type of entity being mutated (e.g., contact, company)';
COMMENT ON COLUMN app.tb_mutation_audit_log.entity_id IS 'ID of the entity being mutated';
COMMENT ON COLUMN app.tb_mutation_audit_log.operation IS 'Type of operation: INSERT, UPDATE, DELETE, NOOP';
COMMENT ON COLUMN app.tb_mutation_audit_log.status IS 'Operation status: success or failed:*';
COMMENT ON COLUMN app.tb_mutation_audit_log.updated_fields IS 'Array of field names that were modified';
COMMENT ON COLUMN app.tb_mutation_audit_log.message IS 'Human-readable success or error message';
COMMENT ON COLUMN app.tb_mutation_audit_log.object_data IS 'Complete entity data after the mutation';
COMMENT ON COLUMN app.tb_mutation_audit_log.extra_metadata IS 'Additional metadata including side effects';
COMMENT ON COLUMN app.tb_mutation_audit_log.error_context IS 'Error context information for debugging';
COMMENT ON COLUMN app.tb_mutation_audit_log.created_at IS 'Timestamp when the audit log entry was created';

-- ============================================================================
-- SHARED UTILITY: app.log_and_return_mutation
-- Used by ALL business schemas for standardized mutation responses with audit logging
-- ============================================================================
CREATE OR REPLACE FUNCTION app.log_and_return_mutation(
    p_tenant_id UUID,
    p_user_id UUID,
    p_entity TEXT,
    p_entity_id UUID,
    p_operation TEXT,          -- 'INSERT', 'UPDATE', 'DELETE', 'NOOP'
    p_status TEXT,             -- 'success', 'failed:*'
    p_updated_fields TEXT[],
    p_message TEXT,
    p_object_data JSONB,
    p_extra_metadata JSONB DEFAULT NULL,
    p_error_context JSONB DEFAULT NULL
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_audit_id UUID := gen_random_uuid();
BEGIN
    -- Insert audit log record
    INSERT INTO app.tb_mutation_audit_log (
        id,
        tenant_id,
        user_id,
        entity_type,
        entity_id,
        operation,
        status,
        updated_fields,
        message,
        object_data,
        extra_metadata,
        error_context,
        created_at
    ) VALUES (
        v_audit_id,
        p_tenant_id,
        p_user_id,
        p_entity,
        p_entity_id,
        p_operation,
        p_status,
        p_updated_fields,
        p_message,
        p_object_data,
        p_extra_metadata,
        p_error_context,
        now()
    );

    -- Return standardized mutation result
    RETURN ROW(
        p_entity_id,
        p_updated_fields,
        p_status,
        p_message,
        p_object_data,
        p_extra_metadata
    )::app.mutation_result;
END;
$$;

COMMENT ON FUNCTION app.log_and_return_mutation IS
  'Audit logger and standardized mutation result builder for all app/core functions';


-- ============================================================================
-- CASCADE HELPER FUNCTIONS
-- Generate GraphQL cascade data for FraiseQL automatic cache updates
-- ============================================================================

-- Helper: Build cascade entity with full data from table view
-- Used for CREATED and UPDATED operations that include entity data
CREATE OR REPLACE FUNCTION app.cascade_entity(
    p_typename TEXT,      -- GraphQL type name (e.g., 'Post', 'User')
    p_id UUID,            -- Entity UUID
    p_operation TEXT,     -- Operation: 'CREATED', 'UPDATED'
    p_schema TEXT,        -- Database schema name
    p_view_name TEXT      -- Table view name (e.g., 'tv_post')
) RETURNS JSONB AS $$
DECLARE
    v_entity_data JSONB;
    v_table_name TEXT;
BEGIN
    -- Try to fetch from table view first (preferred for performance)
    BEGIN
        EXECUTE format('SELECT data FROM %I.%I WHERE id = $1', p_schema, p_view_name)
        INTO v_entity_data
        USING p_id;
    EXCEPTION WHEN undefined_table OR undefined_column THEN
        -- Fallback: try table directly using typename
        -- Construct table name from typename (User -> tb_user)
        v_table_name := 'tb_' || lower(p_typename);

        BEGIN
            EXECUTE format(
                'SELECT row_to_json(t.*)::jsonb FROM %I.%I t WHERE id = $1',
                p_schema,
                v_table_name
            )
            INTO v_entity_data
            USING p_id;
        EXCEPTION WHEN OTHERS THEN
            -- Entity not found or other error
            v_entity_data := NULL;
        END;
    END;

    -- Build GraphQL cascade entity structure
    RETURN jsonb_build_object(
        '__typename', p_typename,
        'id', p_id,
        'operation', p_operation,
        'entity', COALESCE(v_entity_data, '{}'::jsonb)
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION app.cascade_entity IS
  'Builds GraphQL cascade entity with full data for CREATED/UPDATED operations';

-- Helper: Build deleted entity (no data, just ID)
-- Used for DELETED operations that only need ID reference
CREATE OR REPLACE FUNCTION app.cascade_deleted(
    p_typename TEXT,      -- GraphQL type name (e.g., 'Post', 'User')
    p_id UUID             -- Entity UUID
) RETURNS JSONB AS $$
BEGIN
    -- Build GraphQL cascade entity structure for deletions
    RETURN jsonb_build_object(
        '__typename', p_typename,
        'id', p_id,
        'operation', 'DELETED'
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION app.cascade_deleted IS
  'Builds GraphQL cascade entity for DELETED operations (ID only)';
-- Table View: specql_registry.tv_subdomain
-- Table view for Subdomain (read-optimized, denormalized)
CREATE TABLE specql_registry.tv_subdomain (
    pk_subdomain INTEGER PRIMARY KEY,
    id UUID NOT NULL UNIQUE,
    tenant_id UUID NOT NULL,
    fk_parent_domain INTEGER,
    parent_domain_id UUID,
    data JSONB NOT NULL,
    refreshed_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tv_subdomain_tenant ON specql_registry.tv_subdomain(tenant_id);
CREATE INDEX idx_tv_subdomain_parent_domain_id ON specql_registry.tv_subdomain(parent_domain_id);
CREATE INDEX idx_tv_subdomain_data ON specql_registry.tv_subdomain USING GIN(data);

-- Refresh function for tv_subdomain
-- Composes JSONB from related tv_ tables (not tb_ tables!)
CREATE OR REPLACE FUNCTION specql_registry.refresh_tv_subdomain(
    p_pk_subdomain INTEGER DEFAULT NULL
) RETURNS void AS $$
BEGIN
    -- Delete existing rows
    DELETE FROM specql_registry.tv_subdomain
    WHERE p_pk_subdomain IS NULL OR pk_subdomain = p_pk_subdomain;

    -- Insert refreshed data
    INSERT INTO specql_registry.tv_subdomain (
        pk_subdomain, id, tenant_id, fk_parent_domain, parent_domain_id, data
    )
    SELECT
        base.pk_subdomain,
        base.id,
        base.tenant_id,
        base.fk_parent_domain,
        tv_domain.id AS parent_domain_id,
        jsonb_build_object('parent_domain', tv_domain.data, 'subdomain_number', base.subdomain_number, 'subdomain_name', base.subdomain_name, 'description', base.description) AS data
    FROM specql_registry.tb_subdomain base
    LEFT JOIN public.tv_domain tv_domain ON tv_domain.pk_domain = base.fk_parent_domain
    WHERE base.deleted_at IS NULL
      AND (p_pk_subdomain IS NULL OR base.pk_subdomain = p_pk_subdomain);
END;
$$ LANGUAGE plpgsql;-- Table View: specql_registry.tv_subdomain
-- Table view for Subdomain (read-optimized, denormalized)
CREATE TABLE specql_registry.tv_subdomain (
    pk_subdomain INTEGER PRIMARY KEY,
    id UUID NOT NULL UNIQUE,
    tenant_id UUID NOT NULL,
    fk_parent_domain INTEGER,
    parent_domain_id UUID,
    data JSONB NOT NULL,
    refreshed_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tv_subdomain_tenant ON specql_registry.tv_subdomain(tenant_id);
CREATE INDEX idx_tv_subdomain_parent_domain_id ON specql_registry.tv_subdomain(parent_domain_id);
CREATE INDEX idx_tv_subdomain_data ON specql_registry.tv_subdomain USING GIN(data);

-- Refresh function for tv_subdomain
-- Composes JSONB from related tv_ tables (not tb_ tables!)
CREATE OR REPLACE FUNCTION specql_registry.refresh_tv_subdomain(
    p_pk_subdomain INTEGER DEFAULT NULL
) RETURNS void AS $$
BEGIN
    -- Delete existing rows
    DELETE FROM specql_registry.tv_subdomain
    WHERE p_pk_subdomain IS NULL OR pk_subdomain = p_pk_subdomain;

    -- Insert refreshed data
    INSERT INTO specql_registry.tv_subdomain (
        pk_subdomain, id, tenant_id, fk_parent_domain, parent_domain_id, data
    )
    SELECT
        base.pk_subdomain,
        base.id,
        base.tenant_id,
        base.fk_parent_domain,
        tv_domain.id AS parent_domain_id,
        jsonb_build_object('parent_domain', tv_domain.data, 'subdomain_number', base.subdomain_number, 'subdomain_name', base.subdomain_name, 'description', base.description) AS data
    FROM specql_registry.tb_subdomain base
    LEFT JOIN public.tv_domain tv_domain ON tv_domain.pk_domain = base.fk_parent_domain
    WHERE base.deleted_at IS NULL
      AND (p_pk_subdomain IS NULL OR base.pk_subdomain = p_pk_subdomain);
END;
$$ LANGUAGE plpgsql;-- Table View: specql_registry.tv_entityregistration
-- Table view for EntityRegistration (read-optimized, denormalized)
CREATE TABLE specql_registry.tv_entityregistration (
    pk_entityregistration INTEGER PRIMARY KEY,
    id UUID NOT NULL UNIQUE,
    tenant_id UUID NOT NULL,
    fk_parent_domain INTEGER,
    parent_domain_id UUID,
    fk_parent_subdomain INTEGER,
    parent_subdomain_id UUID,
    data JSONB NOT NULL,
    refreshed_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tv_entityregistration_tenant ON specql_registry.tv_entityregistration(tenant_id);
CREATE INDEX idx_tv_entityregistration_parent_domain_id ON specql_registry.tv_entityregistration(parent_domain_id);
CREATE INDEX idx_tv_entityregistration_parent_subdomain_id ON specql_registry.tv_entityregistration(parent_subdomain_id);
CREATE INDEX idx_tv_entityregistration_data ON specql_registry.tv_entityregistration USING GIN(data);

-- Refresh function for tv_entityregistration
-- Composes JSONB from related tv_ tables (not tb_ tables!)
CREATE OR REPLACE FUNCTION specql_registry.refresh_tv_entityregistration(
    p_pk_entityregistration INTEGER DEFAULT NULL
) RETURNS void AS $$
BEGIN
    -- Delete existing rows
    DELETE FROM specql_registry.tv_entityregistration
    WHERE p_pk_entityregistration IS NULL OR pk_entityregistration = p_pk_entityregistration;

    -- Insert refreshed data
    INSERT INTO specql_registry.tv_entityregistration (
        pk_entityregistration, id, tenant_id, fk_parent_domain, parent_domain_id, fk_parent_subdomain, parent_subdomain_id, data
    )
    SELECT
        base.pk_entityregistration,
        base.id,
        base.tenant_id,
        base.fk_parent_domain,
        tv_domain.id AS parent_domain_id,
        base.fk_parent_subdomain,
        tv_subdomain.id AS parent_subdomain_id,
        jsonb_build_object('parent_domain', tv_domain.data, 'parent_subdomain', tv_subdomain.data, 'domain_number', base.domain_number, 'subdomain_number', base.subdomain_number, 'entity_sequence', base.entity_sequence, 'entity_name', base.entity_name, 'table_code', base.table_code, 'schema_name', base.schema_name, 'table_name', base.table_name, 'entity_type', base.entity_type, 'registration_source', base.registration_source) AS data
    FROM specql_registry.tb_entityregistration base
    LEFT JOIN public.tv_domain tv_domain ON tv_domain.pk_domain = base.fk_parent_domain
    LEFT JOIN public.tv_subdomain tv_subdomain ON tv_subdomain.pk_subdomain = base.fk_parent_subdomain
    WHERE base.deleted_at IS NULL
      AND (p_pk_entityregistration IS NULL OR base.pk_entityregistration = p_pk_entityregistration);
END;
$$ LANGUAGE plpgsql;-- Table View: pattern_library.tv_domainpattern
-- Table view for DomainPattern (read-optimized, denormalized)
CREATE TABLE pattern_library.tv_domainpattern (
    pk_domainpattern INTEGER PRIMARY KEY,
    id UUID NOT NULL UNIQUE,
    tenant_id UUID NOT NULL,
    fk_parent_domain INTEGER,
    parent_domain_id UUID,
    data JSONB NOT NULL,
    refreshed_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tv_domainpattern_tenant ON pattern_library.tv_domainpattern(tenant_id);
CREATE INDEX idx_tv_domainpattern_parent_domain_id ON pattern_library.tv_domainpattern(parent_domain_id);
CREATE INDEX idx_tv_domainpattern_data ON pattern_library.tv_domainpattern USING GIN(data);

-- Refresh function for tv_domainpattern
-- Composes JSONB from related tv_ tables (not tb_ tables!)
CREATE OR REPLACE FUNCTION pattern_library.refresh_tv_domainpattern(
    p_pk_domainpattern INTEGER DEFAULT NULL
) RETURNS void AS $$
BEGIN
    -- Delete existing rows
    DELETE FROM pattern_library.tv_domainpattern
    WHERE p_pk_domainpattern IS NULL OR pk_domainpattern = p_pk_domainpattern;

    -- Insert refreshed data
    INSERT INTO pattern_library.tv_domainpattern (
        pk_domainpattern, id, tenant_id, fk_parent_domain, parent_domain_id, data
    )
    SELECT
        base.pk_domainpattern,
        base.id,
        base.tenant_id,
        base.fk_parent_domain,
        tv_domain.id AS parent_domain_id,
        jsonb_build_object('parent_domain', tv_domain.data, 'pattern_id', base.pattern_id, 'pattern_name', base.pattern_name, 'category', base.category, 'description', base.description, 'pattern_type', base.pattern_type, 'fields_json', base.fields_json, 'actions_json', base.actions_json, 'usage_count', base.usage_count, 'popularity_score', base.popularity_score, 'created_by_user', base.created_by_user, 'version', base.version, 'status', base.status) AS data
    FROM pattern_library.tb_domainpattern base
    LEFT JOIN public.tv_domain tv_domain ON tv_domain.pk_domain = base.fk_parent_domain
    WHERE base.deleted_at IS NULL
      AND (p_pk_domainpattern IS NULL OR base.pk_domainpattern = p_pk_domainpattern);
END;
$$ LANGUAGE plpgsql;-- Table View: pattern_library.tv_domainpattern
-- Table view for DomainPattern (read-optimized, denormalized)
CREATE TABLE pattern_library.tv_domainpattern (
    pk_domainpattern INTEGER PRIMARY KEY,
    id UUID NOT NULL UNIQUE,
    tenant_id UUID NOT NULL,
    fk_parent_domain INTEGER,
    parent_domain_id UUID,
    data JSONB NOT NULL,
    refreshed_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tv_domainpattern_tenant ON pattern_library.tv_domainpattern(tenant_id);
CREATE INDEX idx_tv_domainpattern_parent_domain_id ON pattern_library.tv_domainpattern(parent_domain_id);
CREATE INDEX idx_tv_domainpattern_data ON pattern_library.tv_domainpattern USING GIN(data);

-- Refresh function for tv_domainpattern
-- Composes JSONB from related tv_ tables (not tb_ tables!)
CREATE OR REPLACE FUNCTION pattern_library.refresh_tv_domainpattern(
    p_pk_domainpattern INTEGER DEFAULT NULL
) RETURNS void AS $$
BEGIN
    -- Delete existing rows
    DELETE FROM pattern_library.tv_domainpattern
    WHERE p_pk_domainpattern IS NULL OR pk_domainpattern = p_pk_domainpattern;

    -- Insert refreshed data
    INSERT INTO pattern_library.tv_domainpattern (
        pk_domainpattern, id, tenant_id, fk_parent_domain, parent_domain_id, data
    )
    SELECT
        base.pk_domainpattern,
        base.id,
        base.tenant_id,
        base.fk_parent_domain,
        tv_domain.id AS parent_domain_id,
        jsonb_build_object('parent_domain', tv_domain.data, 'pattern_id', base.pattern_id, 'pattern_name', base.pattern_name, 'category', base.category, 'description', base.description, 'pattern_type', base.pattern_type, 'fields_json', base.fields_json, 'actions_json', base.actions_json, 'usage_count', base.usage_count, 'popularity_score', base.popularity_score, 'created_by_user', base.created_by_user, 'version', base.version, 'status', base.status) AS data
    FROM pattern_library.tb_domainpattern base
    LEFT JOIN public.tv_domain tv_domain ON tv_domain.pk_domain = base.fk_parent_domain
    WHERE base.deleted_at IS NULL
      AND (p_pk_domainpattern IS NULL OR base.pk_domainpattern = p_pk_domainpattern);
END;
$$ LANGUAGE plpgsql;-- Table View: specql_registry.tv_entityregistration
-- Table view for EntityRegistration (read-optimized, denormalized)
CREATE TABLE specql_registry.tv_entityregistration (
    pk_entityregistration INTEGER PRIMARY KEY,
    id UUID NOT NULL UNIQUE,
    tenant_id UUID NOT NULL,
    fk_parent_domain INTEGER,
    parent_domain_id UUID,
    fk_parent_subdomain INTEGER,
    parent_subdomain_id UUID,
    data JSONB NOT NULL,
    refreshed_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_tv_entityregistration_tenant ON specql_registry.tv_entityregistration(tenant_id);
CREATE INDEX idx_tv_entityregistration_parent_domain_id ON specql_registry.tv_entityregistration(parent_domain_id);
CREATE INDEX idx_tv_entityregistration_parent_subdomain_id ON specql_registry.tv_entityregistration(parent_subdomain_id);
CREATE INDEX idx_tv_entityregistration_data ON specql_registry.tv_entityregistration USING GIN(data);

-- Refresh function for tv_entityregistration
-- Composes JSONB from related tv_ tables (not tb_ tables!)
CREATE OR REPLACE FUNCTION specql_registry.refresh_tv_entityregistration(
    p_pk_entityregistration INTEGER DEFAULT NULL
) RETURNS void AS $$
BEGIN
    -- Delete existing rows
    DELETE FROM specql_registry.tv_entityregistration
    WHERE p_pk_entityregistration IS NULL OR pk_entityregistration = p_pk_entityregistration;

    -- Insert refreshed data
    INSERT INTO specql_registry.tv_entityregistration (
        pk_entityregistration, id, tenant_id, fk_parent_domain, parent_domain_id, fk_parent_subdomain, parent_subdomain_id, data
    )
    SELECT
        base.pk_entityregistration,
        base.id,
        base.tenant_id,
        base.fk_parent_domain,
        tv_domain.id AS parent_domain_id,
        base.fk_parent_subdomain,
        tv_subdomain.id AS parent_subdomain_id,
        jsonb_build_object('parent_domain', tv_domain.data, 'parent_subdomain', tv_subdomain.data, 'domain_number', base.domain_number, 'subdomain_number', base.subdomain_number, 'entity_sequence', base.entity_sequence, 'entity_name', base.entity_name, 'table_code', base.table_code, 'schema_name', base.schema_name, 'table_name', base.table_name, 'entity_type', base.entity_type, 'registration_source', base.registration_source) AS data
    FROM specql_registry.tb_entityregistration base
    LEFT JOIN public.tv_domain tv_domain ON tv_domain.pk_domain = base.fk_parent_domain
    LEFT JOIN public.tv_subdomain tv_subdomain ON tv_subdomain.pk_subdomain = base.fk_parent_subdomain
    WHERE base.deleted_at IS NULL
      AND (p_pk_entityregistration IS NULL OR base.pk_entityregistration = p_pk_entityregistration);
END;
$$ LANGUAGE plpgsql;