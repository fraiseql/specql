


-- ============================================================================
-- Trinity Helper: sales.order_pk()
-- ============================================================================
-- Converts between UUID and INTEGER representations
-- ============================================================================

-- UUID/identifier/text → INTEGER (pk)
CREATE OR REPLACE FUNCTION sales.order_pk(p_identifier TEXT)
RETURNS INTEGER
LANGUAGE sql STABLE
AS $$
    SELECT pk_order
    FROM sales.tb_order
    WHERE (id::TEXT = p_identifier
        OR pk_order::TEXT = p_identifier)
    LIMIT 1;
$$;

COMMENT ON FUNCTION sales.order_pk(TEXT, UUID) IS
'Trinity Pattern: Resolve entity identifier to internal INTEGER primary key.
Accepts UUID, text identifier, or integer pk and returns pk_order.';




-- ============================================================================
-- Trinity Helper: sales.order_id()
-- ============================================================================
-- Converts between UUID and INTEGER representations
-- ============================================================================

-- INTEGER (pk) → UUID
CREATE OR REPLACE FUNCTION sales.order_id(p_pk INTEGER)
RETURNS UUID
LANGUAGE sql STABLE
AS $$
    SELECT id FROM sales.tb_order
    WHERE pk_order = p_pk;
$$;

COMMENT ON FUNCTION sales.order_id(INTEGER) IS
'Trinity Pattern: Convert internal INTEGER primary key to external UUID identifier.';