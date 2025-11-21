-- ============================================================================
-- INPUT TYPES FOR TASK ENTITY
-- Auto-generated input type definitions for Task mutations
-- ============================================================================

-- Input Type for create

-- ============================================================================
-- INPUT TYPE: type_create_input
-- For action: create
-- ============================================================================
CREATE TYPE app.type_create_input AS (

    title TEXT,

    description TEXT,

    priority TEXT

);

-- FraiseQL metadata
COMMENT ON TYPE app.type_create_input IS
'Input parameters for Create.

@fraiseql:composite
name: CreateInput
tier: 2';


-- Field metadata

COMMENT ON COLUMN app.type_create_input.title IS
'Title (optional).

@fraiseql:field
name: title
type: String
required: false';

COMMENT ON COLUMN app.type_create_input.description IS
'Description (optional).

@fraiseql:field
name: description
type: String
required: false';

COMMENT ON COLUMN app.type_create_input.priority IS
'Priority (low, medium, high).

@fraiseql:field
name: priority
type: String
required: false
enumValues: low, medium, high';
