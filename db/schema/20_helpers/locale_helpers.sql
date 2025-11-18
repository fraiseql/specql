


-- ============================================================================
-- Trinity Helper: catalog.locale_pk()
-- ============================================================================
-- Converts between UUID and INTEGER representations
-- ============================================================================

-- UUID/identifier/text → INTEGER (pk)
CREATE OR REPLACE FUNCTION catalog.locale_pk(p_identifier TEXT)
RETURNS INTEGER
LANGUAGE sql STABLE
AS $$
    SELECT pk_locale
    FROM catalog.tb_locale
    WHERE (id::TEXT = p_identifier
        OR pk_locale::TEXT = p_identifier)
    LIMIT 1;
$$;

COMMENT ON FUNCTION catalog.locale_pk(TEXT, UUID) IS
'Trinity Pattern: Resolve entity identifier to internal INTEGER primary key.
Accepts UUID, text identifier, or integer pk and returns pk_locale.';




-- ============================================================================
-- Trinity Helper: catalog.locale_id()
-- ============================================================================
-- Converts between UUID and INTEGER representations
-- ============================================================================

-- INTEGER (pk) → UUID
CREATE OR REPLACE FUNCTION catalog.locale_id(p_pk INTEGER)
RETURNS UUID
LANGUAGE sql STABLE
AS $$
    SELECT id FROM catalog.tb_locale
    WHERE pk_locale = p_pk;
$$;

COMMENT ON FUNCTION catalog.locale_id(INTEGER) IS
'Trinity Pattern: Convert internal INTEGER primary key to external UUID identifier.';