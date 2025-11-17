"""
Test all 6 patterns working together
"""

import pytest
from src.reverse_engineering.universal_pattern_detector import UniversalPatternDetector


class TestAllPatternsCombined:
    """Test detecting multiple patterns in same codebase"""

    @pytest.fixture
    def detector(self):
        return UniversalPatternDetector()

    def test_complex_sql_with_4_patterns(self, detector):
        """Test SQL with State Machine + Soft Delete + Audit + Multi-Tenant"""
        sql_code = """
CREATE TABLE tb_order (
    pk_order INTEGER PRIMARY KEY,
    tenant_id UUID NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    total NUMERIC NOT NULL,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by UUID NOT NULL,
    FOREIGN KEY (tenant_id) REFERENCES tb_tenant(pk_tenant)
);

-- Multi-tenant isolation
ALTER TABLE tb_order ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_orders ON tb_order
    USING (tenant_id = current_setting('app.current_tenant')::UUID);

-- State machine transitions
CREATE FUNCTION ship_order(p_order_id INT) AS $$
BEGIN
    IF (SELECT status FROM tb_order WHERE pk_order = p_order_id) != 'pending' THEN
        RAISE EXCEPTION 'Must be pending to ship';
    END IF;
    UPDATE tb_order SET status = 'shipped', updated_at = NOW() WHERE pk_order = p_order_id;
END;
$$ LANGUAGE plpgsql;

CREATE FUNCTION cancel_order(p_order_id INT) AS $$
BEGIN
    UPDATE tb_order SET status = 'cancelled', updated_at = NOW() WHERE pk_order = p_order_id;
END;
$$ LANGUAGE plpgsql;

CREATE FUNCTION deliver_order(p_order_id INT) AS $$
BEGIN
    IF (SELECT status FROM tb_order WHERE pk_order = p_order_id) != 'shipped' THEN
        RAISE EXCEPTION 'Must be shipped to deliver';
    END IF;
    UPDATE tb_order SET status = 'delivered', updated_at = NOW() WHERE pk_order = p_order_id;
END;
$$ LANGUAGE plpgsql;

-- Soft delete
CREATE FUNCTION delete_order(p_order_id INT) AS $$
BEGIN
    UPDATE tb_order SET deleted_at = NOW() WHERE pk_order = p_order_id;
END;
$$ LANGUAGE plpgsql;
        """

        patterns = detector.detect(sql_code, language="sql")

        # Should detect 4 patterns
        pattern_names = [p.name for p in patterns]
        assert "state_machine" in pattern_names  # Engineer A
        assert "soft_delete" in pattern_names  # Engineer A
        assert "audit_trail" in pattern_names  # Engineer A
        assert "multi_tenant" in pattern_names  # YOUR PATTERN

        # All should have high confidence
        for p in patterns:
            assert p.confidence >= 0.75, f"{p.name} confidence too low: {p.confidence}"
