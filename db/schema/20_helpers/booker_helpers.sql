


-- ============================================================================
-- Trinity Helper: public.booker_pk()
-- ============================================================================
-- Converts between UUID and INTEGER representations
-- ============================================================================

-- UUID/identifier/text → INTEGER (pk)
CREATE OR REPLACE FUNCTION public.booker_pk(p_identifier TEXT)
RETURNS INTEGER
LANGUAGE sql STABLE
AS $$
    SELECT pk_booker
    FROM public.tb_booker
    WHERE (id::TEXT = p_identifier
        OR pk_booker::TEXT = p_identifier)
    LIMIT 1;
$$;

COMMENT ON FUNCTION public.booker_pk(TEXT, UUID) IS
'Trinity Pattern: Resolve entity identifier to internal INTEGER primary key.
Accepts UUID, text identifier, or integer pk and returns pk_booker.';




-- ============================================================================
-- Trinity Helper: public.booker_id()
-- ============================================================================
-- Converts between UUID and INTEGER representations
-- ============================================================================

-- INTEGER (pk) → UUID
CREATE OR REPLACE FUNCTION public.booker_id(p_pk INTEGER)
RETURNS UUID
LANGUAGE sql STABLE
AS $$
    SELECT id FROM public.tb_booker
    WHERE pk_booker = p_pk;
$$;

COMMENT ON FUNCTION public.booker_id(INTEGER) IS
'Trinity Pattern: Convert internal INTEGER primary key to external UUID identifier.';