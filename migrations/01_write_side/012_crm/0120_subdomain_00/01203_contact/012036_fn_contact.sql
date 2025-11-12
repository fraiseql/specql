


-- ============================================================================
-- Trinity Helper: crm.contact_pk()
-- ============================================================================
-- Converts between UUID and INTEGER representations
-- ============================================================================

-- UUID/identifier/text → INTEGER (pk)
CREATE OR REPLACE FUNCTION crm.contact_pk(p_identifier TEXT, p_tenant_id UUID)
RETURNS INTEGER
LANGUAGE sql STABLE
AS $$
    SELECT pk_contact
    FROM crm.tb_contact
    WHERE (id::TEXT = p_identifier
        OR pk_contact::TEXT = p_identifier)
      AND tenant_id = p_tenant_id
    LIMIT 1;
$$;

COMMENT ON FUNCTION crm.contact_pk(TEXT, UUID) IS
'Trinity Pattern: Resolve entity identifier to internal INTEGER primary key.
Accepts UUID, text identifier, or integer pk and returns pk_contact.';




-- ============================================================================
-- Trinity Helper: crm.contact_id()
-- ============================================================================
-- Converts between UUID and INTEGER representations
-- ============================================================================

-- INTEGER (pk) → UUID
CREATE OR REPLACE FUNCTION crm.contact_id(p_pk INTEGER)
RETURNS UUID
LANGUAGE sql STABLE
AS $$
    SELECT id FROM crm.tb_contact
    WHERE pk_contact = p_pk;
$$;

COMMENT ON FUNCTION crm.contact_id(INTEGER) IS
'Trinity Pattern: Convert internal INTEGER primary key to external UUID identifier.';