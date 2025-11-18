-- App Schema Foundation
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

-- Create schema
CREATE SCHEMA IF NOT EXISTS tenant;

-- Entity Table
-- ============================================================================
-- Table: tenant.tb_contact
-- ============================================================================
-- [Table: CON | Individual contact information linked to an organization.
Includes roles, communication details, and authentication.
]
-- ============================================================================

CREATE TABLE tenant.tb_contact (
    -- ========================================================================
    -- Trinity Pattern: INTEGER primary key for performance
    -- ========================================================================
    pk_contact INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,

    -- ========================================================================
    -- Trinity Pattern: UUID for stable public API
    -- ========================================================================
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    -- ========================================================================
    -- Multi-Tenancy: Denormalized from JWT (CRITICAL for security)
    -- ========================================================================
    tenant_id UUID NOT NULL,

    -- ========================================================================
    -- Multi-Tenancy: Optional business FK to organization
    -- ========================================================================
    -- Note: Only add fk_organization if entity belongs to specific org unit
    -- (not just tenant isolation). Comment out if not needed.
    -- fk_organization INTEGER,
    -- ========================================================================
    -- Business Fields
    -- ========================================================================
    first_name TEXT,
    last_name TEXT,
    email_address TEXT NOT NULL,
    office_phone TEXT,
    mobile_phone TEXT,
    job_title TEXT,
    position TEXT,
    lang TEXT,
    locale TEXT,
    timezone TEXT,
    handles JSONB,
    password_hash TEXT,
    -- ========================================================================
    -- Foreign Keys (Trinity Pattern: INTEGER references)
    -- ========================================================================

    fk_customer_org INTEGER,

    fk_genre INTEGER,

    -- ========================================================================
    -- Audit Fields (Trinity Pattern standard)
    -- ========================================================================
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by UUID,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID,

    -- ========================================================================
    -- Constraints
    -- ========================================================================
    CONSTRAINT tb_contact_id_key UNIQUE (id)
    ,CONSTRAINT chk_tb_contact_email_address_pattern CHECK (email_address ~* '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    ,CONSTRAINT chk_tb_contact_office_phone_pattern CHECK (office_phone ~* '^\+[1-9]\d{1,14}$')
    ,CONSTRAINT chk_tb_contact_mobile_phone_pattern CHECK (mobile_phone ~* '^\+[1-9]\d{1,14}$'));

-- ============================================================================
-- Foreign Key Constraints (defined after table creation)
-- ============================================================================
ALTER TABLE ONLY tenant.tb_contact
    ADD CONSTRAINT tb_contact_fk_customer_org_fkey
    FOREIGN KEY (fk_customer_org) REFERENCES tenant.tb_organization(pk_organization);
ALTER TABLE ONLY tenant.tb_contact
    ADD CONSTRAINT tb_contact_fk_genre_fkey
    FOREIGN KEY (fk_genre) REFERENCES tenant.tb_genre(pk_genre);-- ============================================================================
-- Multi-Tenancy Indexes (CRITICAL for performance & RLS)
-- ============================================================================
CREATE INDEX idx_tb_contact_tenant ON tenant.tb_contact(tenant_id);
-- ============================================================================
-- Documentation
-- ============================================================================
COMMENT ON TABLE tenant.tb_contact IS
'Individual contact information linked to an organization.
Includes roles, communication details, and authentication.
.

@fraiseql:type
trinity: true
';

-- Trinity Pattern columns
COMMENT ON COLUMN tenant.tb_contact.pk_contact IS 'Internal INTEGER primary key used in joins and foreign keys.';
COMMENT ON COLUMN tenant.tb_contact.id IS
'Public UUID identifier for external APIs and GraphQL.

@fraiseql:field
name: id
type: UUID!
required: true';
-- Multi-Tenancy columns
COMMENT ON COLUMN tenant.tb_contact.tenant_id IS 'Denormalized tenant identifier from JWT token (security context).';
-- COMMENT ON COLUMN tenant.tb_contact.fk_organization IS 'Optional business FK to organization unit (uncomment if needed).';
-- Business field columns (comments handled by CommentGenerator)

-- Foreign key columns (comments handled by CommentGenerator)

-- Audit field columns
COMMENT ON COLUMN tenant.tb_contact.created_at IS 'Timestamp when the record was created.';
COMMENT ON COLUMN tenant.tb_contact.created_by IS 'User or system who created the record.';
COMMENT ON COLUMN tenant.tb_contact.updated_at IS 'Timestamp when the record was last updated.';
COMMENT ON COLUMN tenant.tb_contact.updated_by IS 'User or system who last updated the record.';
COMMENT ON COLUMN tenant.tb_contact.deleted_at IS 'Timestamp of soft deletion.';
COMMENT ON COLUMN tenant.tb_contact.deleted_by IS 'User or system who deleted the record.';

-- Input Type: create_contact

-- ============================================================================
-- INPUT TYPE: type_create_contact_input
-- For action: create_contact
-- ============================================================================
CREATE TYPE app.type_create_contact_input AS (

    first_name TEXT,

    last_name TEXT,

    email_address TEXT,

    office_phone TEXT,

    mobile_phone TEXT,

    job_title TEXT,

    position TEXT,

    lang TEXT,

    locale TEXT,

    timezone TEXT,

    handles JSONB,

    password_hash TEXT,

    customer_org_id UUID,

    genre_id UUID

);

-- FraiseQL metadata
COMMENT ON TYPE app.type_create_contact_input IS
'Input parameters for Create Contact.

@fraiseql:composite
name: CreateContactInput
tier: 2';


-- Field metadata

COMMENT ON COLUMN app.type_create_contact_input.first_name IS
'First_Name (optional).

@fraiseql:field
name: first_name
type: String
required: false';

COMMENT ON COLUMN app.type_create_contact_input.last_name IS
'Last_Name (optional).

@fraiseql:field
name: last_name
type: String
required: false';

COMMENT ON COLUMN app.type_create_contact_input.email_address IS
'Email address (required).

@fraiseql:field
name: email_address
type: String!
required: true';

COMMENT ON COLUMN app.type_create_contact_input.office_phone IS
'Office_Phone (optional).

@fraiseql:field
name: office_phone
type: String
required: false';

COMMENT ON COLUMN app.type_create_contact_input.mobile_phone IS
'Mobile_Phone (optional).

@fraiseql:field
name: mobile_phone
type: String
required: false';

COMMENT ON COLUMN app.type_create_contact_input.job_title IS
'Job_Title (optional).

@fraiseql:field
name: job_title
type: String
required: false';

COMMENT ON COLUMN app.type_create_contact_input.position IS
'Position (optional).

@fraiseql:field
name: position
type: String
required: false';

COMMENT ON COLUMN app.type_create_contact_input.lang IS
'Lang (optional).

@fraiseql:field
name: lang
type: String
required: false';

COMMENT ON COLUMN app.type_create_contact_input.locale IS
'Locale (optional).

@fraiseql:field
name: locale
type: String
required: false';

COMMENT ON COLUMN app.type_create_contact_input.timezone IS
'Timezone (optional).

@fraiseql:field
name: timezone
type: String
required: false';

COMMENT ON COLUMN app.type_create_contact_input.handles IS
'Handles (optional).

@fraiseql:field
name: handles
type: JSON
required: false';

COMMENT ON COLUMN app.type_create_contact_input.password_hash IS
'Password_Hash (optional).

@fraiseql:field
name: password_hash
type: String
required: false';

COMMENT ON COLUMN app.type_create_contact_input.customer_org_id IS
'Customer_Org reference (optional).

@fraiseql:field
name: customer_org_id
type: UUID
required: false
references: Organization';

COMMENT ON COLUMN app.type_create_contact_input.genre_id IS
'Genre reference (optional).

@fraiseql:field
name: genre_id
type: UUID
required: false
references: Genre';



-- Input Type: update_contact

-- ============================================================================
-- INPUT TYPE: type_update_contact_input
-- For action: update_contact
-- ============================================================================
CREATE TYPE app.type_update_contact_input AS (

    first_name TEXT,

    last_name TEXT,

    email_address TEXT,

    office_phone TEXT,

    mobile_phone TEXT,

    job_title TEXT,

    position TEXT,

    lang TEXT,

    locale TEXT,

    timezone TEXT,

    handles JSONB,

    password_hash TEXT,

    customer_org_id UUID,

    genre_id UUID,

    id UUID

);

-- FraiseQL metadata
COMMENT ON TYPE app.type_update_contact_input IS
'Input parameters for Update Contact.

@fraiseql:composite
name: UpdateContactInput
tier: 2';


-- Field metadata

COMMENT ON COLUMN app.type_update_contact_input.first_name IS
'First_Name (optional).

@fraiseql:field
name: first_name
type: String
required: false';

COMMENT ON COLUMN app.type_update_contact_input.last_name IS
'Last_Name (optional).

@fraiseql:field
name: last_name
type: String
required: false';

COMMENT ON COLUMN app.type_update_contact_input.email_address IS
'Email address (required).

@fraiseql:field
name: email_address
type: String!
required: true';

COMMENT ON COLUMN app.type_update_contact_input.office_phone IS
'Office_Phone (optional).

@fraiseql:field
name: office_phone
type: String
required: false';

COMMENT ON COLUMN app.type_update_contact_input.mobile_phone IS
'Mobile_Phone (optional).

@fraiseql:field
name: mobile_phone
type: String
required: false';

COMMENT ON COLUMN app.type_update_contact_input.job_title IS
'Job_Title (optional).

@fraiseql:field
name: job_title
type: String
required: false';

COMMENT ON COLUMN app.type_update_contact_input.position IS
'Position (optional).

@fraiseql:field
name: position
type: String
required: false';

COMMENT ON COLUMN app.type_update_contact_input.lang IS
'Lang (optional).

@fraiseql:field
name: lang
type: String
required: false';

COMMENT ON COLUMN app.type_update_contact_input.locale IS
'Locale (optional).

@fraiseql:field
name: locale
type: String
required: false';

COMMENT ON COLUMN app.type_update_contact_input.timezone IS
'Timezone (optional).

@fraiseql:field
name: timezone
type: String
required: false';

COMMENT ON COLUMN app.type_update_contact_input.handles IS
'Handles (optional).

@fraiseql:field
name: handles
type: JSON
required: false';

COMMENT ON COLUMN app.type_update_contact_input.password_hash IS
'Password_Hash (optional).

@fraiseql:field
name: password_hash
type: String
required: false';

COMMENT ON COLUMN app.type_update_contact_input.customer_org_id IS
'Customer_Org reference (optional).

@fraiseql:field
name: customer_org_id
type: UUID
required: false
references: Organization';

COMMENT ON COLUMN app.type_update_contact_input.genre_id IS
'Genre reference (optional).

@fraiseql:field
name: genre_id
type: UUID
required: false
references: Genre';

COMMENT ON COLUMN app.type_update_contact_input.id IS
'Id (required).

@fraiseql:field
name: id
type: UUID!
required: true';



-- Input Type: delete_contact

-- ============================================================================
-- INPUT TYPE: type_delete_contact_input
-- For action: delete_contact
-- ============================================================================
CREATE TYPE app.type_delete_contact_input AS (

    id UUID

);

-- FraiseQL metadata
COMMENT ON TYPE app.type_delete_contact_input IS
'Input parameters for Delete Contact.

@fraiseql:composite
name: DeleteContactInput
tier: 2';


-- Field metadata

COMMENT ON COLUMN app.type_delete_contact_input.id IS
'Id (required).

@fraiseql:field
name: id
type: UUID!
required: true';



-- Input Type: activate_contact

-- ============================================================================
-- INPUT TYPE: type_activate_contact_input
-- For action: activate_contact
-- ============================================================================
CREATE TYPE app.type_activate_contact_input AS (

    id UUID

);

-- FraiseQL metadata
COMMENT ON TYPE app.type_activate_contact_input IS
'Input parameters for Activate Contact.

@fraiseql:composite
name: ActivateContactInput
tier: 2';


-- Field metadata

COMMENT ON COLUMN app.type_activate_contact_input.id IS
'Id (required).

@fraiseql:field
name: id
type: UUID!
required: true';



-- Input Type: deactivate_contact

-- ============================================================================
-- INPUT TYPE: type_deactivate_contact_input
-- For action: deactivate_contact
-- ============================================================================
CREATE TYPE app.type_deactivate_contact_input AS (

    id UUID

);

-- FraiseQL metadata
COMMENT ON TYPE app.type_deactivate_contact_input IS
'Input parameters for Deactivate Contact.

@fraiseql:composite
name: DeactivateContactInput
tier: 2';


-- Field metadata

COMMENT ON COLUMN app.type_deactivate_contact_input.id IS
'Id (required).

@fraiseql:field
name: id
type: UUID!
required: true';



-- Input Type: change_email_address

-- ============================================================================
-- INPUT TYPE: type_change_email_address_input
-- For action: change_email_address
-- ============================================================================
CREATE TYPE app.type_change_email_address_input AS (

    id UUID

);

-- FraiseQL metadata
COMMENT ON TYPE app.type_change_email_address_input IS
'Input parameters for Change Email Address.

@fraiseql:composite
name: ChangeEmailAddressInput
tier: 2';


-- Field metadata

COMMENT ON COLUMN app.type_change_email_address_input.id IS
'Id (required).

@fraiseql:field
name: id
type: UUID!
required: true';



-- Input Type: change_office_phone

-- ============================================================================
-- INPUT TYPE: type_change_office_phone_input
-- For action: change_office_phone
-- ============================================================================
CREATE TYPE app.type_change_office_phone_input AS (

    id UUID

);

-- FraiseQL metadata
COMMENT ON TYPE app.type_change_office_phone_input IS
'Input parameters for Change Office Phone.

@fraiseql:composite
name: ChangeOfficePhoneInput
tier: 2';


-- Field metadata

COMMENT ON COLUMN app.type_change_office_phone_input.id IS
'Id (required).

@fraiseql:field
name: id
type: UUID!
required: true';



-- Input Type: change_mobile_phone

-- ============================================================================
-- INPUT TYPE: type_change_mobile_phone_input
-- For action: change_mobile_phone
-- ============================================================================
CREATE TYPE app.type_change_mobile_phone_input AS (

    id UUID

);

-- FraiseQL metadata
COMMENT ON TYPE app.type_change_mobile_phone_input IS
'Input parameters for Change Mobile Phone.

@fraiseql:composite
name: ChangeMobilePhoneInput
tier: 2';


-- Field metadata

COMMENT ON COLUMN app.type_change_mobile_phone_input.id IS
'Id (required).

@fraiseql:field
name: id
type: UUID!
required: true';



-- Input Type: update_job_title

-- ============================================================================
-- INPUT TYPE: type_update_job_title_input
-- For action: update_job_title
-- ============================================================================
CREATE TYPE app.type_update_job_title_input AS (

    first_name TEXT,

    last_name TEXT,

    email_address TEXT,

    office_phone TEXT,

    mobile_phone TEXT,

    job_title TEXT,

    position TEXT,

    lang TEXT,

    locale TEXT,

    timezone TEXT,

    handles JSONB,

    password_hash TEXT,

    customer_org_id UUID,

    genre_id UUID,

    id UUID

);

-- FraiseQL metadata
COMMENT ON TYPE app.type_update_job_title_input IS
'Input parameters for Update Job Title.

@fraiseql:composite
name: UpdateJobTitleInput
tier: 2';


-- Field metadata

COMMENT ON COLUMN app.type_update_job_title_input.first_name IS
'First_Name (optional).

@fraiseql:field
name: first_name
type: String
required: false';

COMMENT ON COLUMN app.type_update_job_title_input.last_name IS
'Last_Name (optional).

@fraiseql:field
name: last_name
type: String
required: false';

COMMENT ON COLUMN app.type_update_job_title_input.email_address IS
'Email address (required).

@fraiseql:field
name: email_address
type: String!
required: true';

COMMENT ON COLUMN app.type_update_job_title_input.office_phone IS
'Office_Phone (optional).

@fraiseql:field
name: office_phone
type: String
required: false';

COMMENT ON COLUMN app.type_update_job_title_input.mobile_phone IS
'Mobile_Phone (optional).

@fraiseql:field
name: mobile_phone
type: String
required: false';

COMMENT ON COLUMN app.type_update_job_title_input.job_title IS
'Job_Title (optional).

@fraiseql:field
name: job_title
type: String
required: false';

COMMENT ON COLUMN app.type_update_job_title_input.position IS
'Position (optional).

@fraiseql:field
name: position
type: String
required: false';

COMMENT ON COLUMN app.type_update_job_title_input.lang IS
'Lang (optional).

@fraiseql:field
name: lang
type: String
required: false';

COMMENT ON COLUMN app.type_update_job_title_input.locale IS
'Locale (optional).

@fraiseql:field
name: locale
type: String
required: false';

COMMENT ON COLUMN app.type_update_job_title_input.timezone IS
'Timezone (optional).

@fraiseql:field
name: timezone
type: String
required: false';

COMMENT ON COLUMN app.type_update_job_title_input.handles IS
'Handles (optional).

@fraiseql:field
name: handles
type: JSON
required: false';

COMMENT ON COLUMN app.type_update_job_title_input.password_hash IS
'Password_Hash (optional).

@fraiseql:field
name: password_hash
type: String
required: false';

COMMENT ON COLUMN app.type_update_job_title_input.customer_org_id IS
'Customer_Org reference (optional).

@fraiseql:field
name: customer_org_id
type: UUID
required: false
references: Organization';

COMMENT ON COLUMN app.type_update_job_title_input.genre_id IS
'Genre reference (optional).

@fraiseql:field
name: genre_id
type: UUID
required: false
references: Genre';

COMMENT ON COLUMN app.type_update_job_title_input.id IS
'Id (required).

@fraiseql:field
name: id
type: UUID!
required: true';



-- Input Type: update_position

-- ============================================================================
-- INPUT TYPE: type_update_position_input
-- For action: update_position
-- ============================================================================
CREATE TYPE app.type_update_position_input AS (

    first_name TEXT,

    last_name TEXT,

    email_address TEXT,

    office_phone TEXT,

    mobile_phone TEXT,

    job_title TEXT,

    position TEXT,

    lang TEXT,

    locale TEXT,

    timezone TEXT,

    handles JSONB,

    password_hash TEXT,

    customer_org_id UUID,

    genre_id UUID,

    id UUID

);

-- FraiseQL metadata
COMMENT ON TYPE app.type_update_position_input IS
'Input parameters for Update Position.

@fraiseql:composite
name: UpdatePositionInput
tier: 2';


-- Field metadata

COMMENT ON COLUMN app.type_update_position_input.first_name IS
'First_Name (optional).

@fraiseql:field
name: first_name
type: String
required: false';

COMMENT ON COLUMN app.type_update_position_input.last_name IS
'Last_Name (optional).

@fraiseql:field
name: last_name
type: String
required: false';

COMMENT ON COLUMN app.type_update_position_input.email_address IS
'Email address (required).

@fraiseql:field
name: email_address
type: String!
required: true';

COMMENT ON COLUMN app.type_update_position_input.office_phone IS
'Office_Phone (optional).

@fraiseql:field
name: office_phone
type: String
required: false';

COMMENT ON COLUMN app.type_update_position_input.mobile_phone IS
'Mobile_Phone (optional).

@fraiseql:field
name: mobile_phone
type: String
required: false';

COMMENT ON COLUMN app.type_update_position_input.job_title IS
'Job_Title (optional).

@fraiseql:field
name: job_title
type: String
required: false';

COMMENT ON COLUMN app.type_update_position_input.position IS
'Position (optional).

@fraiseql:field
name: position
type: String
required: false';

COMMENT ON COLUMN app.type_update_position_input.lang IS
'Lang (optional).

@fraiseql:field
name: lang
type: String
required: false';

COMMENT ON COLUMN app.type_update_position_input.locale IS
'Locale (optional).

@fraiseql:field
name: locale
type: String
required: false';

COMMENT ON COLUMN app.type_update_position_input.timezone IS
'Timezone (optional).

@fraiseql:field
name: timezone
type: String
required: false';

COMMENT ON COLUMN app.type_update_position_input.handles IS
'Handles (optional).

@fraiseql:field
name: handles
type: JSON
required: false';

COMMENT ON COLUMN app.type_update_position_input.password_hash IS
'Password_Hash (optional).

@fraiseql:field
name: password_hash
type: String
required: false';

COMMENT ON COLUMN app.type_update_position_input.customer_org_id IS
'Customer_Org reference (optional).

@fraiseql:field
name: customer_org_id
type: UUID
required: false
references: Organization';

COMMENT ON COLUMN app.type_update_position_input.genre_id IS
'Genre reference (optional).

@fraiseql:field
name: genre_id
type: UUID
required: false
references: Genre';

COMMENT ON COLUMN app.type_update_position_input.id IS
'Id (required).

@fraiseql:field
name: id
type: UUID!
required: true';



-- Input Type: change_timezone

-- ============================================================================
-- INPUT TYPE: type_change_timezone_input
-- For action: change_timezone
-- ============================================================================
CREATE TYPE app.type_change_timezone_input AS (

    id UUID

);

-- FraiseQL metadata
COMMENT ON TYPE app.type_change_timezone_input IS
'Input parameters for Change Timezone.

@fraiseql:composite
name: ChangeTimezoneInput
tier: 2';


-- Field metadata

COMMENT ON COLUMN app.type_change_timezone_input.id IS
'Id (required).

@fraiseql:field
name: id
type: UUID!
required: true';



-- Input Type: update_password

-- ============================================================================
-- INPUT TYPE: type_update_password_input
-- For action: update_password
-- ============================================================================
CREATE TYPE app.type_update_password_input AS (

    first_name TEXT,

    last_name TEXT,

    email_address TEXT,

    office_phone TEXT,

    mobile_phone TEXT,

    job_title TEXT,

    position TEXT,

    lang TEXT,

    locale TEXT,

    timezone TEXT,

    handles JSONB,

    password_hash TEXT,

    customer_org_id UUID,

    genre_id UUID,

    id UUID

);

-- FraiseQL metadata
COMMENT ON TYPE app.type_update_password_input IS
'Input parameters for Update Password.

@fraiseql:composite
name: UpdatePasswordInput
tier: 2';


-- Field metadata

COMMENT ON COLUMN app.type_update_password_input.first_name IS
'First_Name (optional).

@fraiseql:field
name: first_name
type: String
required: false';

COMMENT ON COLUMN app.type_update_password_input.last_name IS
'Last_Name (optional).

@fraiseql:field
name: last_name
type: String
required: false';

COMMENT ON COLUMN app.type_update_password_input.email_address IS
'Email address (required).

@fraiseql:field
name: email_address
type: String!
required: true';

COMMENT ON COLUMN app.type_update_password_input.office_phone IS
'Office_Phone (optional).

@fraiseql:field
name: office_phone
type: String
required: false';

COMMENT ON COLUMN app.type_update_password_input.mobile_phone IS
'Mobile_Phone (optional).

@fraiseql:field
name: mobile_phone
type: String
required: false';

COMMENT ON COLUMN app.type_update_password_input.job_title IS
'Job_Title (optional).

@fraiseql:field
name: job_title
type: String
required: false';

COMMENT ON COLUMN app.type_update_password_input.position IS
'Position (optional).

@fraiseql:field
name: position
type: String
required: false';

COMMENT ON COLUMN app.type_update_password_input.lang IS
'Lang (optional).

@fraiseql:field
name: lang
type: String
required: false';

COMMENT ON COLUMN app.type_update_password_input.locale IS
'Locale (optional).

@fraiseql:field
name: locale
type: String
required: false';

COMMENT ON COLUMN app.type_update_password_input.timezone IS
'Timezone (optional).

@fraiseql:field
name: timezone
type: String
required: false';

COMMENT ON COLUMN app.type_update_password_input.handles IS
'Handles (optional).

@fraiseql:field
name: handles
type: JSON
required: false';

COMMENT ON COLUMN app.type_update_password_input.password_hash IS
'Password_Hash (optional).

@fraiseql:field
name: password_hash
type: String
required: false';

COMMENT ON COLUMN app.type_update_password_input.customer_org_id IS
'Customer_Org reference (optional).

@fraiseql:field
name: customer_org_id
type: UUID
required: false
references: Organization';

COMMENT ON COLUMN app.type_update_password_input.genre_id IS
'Genre reference (optional).

@fraiseql:field
name: genre_id
type: UUID
required: false
references: Genre';

COMMENT ON COLUMN app.type_update_password_input.id IS
'Id (required).

@fraiseql:field
name: id
type: UUID!
required: true';



-- Indexes
CREATE INDEX tenant_idx_tb_contact_id ON tenant.tb_contact USING btree (id);
CREATE INDEX tenant_idx_tb_contact_customer_org ON tenant.tb_contact USING btree (fk_customer_org);
CREATE INDEX tenant_idx_tb_contact_genre ON tenant.tb_contact USING btree (fk_genre);
CREATE INDEX tenant_idx_tb_contact_email_address ON tenant.tb_contact USING btree (email_address);
CREATE INDEX tenant_idx_tb_contact_office_phone ON tenant.tb_contact USING btree (office_phone);
CREATE INDEX tenant_idx_tb_contact_mobile_phone ON tenant.tb_contact USING btree (mobile_phone);
CREATE INDEX tenant_idx_tb_contact_handles ON tenant.tb_contact USING btree (handles);

-- Foreign Keys
ALTER TABLE ONLY tenant.tb_contact
    ADD CONSTRAINT tb_contact_customer_org_fkey
    FOREIGN KEY (fk_customer_org) REFERENCES tenant.tb_organization(pk_organization);

ALTER TABLE ONLY tenant.tb_contact
    ADD CONSTRAINT tb_contact_genre_fkey
    FOREIGN KEY (fk_genre) REFERENCES tenant.tb_genre(pk_genre);

-- Field Comments for FraiseQL
COMMENT ON COLUMN tenant.tb_contact.first_name IS
'Text string

@fraiseql:field
name: first_name
type: String
required: false';

COMMENT ON COLUMN tenant.tb_contact.last_name IS
'Text string

@fraiseql:field
name: last_name
type: String
required: false';

COMMENT ON COLUMN tenant.tb_contact.email_address IS
'Valid email address (RFC 5322 simplified)

@fraiseql:field
name: email_address
type: Email!
required: true';

COMMENT ON COLUMN tenant.tb_contact.office_phone IS
'International phone number (E.164 format)

@fraiseql:field
name: office_phone
type: PhoneNumber
required: false';

COMMENT ON COLUMN tenant.tb_contact.mobile_phone IS
'International phone number (E.164 format)

@fraiseql:field
name: mobile_phone
type: PhoneNumber
required: false';

COMMENT ON COLUMN tenant.tb_contact.job_title IS
'Text string

@fraiseql:field
name: job_title
type: String
required: false';

COMMENT ON COLUMN tenant.tb_contact.position IS
'Text string

@fraiseql:field
name: position
type: String
required: false';

COMMENT ON COLUMN tenant.tb_contact.lang IS
'Text string

@fraiseql:field
name: lang
type: String
required: false';

COMMENT ON COLUMN tenant.tb_contact.locale IS
'Text string

@fraiseql:field
name: locale
type: String
required: false';

COMMENT ON COLUMN tenant.tb_contact.timezone IS
'Text string

@fraiseql:field
name: timezone
type: String
required: false';

COMMENT ON COLUMN tenant.tb_contact.handles IS
'JSON object or array

@fraiseql:field
name: handles
type: JSON
required: false';

COMMENT ON COLUMN tenant.tb_contact.password_hash IS
'Text string

@fraiseql:field
name: password_hash
type: String
required: false';

COMMENT ON COLUMN tenant.tb_contact.fk_customer_org IS
'Ref value → Organization

@fraiseql:field
name: fk_customer_org
type: UUID
required: false
references: Organization';

COMMENT ON COLUMN tenant.tb_contact.fk_genre IS
'Ref value → Genre

@fraiseql:field
name: fk_genre
type: UUID
required: false
references: Genre';

-- Core Logic Functions
-- ============================================================================
-- CORE LOGIC: tenant.create_contact
-- Business Rules & Data Manipulation
-- ============================================================================
CREATE OR REPLACE FUNCTION tenant.create_contact(
    auth_tenant_id UUID,
    input_data app.type_create_contact_input,
    input_payload JSONB,
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_id UUID := gen_random_uuid();
    v_contact_pk INTEGER;
    v_fk_customer_org INTEGER;
    v_fk_genre INTEGER;
BEGIN
    -- === VALIDATION ===
    IF input_data.email_address IS NULL THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id,
            auth_user_id,
            'contact',
            '00000000-0000-0000-0000-000000000000'::UUID,
            'NOOP',
            'validation:required_field',
            ARRAY['email_address']::TEXT[],
            'Email_address is required',
            NULL, NULL,
            jsonb_build_object('reason', 'validation_email_address_null')
        );
    END IF;

    -- === UUID → INTEGER RESOLUTION (Trinity Helpers) ===
    IF input_data.customer_org_id IS NOT NULL THEN
        v_fk_customer_org := tenant.organization_pk(input_data.customer_org_id::TEXT, auth_tenant_id);

        IF v_fk_customer_org IS NULL THEN
            RETURN app.log_and_return_mutation(
                auth_tenant_id,
                auth_user_id,
                'contact',
                '00000000-0000-0000-0000-000000000000'::UUID,
                'NOOP',
                 'validation:reference_not_found',
                ARRAY['customer_org_id']::TEXT[],
                 'Referenced organization not found',
                NULL, NULL,
                jsonb_build_object('customer_org_id', input_data.customer_org_id)
            );
        END IF;
    END IF;
    IF input_data.genre_id IS NOT NULL THEN
        v_fk_genre := tenant.genre_pk(input_data.genre_id::TEXT, auth_tenant_id);

        IF v_fk_genre IS NULL THEN
            RETURN app.log_and_return_mutation(
                auth_tenant_id,
                auth_user_id,
                'contact',
                '00000000-0000-0000-0000-000000000000'::UUID,
                'NOOP',
                 'validation:reference_not_found',
                ARRAY['genre_id']::TEXT[],
                 'Referenced genre not found',
                NULL, NULL,
                jsonb_build_object('genre_id', input_data.genre_id)
            );
        END IF;
    END IF;

    -- === BUSINESS LOGIC: INSERT ===
    INSERT INTO tenant.tb_contact (
        id,
        tenant_id,
        first_name,
        last_name,
        email_address,
        office_phone,
        mobile_phone,
        job_title,
        position,
        lang,
        locale,
        timezone,
        handles,
        password_hash,
        fk_customer_org,
        fk_genre,
        created_at,
        created_by
    ) VALUES (
        v_contact_id,
        auth_tenant_id,
        input_data.first_name,
        input_data.last_name,
        input_data.email_address,
        input_data.office_phone,
        input_data.mobile_phone,
        input_data.job_title,
        input_data.position,
        input_data.lang,
        input_data.locale,
        input_data.timezone,
        input_data.handles,
        input_data.password_hash,
        v_fk_customer_org,
        v_fk_genre,
        now(),
        auth_user_id
    )
    RETURNING pk_contact INTO v_contact_pk;

    -- === AUDIT & RETURN ===
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'contact',
        v_contact_id,
        'INSERT',
        'success',
        ARRAY(SELECT jsonb_object_keys(input_payload)),
        'Contact created successfully',
        (SELECT row_to_json(t.*) FROM tenant.tb_contact t WHERE t.id = v_contact_id)::JSONB,
        NULL
    );
END;
$$;

-- ============================================================================
-- CORE LOGIC: tenant.update_contact
-- Business Rules & Data Manipulation
-- ============================================================================
CREATE OR REPLACE FUNCTION tenant.update_contact(
    auth_tenant_id UUID,
    input_data app.type_update_contact_input,
    input_payload JSONB,
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_id UUID;
    v_contact_pk INTEGER;
    v_fk_customer_org INTEGER;
    v_fk_genre INTEGER;
BEGIN
    -- === VALIDATION ===
    -- Check if entity exists and belongs to tenant
    SELECT id, pk_contact
    INTO v_contact_id, v_contact_pk
    FROM tenant.tb_contact
    WHERE id = input_data.id::UUID
      AND tenant_id = auth_tenant_id;

    IF v_contact_id IS NULL THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id,
            auth_user_id,
            'contact',
            input_data.id::UUID,
            'NOOP',
             'validation:reference_not_found',
            ARRAY['id']::TEXT[],
             'Referenced contact not found',
            NULL, NULL,
            jsonb_build_object('entity_id', input_data.id)
        );
    END IF;
    IF input_data.email_address IS NULL THEN
            RETURN app.log_and_return_mutation(
                auth_tenant_id,
                auth_user_id,
                'contact',
                v_contact_id,
                'NOOP',
                'validation:required_field',
                ARRAY['email_address']::TEXT[],
                'Email_address is required',
                NULL, NULL,
                jsonb_build_object('reason', 'validation_email_address_null')
            );
    END IF;

    -- === UUID → INTEGER RESOLUTION (Trinity Helpers) ===
    IF input_data.customer_org_id IS NOT NULL THEN
        v_fk_customer_org := tenant.organization_pk(input_data.customer_org_id::TEXT, auth_tenant_id);

        IF v_fk_customer_org IS NULL THEN
                RETURN app.log_and_return_mutation(
                    auth_tenant_id,
                    auth_user_id,
                    'contact',
                    v_contact_id,
                    'NOOP',
                     'validation:reference_not_found',
                    ARRAY['customer_org_id']::TEXT[],
                     'Referenced organization not found',
                    NULL, NULL,
                    jsonb_build_object('customer_org_id', input_data.customer_org_id)
                );
        END IF;
    END IF;
    IF input_data.genre_id IS NOT NULL THEN
        v_fk_genre := tenant.genre_pk(input_data.genre_id::TEXT, auth_tenant_id);

        IF v_fk_genre IS NULL THEN
                RETURN app.log_and_return_mutation(
                    auth_tenant_id,
                    auth_user_id,
                    'contact',
                    v_contact_id,
                    'NOOP',
                     'validation:reference_not_found',
                    ARRAY['genre_id']::TEXT[],
                     'Referenced genre not found',
                    NULL, NULL,
                    jsonb_build_object('genre_id', input_data.genre_id)
                );
        END IF;
    END IF;

    -- === BUSINESS LOGIC: UPDATE ===
    UPDATE tenant.tb_contact
    SET
        first_name = input_data.first_name,
        last_name = input_data.last_name,
        email_address = input_data.email_address,
        office_phone = input_data.office_phone,
        mobile_phone = input_data.mobile_phone,
        job_title = input_data.job_title,
        position = input_data.position,
        lang = input_data.lang,
        locale = input_data.locale,
        timezone = input_data.timezone,
        handles = input_data.handles,
        password_hash = input_data.password_hash,
        fk_customer_org = v_fk_customer_org,
        fk_genre = v_fk_genre,
        updated_at = now(),
        updated_by = auth_user_id
    WHERE id = v_contact_id
      AND tenant_id = auth_tenant_id;

    -- === AUDIT & RETURN ===
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'contact',
        v_contact_id,
        'UPDATE',
        'success',
        ARRAY(SELECT jsonb_object_keys(input_payload)),
        'Contact updated successfully',
        (SELECT row_to_json(t.*) FROM tenant.tb_contact t WHERE t.id = v_contact_id)::JSONB,
        NULL
    );
END;
$$;

-- ============================================================================
-- CORE LOGIC: tenant.delete_contact
-- Soft Delete with Audit Trail
-- ============================================================================
CREATE OR REPLACE FUNCTION tenant.delete_contact(
    auth_tenant_id UUID,
    input_entity_id UUID,
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_id UUID;
    v_contact_pk INTEGER;
BEGIN
    -- === VALIDATION ===
    -- Check if entity exists and belongs to tenant
    SELECT id, pk_contact
    INTO v_contact_id, v_contact_pk
    FROM tenant.tb_contact
    WHERE id = input_entity_id
      AND tenant_id = auth_tenant_id
      AND deleted_at IS NULL;  -- Not already soft deleted

    IF v_contact_id IS NULL THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id,
            auth_user_id,
            'contact',
            input_entity_id,
            'NOOP',
             'validation:reference_not_found',
            ARRAY['entity_id']::TEXT[],
             'Referenced contact not found',
            NULL, NULL,
            jsonb_build_object('entity_id', input_entity_id)
        );
    END IF;

    -- === BUSINESS LOGIC: SOFT DELETE ===
    UPDATE tenant.tb_contact
    SET
        deleted_at = now(),
        deleted_by = auth_user_id
    WHERE id = v_contact_id
      AND tenant_id = auth_tenant_id;

    -- === AUDIT & RETURN ===
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'contact',
        v_contact_id,
        'DELETE',
        'success',
        ARRAY['entity_id']::TEXT[],
        'Contact deleted successfully',
        (SELECT row_to_json(t.*) FROM tenant.tb_contact t WHERE t.id = v_contact_id)::JSONB,
        NULL
    );
END;
$$;

-- ============================================================================
-- CORE LOGIC: tenant.activate_contact
-- Custom Business Action
-- ============================================================================
CREATE OR REPLACE FUNCTION tenant.activate_contact(
    auth_tenant_id UUID,
    input_data app.type_activate_contact_input,
    input_payload JSONB,
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_id UUID := input_data.id;
    v_contact_pk INTEGER;
    v_fk_customer_org INTEGER;
    v_fk_genre INTEGER;
BEGIN
    -- Debug: Input parameters
    RAISE NOTICE 'activate_contact: input_data.id=%, auth_tenant_id=%', input_data.id, auth_tenant_id;

    -- === SUCCESS RESPONSE ===
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'contact',
        v_contact_id,
        'CUSTOM',
        'success',
        ARRAY[]::TEXT[],
        'Activate Contact completed',
        (SELECT row_to_json(t.*) FROM tenant.tb_contact t WHERE t.id = v_contact_id)::JSONB,
        NULL
    );
END;
$$;

-- ============================================================================
-- CORE LOGIC: tenant.deactivate_contact
-- Custom Business Action
-- ============================================================================
CREATE OR REPLACE FUNCTION tenant.deactivate_contact(
    auth_tenant_id UUID,
    input_data app.type_deactivate_contact_input,
    input_payload JSONB,
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_id UUID := input_data.id;
    v_contact_pk INTEGER;
    v_fk_customer_org INTEGER;
    v_fk_genre INTEGER;
BEGIN
    -- Debug: Input parameters
    RAISE NOTICE 'deactivate_contact: input_data.id=%, auth_tenant_id=%', input_data.id, auth_tenant_id;

    -- === SUCCESS RESPONSE ===
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'contact',
        v_contact_id,
        'CUSTOM',
        'success',
        ARRAY[]::TEXT[],
        'Deactivate Contact completed',
        (SELECT row_to_json(t.*) FROM tenant.tb_contact t WHERE t.id = v_contact_id)::JSONB,
        NULL
    );
END;
$$;

-- ============================================================================
-- CORE LOGIC: tenant.change_email_address
-- Custom Business Action
-- ============================================================================
CREATE OR REPLACE FUNCTION tenant.change_email_address(
    auth_tenant_id UUID,
    input_data app.type_change_email_address_input,
    input_payload JSONB,
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_id UUID := input_data.id;
    v_contact_pk INTEGER;
    v_fk_customer_org INTEGER;
    v_fk_genre INTEGER;
BEGIN
    -- Debug: Input parameters
    RAISE NOTICE 'change_email_address: input_data.id=%, auth_tenant_id=%', input_data.id, auth_tenant_id;

    -- === SUCCESS RESPONSE ===
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'contact',
        v_contact_id,
        'CUSTOM',
        'success',
        ARRAY[]::TEXT[],
        'Change Email Address completed',
        (SELECT row_to_json(t.*) FROM tenant.tb_contact t WHERE t.id = v_contact_id)::JSONB,
        NULL
    );
END;
$$;

-- ============================================================================
-- CORE LOGIC: tenant.change_office_phone
-- Custom Business Action
-- ============================================================================
CREATE OR REPLACE FUNCTION tenant.change_office_phone(
    auth_tenant_id UUID,
    input_data app.type_change_office_phone_input,
    input_payload JSONB,
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_id UUID := input_data.id;
    v_contact_pk INTEGER;
    v_fk_customer_org INTEGER;
    v_fk_genre INTEGER;
BEGIN
    -- Debug: Input parameters
    RAISE NOTICE 'change_office_phone: input_data.id=%, auth_tenant_id=%', input_data.id, auth_tenant_id;

    -- === SUCCESS RESPONSE ===
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'contact',
        v_contact_id,
        'CUSTOM',
        'success',
        ARRAY[]::TEXT[],
        'Change Office Phone completed',
        (SELECT row_to_json(t.*) FROM tenant.tb_contact t WHERE t.id = v_contact_id)::JSONB,
        NULL
    );
END;
$$;

-- ============================================================================
-- CORE LOGIC: tenant.change_mobile_phone
-- Custom Business Action
-- ============================================================================
CREATE OR REPLACE FUNCTION tenant.change_mobile_phone(
    auth_tenant_id UUID,
    input_data app.type_change_mobile_phone_input,
    input_payload JSONB,
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_id UUID := input_data.id;
    v_contact_pk INTEGER;
    v_fk_customer_org INTEGER;
    v_fk_genre INTEGER;
BEGIN
    -- Debug: Input parameters
    RAISE NOTICE 'change_mobile_phone: input_data.id=%, auth_tenant_id=%', input_data.id, auth_tenant_id;

    -- === SUCCESS RESPONSE ===
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'contact',
        v_contact_id,
        'CUSTOM',
        'success',
        ARRAY[]::TEXT[],
        'Change Mobile Phone completed',
        (SELECT row_to_json(t.*) FROM tenant.tb_contact t WHERE t.id = v_contact_id)::JSONB,
        NULL
    );
END;
$$;

-- ============================================================================
-- CORE LOGIC: tenant.update_contact
-- Business Rules & Data Manipulation
-- ============================================================================
CREATE OR REPLACE FUNCTION tenant.update_contact(
    auth_tenant_id UUID,
    input_data app.type_update_contact_input,
    input_payload JSONB,
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_id UUID;
    v_contact_pk INTEGER;
    v_fk_customer_org INTEGER;
    v_fk_genre INTEGER;
BEGIN
    -- === VALIDATION ===
    -- Check if entity exists and belongs to tenant
    SELECT id, pk_contact
    INTO v_contact_id, v_contact_pk
    FROM tenant.tb_contact
    WHERE id = input_data.id::UUID
      AND tenant_id = auth_tenant_id;

    IF v_contact_id IS NULL THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id,
            auth_user_id,
            'contact',
            input_data.id::UUID,
            'NOOP',
             'validation:reference_not_found',
            ARRAY['id']::TEXT[],
             'Referenced contact not found',
            NULL, NULL,
            jsonb_build_object('entity_id', input_data.id)
        );
    END IF;
    IF input_data.email_address IS NULL THEN
            RETURN app.log_and_return_mutation(
                auth_tenant_id,
                auth_user_id,
                'contact',
                v_contact_id,
                'NOOP',
                'validation:required_field',
                ARRAY['email_address']::TEXT[],
                'Email_address is required',
                NULL, NULL,
                jsonb_build_object('reason', 'validation_email_address_null')
            );
    END IF;

    -- === UUID → INTEGER RESOLUTION (Trinity Helpers) ===
    IF input_data.customer_org_id IS NOT NULL THEN
        v_fk_customer_org := tenant.organization_pk(input_data.customer_org_id::TEXT, auth_tenant_id);

        IF v_fk_customer_org IS NULL THEN
                RETURN app.log_and_return_mutation(
                    auth_tenant_id,
                    auth_user_id,
                    'contact',
                    v_contact_id,
                    'NOOP',
                     'validation:reference_not_found',
                    ARRAY['customer_org_id']::TEXT[],
                     'Referenced organization not found',
                    NULL, NULL,
                    jsonb_build_object('customer_org_id', input_data.customer_org_id)
                );
        END IF;
    END IF;
    IF input_data.genre_id IS NOT NULL THEN
        v_fk_genre := tenant.genre_pk(input_data.genre_id::TEXT, auth_tenant_id);

        IF v_fk_genre IS NULL THEN
                RETURN app.log_and_return_mutation(
                    auth_tenant_id,
                    auth_user_id,
                    'contact',
                    v_contact_id,
                    'NOOP',
                     'validation:reference_not_found',
                    ARRAY['genre_id']::TEXT[],
                     'Referenced genre not found',
                    NULL, NULL,
                    jsonb_build_object('genre_id', input_data.genre_id)
                );
        END IF;
    END IF;

    -- === BUSINESS LOGIC: UPDATE ===
    UPDATE tenant.tb_contact
    SET
        first_name = input_data.first_name,
        last_name = input_data.last_name,
        email_address = input_data.email_address,
        office_phone = input_data.office_phone,
        mobile_phone = input_data.mobile_phone,
        job_title = input_data.job_title,
        position = input_data.position,
        lang = input_data.lang,
        locale = input_data.locale,
        timezone = input_data.timezone,
        handles = input_data.handles,
        password_hash = input_data.password_hash,
        fk_customer_org = v_fk_customer_org,
        fk_genre = v_fk_genre,
        updated_at = now(),
        updated_by = auth_user_id
    WHERE id = v_contact_id
      AND tenant_id = auth_tenant_id;

    -- === AUDIT & RETURN ===
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'contact',
        v_contact_id,
        'UPDATE',
        'success',
        ARRAY(SELECT jsonb_object_keys(input_payload)),
        'Contact updated successfully',
        (SELECT row_to_json(t.*) FROM tenant.tb_contact t WHERE t.id = v_contact_id)::JSONB,
        NULL
    );
END;
$$;

-- ============================================================================
-- CORE LOGIC: tenant.update_contact
-- Business Rules & Data Manipulation
-- ============================================================================
CREATE OR REPLACE FUNCTION tenant.update_contact(
    auth_tenant_id UUID,
    input_data app.type_update_contact_input,
    input_payload JSONB,
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_id UUID;
    v_contact_pk INTEGER;
    v_fk_customer_org INTEGER;
    v_fk_genre INTEGER;
BEGIN
    -- === VALIDATION ===
    -- Check if entity exists and belongs to tenant
    SELECT id, pk_contact
    INTO v_contact_id, v_contact_pk
    FROM tenant.tb_contact
    WHERE id = input_data.id::UUID
      AND tenant_id = auth_tenant_id;

    IF v_contact_id IS NULL THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id,
            auth_user_id,
            'contact',
            input_data.id::UUID,
            'NOOP',
             'validation:reference_not_found',
            ARRAY['id']::TEXT[],
             'Referenced contact not found',
            NULL, NULL,
            jsonb_build_object('entity_id', input_data.id)
        );
    END IF;
    IF input_data.email_address IS NULL THEN
            RETURN app.log_and_return_mutation(
                auth_tenant_id,
                auth_user_id,
                'contact',
                v_contact_id,
                'NOOP',
                'validation:required_field',
                ARRAY['email_address']::TEXT[],
                'Email_address is required',
                NULL, NULL,
                jsonb_build_object('reason', 'validation_email_address_null')
            );
    END IF;

    -- === UUID → INTEGER RESOLUTION (Trinity Helpers) ===
    IF input_data.customer_org_id IS NOT NULL THEN
        v_fk_customer_org := tenant.organization_pk(input_data.customer_org_id::TEXT, auth_tenant_id);

        IF v_fk_customer_org IS NULL THEN
                RETURN app.log_and_return_mutation(
                    auth_tenant_id,
                    auth_user_id,
                    'contact',
                    v_contact_id,
                    'NOOP',
                     'validation:reference_not_found',
                    ARRAY['customer_org_id']::TEXT[],
                     'Referenced organization not found',
                    NULL, NULL,
                    jsonb_build_object('customer_org_id', input_data.customer_org_id)
                );
        END IF;
    END IF;
    IF input_data.genre_id IS NOT NULL THEN
        v_fk_genre := tenant.genre_pk(input_data.genre_id::TEXT, auth_tenant_id);

        IF v_fk_genre IS NULL THEN
                RETURN app.log_and_return_mutation(
                    auth_tenant_id,
                    auth_user_id,
                    'contact',
                    v_contact_id,
                    'NOOP',
                     'validation:reference_not_found',
                    ARRAY['genre_id']::TEXT[],
                     'Referenced genre not found',
                    NULL, NULL,
                    jsonb_build_object('genre_id', input_data.genre_id)
                );
        END IF;
    END IF;

    -- === BUSINESS LOGIC: UPDATE ===
    UPDATE tenant.tb_contact
    SET
        first_name = input_data.first_name,
        last_name = input_data.last_name,
        email_address = input_data.email_address,
        office_phone = input_data.office_phone,
        mobile_phone = input_data.mobile_phone,
        job_title = input_data.job_title,
        position = input_data.position,
        lang = input_data.lang,
        locale = input_data.locale,
        timezone = input_data.timezone,
        handles = input_data.handles,
        password_hash = input_data.password_hash,
        fk_customer_org = v_fk_customer_org,
        fk_genre = v_fk_genre,
        updated_at = now(),
        updated_by = auth_user_id
    WHERE id = v_contact_id
      AND tenant_id = auth_tenant_id;

    -- === AUDIT & RETURN ===
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'contact',
        v_contact_id,
        'UPDATE',
        'success',
        ARRAY(SELECT jsonb_object_keys(input_payload)),
        'Contact updated successfully',
        (SELECT row_to_json(t.*) FROM tenant.tb_contact t WHERE t.id = v_contact_id)::JSONB,
        NULL
    );
END;
$$;

-- ============================================================================
-- CORE LOGIC: tenant.change_timezone
-- Custom Business Action
-- ============================================================================
CREATE OR REPLACE FUNCTION tenant.change_timezone(
    auth_tenant_id UUID,
    input_data app.type_change_timezone_input,
    input_payload JSONB,
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_id UUID := input_data.id;
    v_contact_pk INTEGER;
    v_fk_customer_org INTEGER;
    v_fk_genre INTEGER;
BEGIN
    -- Debug: Input parameters
    RAISE NOTICE 'change_timezone: input_data.id=%, auth_tenant_id=%', input_data.id, auth_tenant_id;

    -- === SUCCESS RESPONSE ===
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'contact',
        v_contact_id,
        'CUSTOM',
        'success',
        ARRAY[]::TEXT[],
        'Change Timezone completed',
        (SELECT row_to_json(t.*) FROM tenant.tb_contact t WHERE t.id = v_contact_id)::JSONB,
        NULL
    );
END;
$$;

-- ============================================================================
-- CORE LOGIC: tenant.update_contact
-- Business Rules & Data Manipulation
-- ============================================================================
CREATE OR REPLACE FUNCTION tenant.update_contact(
    auth_tenant_id UUID,
    input_data app.type_update_contact_input,
    input_payload JSONB,
    auth_user_id UUID
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    v_contact_id UUID;
    v_contact_pk INTEGER;
    v_fk_customer_org INTEGER;
    v_fk_genre INTEGER;
BEGIN
    -- === VALIDATION ===
    -- Check if entity exists and belongs to tenant
    SELECT id, pk_contact
    INTO v_contact_id, v_contact_pk
    FROM tenant.tb_contact
    WHERE id = input_data.id::UUID
      AND tenant_id = auth_tenant_id;

    IF v_contact_id IS NULL THEN
        RETURN app.log_and_return_mutation(
            auth_tenant_id,
            auth_user_id,
            'contact',
            input_data.id::UUID,
            'NOOP',
             'validation:reference_not_found',
            ARRAY['id']::TEXT[],
             'Referenced contact not found',
            NULL, NULL,
            jsonb_build_object('entity_id', input_data.id)
        );
    END IF;
    IF input_data.email_address IS NULL THEN
            RETURN app.log_and_return_mutation(
                auth_tenant_id,
                auth_user_id,
                'contact',
                v_contact_id,
                'NOOP',
                'validation:required_field',
                ARRAY['email_address']::TEXT[],
                'Email_address is required',
                NULL, NULL,
                jsonb_build_object('reason', 'validation_email_address_null')
            );
    END IF;

    -- === UUID → INTEGER RESOLUTION (Trinity Helpers) ===
    IF input_data.customer_org_id IS NOT NULL THEN
        v_fk_customer_org := tenant.organization_pk(input_data.customer_org_id::TEXT, auth_tenant_id);

        IF v_fk_customer_org IS NULL THEN
                RETURN app.log_and_return_mutation(
                    auth_tenant_id,
                    auth_user_id,
                    'contact',
                    v_contact_id,
                    'NOOP',
                     'validation:reference_not_found',
                    ARRAY['customer_org_id']::TEXT[],
                     'Referenced organization not found',
                    NULL, NULL,
                    jsonb_build_object('customer_org_id', input_data.customer_org_id)
                );
        END IF;
    END IF;
    IF input_data.genre_id IS NOT NULL THEN
        v_fk_genre := tenant.genre_pk(input_data.genre_id::TEXT, auth_tenant_id);

        IF v_fk_genre IS NULL THEN
                RETURN app.log_and_return_mutation(
                    auth_tenant_id,
                    auth_user_id,
                    'contact',
                    v_contact_id,
                    'NOOP',
                     'validation:reference_not_found',
                    ARRAY['genre_id']::TEXT[],
                     'Referenced genre not found',
                    NULL, NULL,
                    jsonb_build_object('genre_id', input_data.genre_id)
                );
        END IF;
    END IF;

    -- === BUSINESS LOGIC: UPDATE ===
    UPDATE tenant.tb_contact
    SET
        first_name = input_data.first_name,
        last_name = input_data.last_name,
        email_address = input_data.email_address,
        office_phone = input_data.office_phone,
        mobile_phone = input_data.mobile_phone,
        job_title = input_data.job_title,
        position = input_data.position,
        lang = input_data.lang,
        locale = input_data.locale,
        timezone = input_data.timezone,
        handles = input_data.handles,
        password_hash = input_data.password_hash,
        fk_customer_org = v_fk_customer_org,
        fk_genre = v_fk_genre,
        updated_at = now(),
        updated_by = auth_user_id
    WHERE id = v_contact_id
      AND tenant_id = auth_tenant_id;

    -- === AUDIT & RETURN ===
    RETURN app.log_and_return_mutation(
        auth_tenant_id,
        auth_user_id,
        'contact',
        v_contact_id,
        'UPDATE',
        'success',
        ARRAY(SELECT jsonb_object_keys(input_payload)),
        'Contact updated successfully',
        (SELECT row_to_json(t.*) FROM tenant.tb_contact t WHERE t.id = v_contact_id)::JSONB,
        NULL
    );
END;
$$;

-- FraiseQL Mutation Annotations (Team D)
COMMENT ON FUNCTION tenant.create_contact IS
'Core business logic for create contact.

Validation:
- Input validation
- Permission checks

Operations:
- Trinity FK resolution (UUID → INTEGER)
- INSERT operation on tenant.tb_contact
- Audit logging via app.log_and_return_mutation

Called by: app.create_contact (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';

COMMENT ON FUNCTION tenant.update_contact IS
'Core business logic for update contact.

Validation:
- Input validation
- Permission checks

Operations:
- Trinity FK resolution (UUID → INTEGER)
- UPDATE operation on tenant.tb_contact
- Audit logging via app.log_and_return_mutation

Called by: app.update_contact (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';

COMMENT ON FUNCTION tenant.delete_contact IS
'Core business logic for delete contact.

Validation:
- Input validation
- Permission checks

Operations:
- Trinity FK resolution (UUID → INTEGER)
- DELETE operation on tenant.tb_contact
- Audit logging via app.log_and_return_mutation

Called by: app.delete_contact (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';

COMMENT ON FUNCTION tenant.activate_contact IS
'Core business logic for activate contact.

Validation:
- Input validation
- Permission checks

Operations:
- Trinity FK resolution (UUID → INTEGER)
- OPERATION operation on tenant.tb_contact
- Audit logging via app.log_and_return_mutation

Called by: app.activate_contact (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';

COMMENT ON FUNCTION tenant.deactivate_contact IS
'Core business logic for deactivate contact.

Validation:
- Input validation
- Permission checks

Operations:
- Trinity FK resolution (UUID → INTEGER)
- OPERATION operation on tenant.tb_contact
- Audit logging via app.log_and_return_mutation

Called by: app.deactivate_contact (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';

COMMENT ON FUNCTION tenant.change_email_address IS
'Core business logic for change email address.

Validation:
- Input validation
- Permission checks

Operations:
- Trinity FK resolution (UUID → INTEGER)
- OPERATION operation on tenant.tb_contact
- Audit logging via app.log_and_return_mutation

Called by: app.change_email_address (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';

COMMENT ON FUNCTION tenant.change_office_phone IS
'Core business logic for change office phone.

Validation:
- Input validation
- Permission checks

Operations:
- Trinity FK resolution (UUID → INTEGER)
- OPERATION operation on tenant.tb_contact
- Audit logging via app.log_and_return_mutation

Called by: app.change_office_phone (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';

COMMENT ON FUNCTION tenant.change_mobile_phone IS
'Core business logic for change mobile phone.

Validation:
- Input validation
- Permission checks

Operations:
- Trinity FK resolution (UUID → INTEGER)
- OPERATION operation on tenant.tb_contact
- Audit logging via app.log_and_return_mutation

Called by: app.change_mobile_phone (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';

COMMENT ON FUNCTION tenant.update_job_title IS
'Core business logic for update job title.

Validation:
- Input validation
- Permission checks

Operations:
- Trinity FK resolution (UUID → INTEGER)
- UPDATE operation on tenant.tb_contact
- Audit logging via app.log_and_return_mutation

Called by: app.update_job_title (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';

COMMENT ON FUNCTION tenant.update_position IS
'Core business logic for update position.

Validation:
- Input validation
- Permission checks

Operations:
- Trinity FK resolution (UUID → INTEGER)
- UPDATE operation on tenant.tb_contact
- Audit logging via app.log_and_return_mutation

Called by: app.update_position (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';

COMMENT ON FUNCTION tenant.change_timezone IS
'Core business logic for change timezone.

Validation:
- Input validation
- Permission checks

Operations:
- Trinity FK resolution (UUID → INTEGER)
- OPERATION operation on tenant.tb_contact
- Audit logging via app.log_and_return_mutation

Called by: app.change_timezone (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';

COMMENT ON FUNCTION tenant.update_password IS
'Core business logic for update password.

Validation:
- Input validation
- Permission checks

Operations:
- Trinity FK resolution (UUID → INTEGER)
- UPDATE operation on tenant.tb_contact
- Audit logging via app.log_and_return_mutation

Called by: app.update_password (GraphQL mutation)
Returns: app.mutation_result (success/failure status)';

-- App Wrapper Functions
-- ============================================================================
-- APP WRAPPER: create_contact
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.create_contact(
    auth_tenant_id UUID,              -- JWT context: tenant_id
    auth_user_id UUID,                -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL/REST)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_create_contact_input;
BEGIN
    -- Convert JSONB → Typed Composite
    input_data := jsonb_populate_record(
        NULL::app.type_create_contact_input,
        input_payload
    );

    -- Delegate to core business logic
    RETURN tenant.create_contact(
        auth_tenant_id,
        input_data,
        input_payload,
        auth_user_id
    );
EXCEPTION
    WHEN OTHERS THEN
        -- Handle unexpected errors
        RETURN ROW(
            '00000000-0000-0000-0000-000000000000'::UUID,
            ARRAY[]::TEXT[],
            'failed:unexpected_error',
            'An unexpected error occurred',
            NULL::JSONB,
            jsonb_build_object('error', SQLERRM, 'detail', SQLSTATE)
        )::app.mutation_result;
END;
$$;

COMMENT ON FUNCTION app.create_contact IS
'Creates a new Contact record.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: createContact
input_type: app.type_create_contact_input
success_type: CreateContactSuccess
failure_type: CreateContactError';

-- ============================================================================
-- APP WRAPPER: update_contact
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.update_contact(
    auth_tenant_id UUID,              -- JWT context: tenant_id
    auth_user_id UUID,                -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL/REST)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_update_contact_input;
BEGIN
    -- Convert JSONB → Typed Composite
    input_data := jsonb_populate_record(
        NULL::app.type_update_contact_input,
        input_payload
    );

    -- Delegate to core business logic
    RETURN tenant.update_contact(
        auth_tenant_id,
        input_data,
        input_payload,
        auth_user_id
    );
EXCEPTION
    WHEN OTHERS THEN
        -- Handle unexpected errors
        RETURN ROW(
            '00000000-0000-0000-0000-000000000000'::UUID,
            ARRAY[]::TEXT[],
            'failed:unexpected_error',
            'An unexpected error occurred',
            NULL::JSONB,
            jsonb_build_object('error', SQLERRM, 'detail', SQLSTATE)
        )::app.mutation_result;
END;
$$;

COMMENT ON FUNCTION app.update_contact IS
'Updates an existing Contact record.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: updateContact
input_type: app.type_update_contact_input
success_type: UpdateContactSuccess
failure_type: UpdateContactError';

-- ============================================================================
-- APP WRAPPER: delete_contact
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.delete_contact(
    auth_tenant_id UUID,              -- JWT context: tenant_id
    auth_user_id UUID,                -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL/REST)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_delete_contact_input;
BEGIN
    -- Convert JSONB → Typed Composite
    input_data := jsonb_populate_record(
        NULL::app.type_delete_contact_input,
        input_payload
    );

    -- Delegate to core business logic
    RETURN tenant.delete_contact(
        auth_tenant_id,
        input_data.id,
        auth_user_id
    );
EXCEPTION
    WHEN OTHERS THEN
        -- Handle unexpected errors
        RETURN ROW(
            '00000000-0000-0000-0000-000000000000'::UUID,
            ARRAY[]::TEXT[],
            'failed:unexpected_error',
            'An unexpected error occurred',
            NULL::JSONB,
            jsonb_build_object('error', SQLERRM, 'detail', SQLSTATE)
        )::app.mutation_result;
END;
$$;

COMMENT ON FUNCTION app.delete_contact IS
'Deletes an existing Contact record.
Validates permissions and delegates to core business logic.

@fraiseql:mutation
name: deleteContact
input_type: app.type_delete_contact_input
success_type: DeleteContactSuccess
failure_type: DeleteContactError';

-- ============================================================================
-- APP WRAPPER: activate_contact
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.activate_contact(
    auth_tenant_id UUID,              -- JWT context: tenant_id
    auth_user_id UUID,                -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL/REST)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_activate_contact_input;
BEGIN
    -- Convert JSONB → Typed Composite
    input_data := jsonb_populate_record(
        NULL::app.type_activate_contact_input,
        input_payload
    );

    -- Delegate to core business logic
    RETURN tenant.activate_contact(
        auth_tenant_id,
        input_data,
        input_payload,
        auth_user_id
    );
EXCEPTION
    WHEN OTHERS THEN
        -- Handle unexpected errors
        RETURN ROW(
            '00000000-0000-0000-0000-000000000000'::UUID,
            ARRAY[]::TEXT[],
            'failed:unexpected_error',
            'An unexpected error occurred',
            NULL::JSONB,
            jsonb_build_object('error', SQLERRM, 'detail', SQLSTATE)
        )::app.mutation_result;
END;
$$;

COMMENT ON FUNCTION app.activate_contact IS
'Performs activate contact operation on Contact.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: activateContact
input_type: app.type_activate_contact_input
success_type: ActivateContactSuccess
failure_type: ActivateContactError';

-- ============================================================================
-- APP WRAPPER: deactivate_contact
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.deactivate_contact(
    auth_tenant_id UUID,              -- JWT context: tenant_id
    auth_user_id UUID,                -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL/REST)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_deactivate_contact_input;
BEGIN
    -- Convert JSONB → Typed Composite
    input_data := jsonb_populate_record(
        NULL::app.type_deactivate_contact_input,
        input_payload
    );

    -- Delegate to core business logic
    RETURN tenant.deactivate_contact(
        auth_tenant_id,
        input_data,
        input_payload,
        auth_user_id
    );
EXCEPTION
    WHEN OTHERS THEN
        -- Handle unexpected errors
        RETURN ROW(
            '00000000-0000-0000-0000-000000000000'::UUID,
            ARRAY[]::TEXT[],
            'failed:unexpected_error',
            'An unexpected error occurred',
            NULL::JSONB,
            jsonb_build_object('error', SQLERRM, 'detail', SQLSTATE)
        )::app.mutation_result;
END;
$$;

COMMENT ON FUNCTION app.deactivate_contact IS
'Performs deactivate contact operation on Contact.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: deactivateContact
input_type: app.type_deactivate_contact_input
success_type: DeactivateContactSuccess
failure_type: DeactivateContactError';

-- ============================================================================
-- APP WRAPPER: change_email_address
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.change_email_address(
    auth_tenant_id UUID,              -- JWT context: tenant_id
    auth_user_id UUID,                -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL/REST)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_change_email_address_input;
BEGIN
    -- Convert JSONB → Typed Composite
    input_data := jsonb_populate_record(
        NULL::app.type_change_email_address_input,
        input_payload
    );

    -- Delegate to core business logic
    RETURN tenant.change_email_address(
        auth_tenant_id,
        input_data,
        input_payload,
        auth_user_id
    );
EXCEPTION
    WHEN OTHERS THEN
        -- Handle unexpected errors
        RETURN ROW(
            '00000000-0000-0000-0000-000000000000'::UUID,
            ARRAY[]::TEXT[],
            'failed:unexpected_error',
            'An unexpected error occurred',
            NULL::JSONB,
            jsonb_build_object('error', SQLERRM, 'detail', SQLSTATE)
        )::app.mutation_result;
END;
$$;

COMMENT ON FUNCTION app.change_email_address IS
'Performs change email address operation on Contact.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: changeEmailAddress
input_type: app.type_change_email_address_input
success_type: ChangeEmailAddressSuccess
failure_type: ChangeEmailAddressError';

-- ============================================================================
-- APP WRAPPER: change_office_phone
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.change_office_phone(
    auth_tenant_id UUID,              -- JWT context: tenant_id
    auth_user_id UUID,                -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL/REST)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_change_office_phone_input;
BEGIN
    -- Convert JSONB → Typed Composite
    input_data := jsonb_populate_record(
        NULL::app.type_change_office_phone_input,
        input_payload
    );

    -- Delegate to core business logic
    RETURN tenant.change_office_phone(
        auth_tenant_id,
        input_data,
        input_payload,
        auth_user_id
    );
EXCEPTION
    WHEN OTHERS THEN
        -- Handle unexpected errors
        RETURN ROW(
            '00000000-0000-0000-0000-000000000000'::UUID,
            ARRAY[]::TEXT[],
            'failed:unexpected_error',
            'An unexpected error occurred',
            NULL::JSONB,
            jsonb_build_object('error', SQLERRM, 'detail', SQLSTATE)
        )::app.mutation_result;
END;
$$;

COMMENT ON FUNCTION app.change_office_phone IS
'Performs change office phone operation on Contact.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: changeOfficePhone
input_type: app.type_change_office_phone_input
success_type: ChangeOfficePhoneSuccess
failure_type: ChangeOfficePhoneError';

-- ============================================================================
-- APP WRAPPER: change_mobile_phone
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.change_mobile_phone(
    auth_tenant_id UUID,              -- JWT context: tenant_id
    auth_user_id UUID,                -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL/REST)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_change_mobile_phone_input;
BEGIN
    -- Convert JSONB → Typed Composite
    input_data := jsonb_populate_record(
        NULL::app.type_change_mobile_phone_input,
        input_payload
    );

    -- Delegate to core business logic
    RETURN tenant.change_mobile_phone(
        auth_tenant_id,
        input_data,
        input_payload,
        auth_user_id
    );
EXCEPTION
    WHEN OTHERS THEN
        -- Handle unexpected errors
        RETURN ROW(
            '00000000-0000-0000-0000-000000000000'::UUID,
            ARRAY[]::TEXT[],
            'failed:unexpected_error',
            'An unexpected error occurred',
            NULL::JSONB,
            jsonb_build_object('error', SQLERRM, 'detail', SQLSTATE)
        )::app.mutation_result;
END;
$$;

COMMENT ON FUNCTION app.change_mobile_phone IS
'Performs change mobile phone operation on Contact.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: changeMobilePhone
input_type: app.type_change_mobile_phone_input
success_type: ChangeMobilePhoneSuccess
failure_type: ChangeMobilePhoneError';

-- ============================================================================
-- APP WRAPPER: update_job_title
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.update_job_title(
    auth_tenant_id UUID,              -- JWT context: tenant_id
    auth_user_id UUID,                -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL/REST)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_update_job_title_input;
BEGIN
    -- Convert JSONB → Typed Composite
    input_data := jsonb_populate_record(
        NULL::app.type_update_job_title_input,
        input_payload
    );

    -- Delegate to core business logic
    RETURN tenant.update_job_title(
        auth_tenant_id,
        input_data,
        input_payload,
        auth_user_id
    );
EXCEPTION
    WHEN OTHERS THEN
        -- Handle unexpected errors
        RETURN ROW(
            '00000000-0000-0000-0000-000000000000'::UUID,
            ARRAY[]::TEXT[],
            'failed:unexpected_error',
            'An unexpected error occurred',
            NULL::JSONB,
            jsonb_build_object('error', SQLERRM, 'detail', SQLSTATE)
        )::app.mutation_result;
END;
$$;

COMMENT ON FUNCTION app.update_job_title IS
'Updates an existing Contact record.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: updateJobTitle
input_type: app.type_update_job_title_input
success_type: UpdateJobTitleSuccess
failure_type: UpdateJobTitleError';

-- ============================================================================
-- APP WRAPPER: update_position
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.update_position(
    auth_tenant_id UUID,              -- JWT context: tenant_id
    auth_user_id UUID,                -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL/REST)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_update_position_input;
BEGIN
    -- Convert JSONB → Typed Composite
    input_data := jsonb_populate_record(
        NULL::app.type_update_position_input,
        input_payload
    );

    -- Delegate to core business logic
    RETURN tenant.update_position(
        auth_tenant_id,
        input_data,
        input_payload,
        auth_user_id
    );
EXCEPTION
    WHEN OTHERS THEN
        -- Handle unexpected errors
        RETURN ROW(
            '00000000-0000-0000-0000-000000000000'::UUID,
            ARRAY[]::TEXT[],
            'failed:unexpected_error',
            'An unexpected error occurred',
            NULL::JSONB,
            jsonb_build_object('error', SQLERRM, 'detail', SQLSTATE)
        )::app.mutation_result;
END;
$$;

COMMENT ON FUNCTION app.update_position IS
'Updates an existing Contact record.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: updatePosition
input_type: app.type_update_position_input
success_type: UpdatePositionSuccess
failure_type: UpdatePositionError';

-- ============================================================================
-- APP WRAPPER: change_timezone
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.change_timezone(
    auth_tenant_id UUID,              -- JWT context: tenant_id
    auth_user_id UUID,                -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL/REST)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_change_timezone_input;
BEGIN
    -- Convert JSONB → Typed Composite
    input_data := jsonb_populate_record(
        NULL::app.type_change_timezone_input,
        input_payload
    );

    -- Delegate to core business logic
    RETURN tenant.change_timezone(
        auth_tenant_id,
        input_data,
        input_payload,
        auth_user_id
    );
EXCEPTION
    WHEN OTHERS THEN
        -- Handle unexpected errors
        RETURN ROW(
            '00000000-0000-0000-0000-000000000000'::UUID,
            ARRAY[]::TEXT[],
            'failed:unexpected_error',
            'An unexpected error occurred',
            NULL::JSONB,
            jsonb_build_object('error', SQLERRM, 'detail', SQLSTATE)
        )::app.mutation_result;
END;
$$;

COMMENT ON FUNCTION app.change_timezone IS
'Performs change timezone operation on Contact.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: changeTimezone
input_type: app.type_change_timezone_input
success_type: ChangeTimezoneSuccess
failure_type: ChangeTimezoneError';

-- ============================================================================
-- APP WRAPPER: update_password
-- API Entry Point (GraphQL/REST)
-- ============================================================================
CREATE OR REPLACE FUNCTION app.update_password(
    auth_tenant_id UUID,              -- JWT context: tenant_id
    auth_user_id UUID,                -- JWT context: user_id
    input_payload JSONB               -- User input (GraphQL/REST)
) RETURNS app.mutation_result
LANGUAGE plpgsql
AS $$
DECLARE
    input_data app.type_update_password_input;
BEGIN
    -- Convert JSONB → Typed Composite
    input_data := jsonb_populate_record(
        NULL::app.type_update_password_input,
        input_payload
    );

    -- Delegate to core business logic
    RETURN tenant.update_password(
        auth_tenant_id,
        input_data,
        input_payload,
        auth_user_id
    );
EXCEPTION
    WHEN OTHERS THEN
        -- Handle unexpected errors
        RETURN ROW(
            '00000000-0000-0000-0000-000000000000'::UUID,
            ARRAY[]::TEXT[],
            'failed:unexpected_error',
            'An unexpected error occurred',
            NULL::JSONB,
            jsonb_build_object('error', SQLERRM, 'detail', SQLSTATE)
        )::app.mutation_result;
END;
$$;

COMMENT ON FUNCTION app.update_password IS
'Updates an existing Contact record.
Validates input and delegates to core business logic.

@fraiseql:mutation
name: updatePassword
input_type: app.type_update_password_input
success_type: UpdatePasswordSuccess
failure_type: UpdatePasswordError';

-- Trinity Helper Functions



-- ============================================================================
-- Trinity Helper: tenant.contact_pk()
-- ============================================================================
-- Converts between UUID and INTEGER representations
-- ============================================================================

-- UUID/identifier/text → INTEGER (pk)
CREATE OR REPLACE FUNCTION tenant.contact_pk(p_identifier TEXT, p_tenant_id UUID)
RETURNS INTEGER
LANGUAGE sql STABLE
AS $$
    SELECT pk_contact
    FROM tenant.tb_contact
    WHERE (id::TEXT = p_identifier
        OR pk_contact::TEXT = p_identifier)
      AND tenant_id = p_tenant_id
    LIMIT 1;
$$;

COMMENT ON FUNCTION tenant.contact_pk(TEXT, UUID) IS
'Trinity Pattern: Resolve entity identifier to internal INTEGER primary key.
Accepts UUID, text identifier, or integer pk and returns pk_contact.';




-- ============================================================================
-- Trinity Helper: tenant.contact_id()
-- ============================================================================
-- Converts between UUID and INTEGER representations
-- ============================================================================

-- INTEGER (pk) → UUID
CREATE OR REPLACE FUNCTION tenant.contact_id(p_pk INTEGER)
RETURNS UUID
LANGUAGE sql STABLE
AS $$
    SELECT id FROM tenant.tb_contact
    WHERE pk_contact = p_pk;
$$;

COMMENT ON FUNCTION tenant.contact_id(INTEGER) IS
'Trinity Pattern: Convert internal INTEGER primary key to external UUID identifier.';