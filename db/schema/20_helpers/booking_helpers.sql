


-- ============================================================================
-- Trinity Helper: public.booking_pk()
-- ============================================================================
-- Converts between UUID and INTEGER representations
-- ============================================================================

-- UUID/identifier/text → INTEGER (pk)
CREATE OR REPLACE FUNCTION public.booking_pk(p_identifier TEXT)
RETURNS INTEGER
LANGUAGE sql STABLE
AS $$
    SELECT pk_booking
    FROM public.tb_booking
    WHERE (id::TEXT = p_identifier
        OR pk_booking::TEXT = p_identifier)
    LIMIT 1;
$$;

COMMENT ON FUNCTION public.booking_pk(TEXT, UUID) IS
'Trinity Pattern: Resolve entity identifier to internal INTEGER primary key.
Accepts UUID, text identifier, or integer pk and returns pk_booking.';




-- ============================================================================
-- Trinity Helper: public.booking_id()
-- ============================================================================
-- Converts between UUID and INTEGER representations
-- ============================================================================

-- INTEGER (pk) → UUID
CREATE OR REPLACE FUNCTION public.booking_id(p_pk INTEGER)
RETURNS UUID
LANGUAGE sql STABLE
AS $$
    SELECT id FROM public.tb_booking
    WHERE pk_booking = p_pk;
$$;

COMMENT ON FUNCTION public.booking_id(INTEGER) IS
'Trinity Pattern: Convert internal INTEGER primary key to external UUID identifier.';