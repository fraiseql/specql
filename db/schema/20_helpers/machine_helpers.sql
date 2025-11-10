


-- ============================================================================
-- Trinity Helper: tenant.machine_pk()
-- ============================================================================
-- Converts between UUID and INTEGER representations
-- ============================================================================

-- UUID/identifier/text → INTEGER (pk)
CREATE OR REPLACE FUNCTION tenant.machine_pk(p_identifier TEXT, p_tenant_id UUID)
RETURNS INTEGER
LANGUAGE sql STABLE
AS $$
    SELECT pk_machine
    FROM tenant.tb_machine
    WHERE (id::TEXT = p_identifier
        OR pk_machine::TEXT = p_identifier)
      AND tenant_id = p_tenant_id
    LIMIT 1;
$$;

COMMENT ON FUNCTION tenant.machine_pk(TEXT, UUID) IS
'Trinity Pattern: Resolve entity identifier to internal INTEGER primary key.
Accepts UUID, text identifier, or integer pk and returns pk_machine.';




-- ============================================================================
-- Trinity Helper: tenant.machine_id()
-- ============================================================================
-- Converts between UUID and INTEGER representations
-- ============================================================================

-- INTEGER (pk) → UUID
CREATE OR REPLACE FUNCTION tenant.machine_id(p_pk INTEGER)
RETURNS UUID
LANGUAGE sql STABLE
AS $$
    SELECT id FROM tenant.tb_machine
    WHERE pk_machine = p_pk;
$$;

COMMENT ON FUNCTION tenant.machine_id(INTEGER) IS
'Trinity Pattern: Convert internal INTEGER primary key to external UUID identifier.';