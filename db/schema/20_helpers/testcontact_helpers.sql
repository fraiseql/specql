


-- ============================================================================
-- Trinity Helper: crm.testcontact_pk()
-- ============================================================================
-- Converts between UUID and INTEGER representations
-- ============================================================================

-- UUID/identifier/text → INTEGER (pk)
CREATE OR REPLACE FUNCTION crm.testcontact_pk(p_identifier TEXT)
RETURNS INTEGER
LANGUAGE sql STABLE
AS $$
    SELECT pk_test_contact
    FROM crm.tb_test_contact
    WHERE (id::TEXT = p_identifier
        OR pk_test_contact::TEXT = p_identifier)
    LIMIT 1;
$$;

COMMENT ON FUNCTION crm.testcontact_pk(TEXT, UUID) IS
'Trinity Pattern: Resolve entity identifier to internal INTEGER primary key.
Accepts UUID, text identifier, or integer pk and returns pk_test_contact.';




-- ============================================================================
-- Trinity Helper: crm.testcontact_id()
-- ============================================================================
-- Converts between UUID and INTEGER representations
-- ============================================================================

-- INTEGER (pk) → UUID
CREATE OR REPLACE FUNCTION crm.testcontact_id(p_pk INTEGER)
RETURNS UUID
LANGUAGE sql STABLE
AS $$
    SELECT id FROM crm.tb_test_contact
    WHERE pk_test_contact = p_pk;
$$;

COMMENT ON FUNCTION crm.testcontact_id(INTEGER) IS
'Trinity Pattern: Convert internal INTEGER primary key to external UUID identifier.';