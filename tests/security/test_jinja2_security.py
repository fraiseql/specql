# tests/security/test_jinja2_security.py
import pytest
from jinja2 import Environment


def test_action_compiler_has_autoescape_enabled():
    """Ensure Jinja2 templates have autoescape to prevent XSS"""
    from src.generators.actions.action_compiler import ActionCompiler

    compiler = ActionCompiler()
    # Access the internal Jinja2 environment
    assert hasattr(compiler, "env"), "Compiler should have Jinja2 environment"
    # When using select_autoescape, autoescape is a function, not a boolean
    assert callable(compiler.env.autoescape), (
        "Autoescape should be a function when using select_autoescape"
    )


def test_xss_prevention_in_template_rendering():
    """Verify Jinja2 templates escape malicious input"""
    # This test should FAIL initially
    from src.generators.actions.action_compiler import ActionCompiler

    compiler = ActionCompiler()
    # Create a simple template with user input
    template = compiler.env.from_string("SELECT '{{ user_input }}' FROM users;")
    test_input = "<script>alert('xss')</script>"

    # Render with malicious input
    result = template.render(user_input=test_input)

    # Should be escaped if autoescape is enabled
    assert "&lt;script&gt;" in result or test_input not in result
