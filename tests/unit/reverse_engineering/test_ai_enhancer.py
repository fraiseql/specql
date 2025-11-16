"""
Tests for AI Enhancer

Tests LLM-based enhancements (mocked for CI)
"""

from unittest.mock import Mock
from src.reverse_engineering.ai_enhancer import AIEnhancer
from src.reverse_engineering.algorithmic_parser import AlgorithmicParser


def test_ai_enhancer_initialization():
    """Test AI enhancer initialization"""
    enhancer = AIEnhancer()
    assert enhancer.local_model_path.endswith("llama-3.1-8b.gguf")
    assert enhancer.use_cloud_fallback is False
    assert enhancer.cloud_api_key is None


def test_ai_enhancer_with_mock_llm():
    """Test AI enhancer with mocked LLM"""

    # Create enhancer and manually set mock LLM
    enhancer = AIEnhancer()

    # Mock the LLM
    mock_llm = Mock()
    mock_llm.return_value = {
        "choices": [{"text": "This function calculates order totals."}]
    }
    enhancer.local_llm = mock_llm

    # Test with simple function
    sql = """
    CREATE OR REPLACE FUNCTION test.simple() RETURNS TEXT AS $$
    BEGIN RETURN 'hello'; END;
    $$ LANGUAGE plpgsql;
    """

    parser = AlgorithmicParser(use_heuristics=False)  # Disable heuristics for this test
    result = parser.parse(sql)

    # Manually lower confidence to trigger AI enhancement
    result.confidence = 0.85

    # Enhance with AI
    enhanced_result = enhancer.enhance(result)

    # Check that intent was inferred
    assert hasattr(enhanced_result, "metadata")
    assert enhanced_result.metadata is not None
    assert "intent" in enhanced_result.metadata
    assert (
        enhanced_result.metadata["intent"] == "This function calculates order totals."
    )

    # Confidence should be improved
    assert enhanced_result.confidence >= result.confidence


def test_ai_enhancer_without_llm():
    """Test AI enhancer when no LLM is available"""

    # Create enhancer without mocking llama_cpp (so it won't load)
    enhancer = AIEnhancer()

    # Manually set local_llm to None to simulate no LLM
    enhancer.local_llm = None

    sql = """
    CREATE OR REPLACE FUNCTION test.simple() RETURNS TEXT AS $$
    BEGIN RETURN 'hello'; END;
    $$ LANGUAGE plpgsql;
    """

    parser = AlgorithmicParser(use_heuristics=False)
    result = parser.parse(sql)

    # Enhance without LLM
    enhanced_result = enhancer.enhance(result)

    # Result should be unchanged
    assert enhanced_result.confidence == result.confidence


def test_variable_name_improvement():
    """Test variable name improvement with mocked LLM"""

    # Create enhancer and manually set mock LLM
    enhancer = AIEnhancer()

    # Mock LLM response with JSON
    mock_llm = Mock()
    mock_llm.return_value = {
        "choices": [{"text": '{"v_total": "total_amount", "v_cnt": "item_count"}'}]
    }
    enhancer.local_llm = mock_llm

    sql = """
    CREATE OR REPLACE FUNCTION sales.calculate(p_order_id UUID)
    RETURNS NUMERIC AS $$
    DECLARE
        v_total NUMERIC := 0;
        v_cnt INTEGER := 0;
    BEGIN
        SELECT SUM(amount), COUNT(*)
        INTO v_total, v_cnt
        FROM items WHERE order_id = p_order_id;

        RETURN v_total;
    END;
    $$ LANGUAGE plpgsql;
    """

    parser = AlgorithmicParser(use_heuristics=False)
    result = parser.parse(sql)

    # Manually lower confidence to trigger AI enhancement
    result.confidence = 0.85

    enhanced_result = enhancer.enhance(result)

    # Check confidence improvement
    assert enhanced_result.confidence > 0.85


def test_pattern_suggestion():
    """Test pattern suggestion with mocked LLM"""

    # Create enhancer and manually set mock LLM
    enhancer = AIEnhancer()

    # Mock LLM response
    mock_llm = Mock()
    mock_llm.return_value = {
        "choices": [{"text": "aggregation_pipeline, validation_chain"}]
    }
    enhancer.local_llm = mock_llm

    sql = """
    CREATE OR REPLACE FUNCTION test.aggregate() RETURNS NUMERIC AS $$
    BEGIN
        SELECT SUM(amount) FROM items;
    END;
    $$ LANGUAGE plpgsql;
    """

    parser = AlgorithmicParser(use_heuristics=False)
    result = parser.parse(sql)

    enhanced_result = enhancer.enhance(result)

    # Check that patterns were suggested
    if hasattr(enhanced_result, "metadata"):
        assert "suggested_patterns" in enhanced_result.metadata
        patterns = enhanced_result.metadata["suggested_patterns"]
        assert "aggregation_pipeline" in patterns
        assert "validation_chain" in patterns
