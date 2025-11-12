"""
Tests for Heuristic Enhancer

Tests pattern detection and variable purpose inference
"""

from src.reverse_engineering.heuristic_enhancer import HeuristicEnhancer
from src.reverse_engineering.algorithmic_parser import AlgorithmicParser


def test_variable_purpose_inference():
    """Test variable purpose inference"""

    sql = """
    CREATE OR REPLACE FUNCTION sales.calculate_total(p_order_id UUID)
    RETURNS NUMERIC AS $$
    DECLARE
        v_total NUMERIC := 0;
        v_count INTEGER := 0;
        v_is_valid BOOLEAN := TRUE;
    BEGIN
        SELECT SUM(amount), COUNT(*)
        INTO v_total, v_count
        FROM tb_order_line
        WHERE order_id = p_order_id;

        IF v_count > 0 THEN
            RETURN v_total;
        ELSE
            RETURN 0;
        END IF;
    END;
    $$ LANGUAGE plpgsql;
    """

    parser = AlgorithmicParser()
    result = parser.parse(sql)

    enhancer = HeuristicEnhancer()
    enhanced_result = enhancer.enhance(result)

    # Check variable purposes were inferred
    assert 'variable_purposes' in enhanced_result.metadata
    purposes = enhanced_result.metadata['variable_purposes']

    assert 'v_total' in purposes
    assert purposes['v_total'] == 'total'

    assert 'v_count' in purposes
    assert purposes['v_count'] == 'count'

    assert 'v_is_valid' in purposes
    assert purposes['v_is_valid'] == 'flag'

    # Confidence should be improved
    assert enhanced_result.confidence > result.confidence


def test_state_machine_pattern_detection():
    """Test detection of state machine pattern"""

    sql = """
    CREATE OR REPLACE FUNCTION orders.update_status(p_order_id UUID, p_new_status TEXT)
    RETURNS VOID AS $$
    DECLARE
        v_current_status TEXT;
        v_can_transition BOOLEAN := FALSE;
    BEGIN
        -- Get current status
        SELECT status INTO v_current_status
        FROM tb_order
        WHERE id = p_order_id;

        -- Check if transition is valid
        IF v_current_status = 'pending' AND p_new_status = 'confirmed' THEN
            v_can_transition := TRUE;
        ELSIF v_current_status = 'confirmed' AND p_new_status = 'shipped' THEN
            v_can_transition := TRUE;
        END IF;

        IF v_can_transition THEN
            UPDATE tb_order
            SET status = p_new_status,
                updated_at = NOW()
            WHERE id = p_order_id;
        END IF;
    END;
    $$ LANGUAGE plpgsql;
    """

    parser = AlgorithmicParser()
    result = parser.parse(sql)

    enhancer = HeuristicEnhancer()
    enhanced_result = enhancer.enhance(result)

    # Should detect state machine pattern
    assert 'detected_patterns' in enhanced_result.metadata
    patterns = enhanced_result.metadata['detected_patterns']
    assert 'state_machine' in patterns


def test_audit_trail_pattern_detection():
    """Test detection of audit trail pattern"""

    sql = """
    CREATE OR REPLACE FUNCTION users.update_profile(p_user_id UUID, p_name TEXT)
    RETURNS VOID AS $$
    BEGIN
        -- Insert audit record
        INSERT INTO audit_log (user_id, action, old_value, new_value, changed_by, changed_at)
        SELECT p_user_id, 'update_name', name, p_name, p_user_id, NOW()
        FROM users
        WHERE id = p_user_id;

        -- Update the record
        UPDATE users
        SET name = p_name,
            updated_at = NOW(),
            updated_by = p_user_id
        WHERE id = p_user_id;
    END;
    $$ LANGUAGE plpgsql;
    """

    parser = AlgorithmicParser()
    result = parser.parse(sql)

    enhancer = HeuristicEnhancer()
    enhanced_result = enhancer.enhance(result)

    # Should detect audit trail pattern
    assert 'detected_patterns' in enhanced_result.metadata
    patterns = enhanced_result.metadata['detected_patterns']
    assert 'audit_trail' in patterns


def test_soft_delete_pattern_detection():
    """Test detection of soft delete pattern"""

    sql = """
    CREATE OR REPLACE FUNCTION products.delete_product(p_product_id UUID)
    RETURNS VOID AS $$
    BEGIN
        UPDATE products
        SET deleted_at = NOW(),
            deleted_by = current_user_id(),
            is_active = FALSE
        WHERE id = p_product_id;
    END;
    $$ LANGUAGE plpgsql;
    """

    parser = AlgorithmicParser()
    result = parser.parse(sql)

    enhancer = HeuristicEnhancer()
    enhanced_result = enhancer.enhance(result)

    # Should detect soft delete pattern
    assert 'detected_patterns' in enhanced_result.metadata
    patterns = enhanced_result.metadata['detected_patterns']
    assert 'soft_delete' in patterns


def test_validation_chain_pattern_detection():
    """Test detection of validation chain pattern"""

    sql = """
    CREATE OR REPLACE FUNCTION orders.place_order(p_customer_id UUID, p_product_id UUID, p_quantity INTEGER)
    RETURNS UUID AS $$
    DECLARE
        v_customer_exists BOOLEAN;
        v_product_available BOOLEAN;
        v_sufficient_stock BOOLEAN;
        v_order_id UUID;
    BEGIN
        -- Validate customer exists
        SELECT EXISTS(SELECT 1 FROM customers WHERE id = p_customer_id)
        INTO v_customer_exists;

        IF NOT v_customer_exists THEN
            RAISE EXCEPTION 'Customer does not exist';
        END IF;

        -- Validate product exists and is active
        SELECT EXISTS(SELECT 1 FROM products WHERE id = p_product_id AND is_active = TRUE)
        INTO v_product_available;

        IF NOT v_product_available THEN
            RAISE EXCEPTION 'Product not available';
        END IF;

        -- Validate sufficient stock
        SELECT stock_quantity >= p_quantity
        INTO v_sufficient_stock
        FROM products
        WHERE id = p_product_id;

        IF NOT v_sufficient_stock THEN
            RAISE EXCEPTION 'Insufficient stock';
        END IF;

        -- Create order
        INSERT INTO orders (customer_id, product_id, quantity, status)
        VALUES (p_customer_id, p_product_id, p_quantity, 'pending')
        RETURNING id INTO v_order_id;

        RETURN v_order_id;
    END;
    $$ LANGUAGE plpgsql;
    """

    parser = AlgorithmicParser()
    result = parser.parse(sql)

    enhancer = HeuristicEnhancer()
    enhanced_result = enhancer.enhance(result)

    # Should detect validation chain pattern
    assert 'detected_patterns' in enhanced_result.metadata
    patterns = enhanced_result.metadata['detected_patterns']
    assert 'validation_chain' in patterns


def test_naming_improvements():
    """Test variable naming improvements"""

    sql = """
    CREATE OR REPLACE FUNCTION test.function(p_param UUID)
    RETURNS INTEGER AS $$
    DECLARE
        v_total_amount INTEGER := 0;
        v_item_count INTEGER := 0;
    BEGIN
        SELECT SUM(amount), COUNT(*)
        INTO v_total_amount, v_item_count
        FROM items
        WHERE parent_id = p_param;

        RETURN v_total_amount;
    END;
    $$ LANGUAGE plpgsql;
    """

    parser = AlgorithmicParser()
    result = parser.parse(sql)

    enhancer = HeuristicEnhancer()
    enhanced_result = enhancer.enhance(result)

    # Check that confidence improved
    assert enhanced_result.confidence >= result.confidence

    # Check that patterns were detected
    assert 'detected_patterns' in enhanced_result.metadata or 'variable_purposes' in enhanced_result.metadata


def test_confidence_improvement():
    """Test that heuristic enhancer improves confidence"""

    sql = """
    CREATE OR REPLACE FUNCTION simple.test()
    RETURNS TEXT AS $$
    BEGIN
        RETURN 'hello';
    END;
    $$ LANGUAGE plpgsql;
    """

    parser = AlgorithmicParser()
    result = parser.parse(sql)

    initial_confidence = result.confidence

    enhancer = HeuristicEnhancer()
    enhanced_result = enhancer.enhance(result)

    # Confidence should not decrease
    assert enhanced_result.confidence >= initial_confidence

    # For simple functions with no patterns, confidence stays the same or improves slightly
    # The cap only applies when there are actual improvements to make