


-- ============================================================================
-- Trinity Helper: catalog.manufacturerrange_pk()
-- ============================================================================
-- Converts between UUID and INTEGER representations
-- ============================================================================

-- UUID/identifier/text → INTEGER (pk)
CREATE OR REPLACE FUNCTION catalog.manufacturerrange_pk(p_identifier TEXT)
RETURNS INTEGER
LANGUAGE sql STABLE
AS $$
    SELECT pk_manufacturer_range
    FROM catalog.tb_manufacturer_range
    WHERE (id::TEXT = p_identifier
        OR pk_manufacturer_range::TEXT = p_identifier)
    LIMIT 1;
$$;

COMMENT ON FUNCTION catalog.manufacturerrange_pk(TEXT, UUID) IS
'Trinity Pattern: Resolve entity identifier to internal INTEGER primary key.
Accepts UUID, text identifier, or integer pk and returns pk_manufacturer_range.';




-- ============================================================================
-- Trinity Helper: catalog.manufacturerrange_id()
-- ============================================================================
-- Converts between UUID and INTEGER representations
-- ============================================================================

-- INTEGER (pk) → UUID
CREATE OR REPLACE FUNCTION catalog.manufacturerrange_id(p_pk INTEGER)
RETURNS UUID
LANGUAGE sql STABLE
AS $$
    SELECT id FROM catalog.tb_manufacturer_range
    WHERE pk_manufacturer_range = p_pk;
$$;

COMMENT ON FUNCTION catalog.manufacturerrange_id(INTEGER) IS
'Trinity Pattern: Convert internal INTEGER primary key to external UUID identifier.';