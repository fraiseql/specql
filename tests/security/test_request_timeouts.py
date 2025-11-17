# tests/security/test_request_timeouts.py
import pytest
from unittest.mock import patch, MagicMock


def test_llm_recommendations_has_timeout():
    """Ensure all HTTP requests have timeouts to prevent DoS"""
    # This should FAIL initially
    from src.cicd.llm_recommendations import LLMRecommendations

    with patch("requests.post") as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "choices": [{"message": {"content": '{"test": "response"}'}}]
            },
        )

        llm = LLMRecommendations(api_key="test_key")
        # Call a method that makes HTTP requests
        try:
            llm._call_llm("test prompt")
        except:
            pass  # We just want to check if timeout was used

        # Verify timeout was set
        call_kwargs = mock_post.call_args[1]
        assert "timeout" in call_kwargs, "Request must have timeout"
        assert call_kwargs["timeout"] > 0, "Timeout must be positive"


def test_cdc_status_has_timeout():
    """Ensure CDC status requests have timeouts"""
    # Test that the timeout is properly configured in the code
    # We can't easily test the click command, so we'll verify the code has timeout
    with open("src/cli/cdc.py") as f:
        content = f.read()
        assert "timeout=DEFAULT_REQUEST_TIMEOUT" in content, (
            "CDC status request should have timeout"
        )
