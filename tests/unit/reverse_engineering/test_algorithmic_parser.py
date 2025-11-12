"""
Tests for Algorithmic Parser

Tests SQL → SpecQL conversion without AI
"""

from src.reverse_engineering.algorithmic_parser import AlgorithmicParser


def test_parse_simple_function():
    """Test parsing simple SQL function to SpecQL"""

    sql = """
    CREATE OR REPLACE FUNCTION crm.calculate_total(p_order_id UUID)
    RETURNS NUMERIC AS $$
    DECLARE
        v_total NUMERIC := 0;
    BEGIN
        SELECT SUM(amount) INTO v_total
        FROM tb_order_line
        WHERE order_id = p_order_id;

        RETURN v_total;
    END;
    $$ LANGUAGE plpgsql;
    """

    parser = AlgorithmicParser()
    result = parser.parse(sql)

    assert result is not None
    assert result.function_name == "calculate_total"
    assert result.schema == "crm"
    assert len(result.parameters) == 1
    assert result.parameters[0]["name"] == "order_id"
    assert result.parameters[0]["type"] == "uuid"
    assert result.return_type == "numeric"

    assert len(result.steps) == 3
    assert result.steps[0].type == "declare"
    assert result.steps[1].type == "query"
    assert result.steps[2].type == "return"

    assert result.confidence >= 0.85


def test_parse_function_with_cte():
    """Test parsing function with CTE"""

    sql = """
    CREATE OR REPLACE FUNCTION sales.monthly_report(p_year INTEGER)
    RETURNS TABLE(month DATE, total NUMERIC) AS $$
    BEGIN
        RETURN QUERY
        WITH monthly_totals AS (
            SELECT
                DATE_TRUNC('month', order_date) AS month,
                SUM(total_amount) AS total
            FROM tb_order
            WHERE EXTRACT(YEAR FROM order_date) = p_year
            GROUP BY DATE_TRUNC('month', order_date)
        )
        SELECT * FROM monthly_totals ORDER BY month;
    END;
    $$ LANGUAGE plpgsql;
    """

    parser = AlgorithmicParser()
    result = parser.parse(sql)

    assert result.function_name == "monthly_report"
    assert len(result.steps) == 1  # Algorithmic parser treats RETURN QUERY as one step
    assert result.steps[0].type == "return_table"
    assert "monthly_totals" in result.steps[0].return_table_query


def test_parse_function_with_if():
    """Test parsing function with conditional logic"""

    sql = """
    CREATE OR REPLACE FUNCTION check_inventory(p_product_id UUID, p_quantity INTEGER)
    RETURNS BOOLEAN AS $$
    DECLARE
        v_available INTEGER;
    BEGIN
        SELECT stock_quantity INTO v_available
        FROM tb_product
        WHERE id = p_product_id;

        IF v_available >= p_quantity THEN
            RETURN TRUE;
        ELSE
            RETURN FALSE;
        END IF;
    END;
    $$ LANGUAGE plpgsql;
    """

    parser = AlgorithmicParser()
    result = parser.parse(sql)

    # Find the IF step
    if_step = None
    for step in result.steps:
        if step.type == "if":
            if_step = step
            break
    assert if_step is not None
    assert if_step.condition == "available >= quantity"
    # Algorithmic parser doesn't parse THEN/ELSE blocks in detail
    assert len(if_step.then_steps) == 0
    assert len(if_step.else_steps) == 0


def test_parse_to_yaml():
    """Test conversion to YAML format"""

    sql = """
    CREATE OR REPLACE FUNCTION test.simple_func(p_id INTEGER)
    RETURNS TEXT AS $$
    BEGIN
        RETURN 'test';
    END;
    $$ LANGUAGE plpgsql;
    """

    parser = AlgorithmicParser()
    yaml_output = parser.parse_to_yaml(sql)

    assert "entity: SimpleFunc" in yaml_output
    assert "name: simple_func" in yaml_output
    assert "returns: text" in yaml_output
    assert "generated_by: algorithmic_parser" in yaml_output


def test_confidence_scoring():
    """Test that confidence scores are reasonable"""

    # Simple function should have high confidence
    simple_sql = """
    CREATE OR REPLACE FUNCTION test.simple() RETURNS INTEGER AS $$
    BEGIN RETURN 42; END;
    $$ LANGUAGE plpgsql;
    """

    parser = AlgorithmicParser()
    result = parser.parse(simple_sql)

    assert result.confidence >= 0.8

    # Complex function might have lower confidence
    complex_sql = """
    CREATE OR REPLACE FUNCTION test.complex() RETURNS INTEGER AS $$
    DECLARE
        v_unknown_var UNKNOWN_TYPE;
    BEGIN
        -- Some unknown syntax
        PERFORM unknown_operation();
        RETURN 42;
    END;
    $$ LANGUAGE plpgsql;
    """

    result = parser.parse(complex_sql)
    # Should still have some confidence but lower due to warnings
    assert result.confidence < 1.0
    assert len(result.warnings) > 0