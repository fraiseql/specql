


-- ============================================================================
-- Trinity Helper: catalog.manufacturer_pk()
-- ============================================================================
-- Converts between UUID and INTEGER representations
-- ============================================================================

-- UUID/identifier/text → INTEGER (pk)
CREATE OR REPLACE FUNCTION catalog.manufacturer_pk(p_identifier TEXT)
RETURNS INTEGER
LANGUAGE sql STABLE
AS $$
    SELECT pk_manufacturer
    FROM catalog.tb_manufacturer
    WHERE (id::TEXT = p_identifier
        OR pk_manufacturer::TEXT = p_identifier)
    LIMIT 1;
$$;

COMMENT ON FUNCTION catalog.manufacturer_pk(TEXT, UUID) IS
'Trinity Pattern: Resolve entity identifier to internal INTEGER primary key.
Accepts UUID, text identifier, or integer pk and returns pk_manufacturer.';




-- ============================================================================
-- Trinity Helper: catalog.manufacturer_id()
-- ============================================================================
-- Converts between UUID and INTEGER representations
-- ============================================================================

-- INTEGER (pk) → UUID
CREATE OR REPLACE FUNCTION catalog.manufacturer_id(p_pk INTEGER)
RETURNS UUID
LANGUAGE sql STABLE
AS $$
    SELECT id FROM catalog.tb_manufacturer
    WHERE pk_manufacturer = p_pk;
$$;

COMMENT ON FUNCTION catalog.manufacturer_id(INTEGER) IS
'Trinity Pattern: Convert internal INTEGER primary key to external UUID identifier.';