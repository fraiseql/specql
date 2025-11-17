# tests/type_checking/test_annotations.py
import ast
import pytest


def test_sql_ast_parser_has_parameter_annotation():
    """Verify parameters variable has type annotation"""
    with open("src/reverse_engineering/sql_ast_parser.py") as f:
        tree = ast.parse(f.read())

    # Find the assignment to 'parameters'
    found_annotation = False
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "parameters"
        ):
            found_annotation = True
            break

    assert found_annotation, "parameters must have type annotation"


def test_python_to_specql_mapper_has_list_annotations():
    """Verify list variables have type annotations"""
    with open("src/reverse_engineering/python_to_specql_mapper.py") as f:
        tree = ast.parse(f.read())

    # Check for then_steps, else_steps, body_steps
    required_vars = ["then_steps", "else_steps", "body_steps"]
    found_annotations = {var: False for var in required_vars}

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id in required_vars
        ):
            found_annotations[node.target.id] = True

    for var, found in found_annotations.items():
        assert found, f"{var} must have type annotation"


def test_ast_to_specql_mapper_has_steps_annotation():
    """Verify steps variable has type annotation"""
    with open("src/reverse_engineering/ast_to_specql_mapper.py") as f:
        tree = ast.parse(f.read())

    # Find the assignment to 'steps'
    found_annotation = False
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "steps"
        ):
            found_annotation = True
            break

    assert found_annotation, "steps must have type annotation"


def test_return_optimizer_has_unreachable_annotation():
    """Verify unreachable variable has type annotation"""
    with open("src/generators/actions/return_optimizer.py") as f:
        tree = ast.parse(f.read())

    # Find the assignment to 'unreachable'
    found_annotation = False
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "unreachable"
        ):
            found_annotation = True
            break

    assert found_annotation, "unreachable must have type annotation"


def test_java_parser_has_java_files_annotation():
    """Verify java_files variable has type annotation"""
    with open("src/reverse_engineering/java/java_parser.py") as f:
        tree = ast.parse(f.read())

    # Find the assignment to 'java_files'
    found_annotation = False
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "java_files"
        ):
            found_annotation = True
            break

    assert found_annotation, "java_files must have type annotation"


def test_jenkins_parser_has_env_vars_annotation():
    """Verify env_vars variable has type annotation"""
    with open("src/cicd/parsers/jenkins_parser.py") as f:
        tree = ast.parse(f.read())

    # Find the assignment to 'env_vars'
    found_annotation = False
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "env_vars"
        ):
            found_annotation = True
            break

    assert found_annotation, "env_vars must have type annotation"


def test_group_leader_detector_has_groups_annotation():
    """Verify groups variable has type annotation"""
    with open("src/testing/metadata/group_leader_detector.py") as f:
        tree = ast.parse(f.read())

    # Find the assignment to 'groups'
    found_annotation = False
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "groups"
        ):
            found_annotation = True
            break

    assert found_annotation, "groups must have type annotation"


def test_serverless_runner_has_config_annotation():
    """Verify config variable has type annotation"""
    with open("src/runners/serverless_runner.py") as f:
        tree = ast.parse(f.read())

    # Find the assignment to 'config'
    found_annotation = False
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "config"
        ):
            found_annotation = True
            break

    assert found_annotation, "config must have type annotation"


def test_table_view_dependency_has_graph_annotations():
    """Verify graph and reverse_graph variables have type annotations"""
    with open("src/generators/schema/table_view_dependency.py") as f:
        tree = ast.parse(f.read())

    # Check for graph and reverse_graph
    required_vars = ["graph", "reverse_graph"]
    found_annotations = {var: False for var in required_vars}

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id in required_vars
        ):
            found_annotations[node.target.id] = True

    for var, found in found_annotations.items():
        assert found, f"{var} must have type annotation"


def test_conditional_compiler_has_cases_annotation():
    """Verify cases variable has type annotation"""
    with open("src/generators/actions/conditional_compiler.py") as f:
        tree = ast.parse(f.read())

    # Find the assignment to 'cases'
    found_annotation = False
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "cases"
        ):
            found_annotation = True
            break

    assert found_annotation, "cases must have type annotation"


def test_rich_type_handler_has_base_fields_annotation():
    """Verify base_fields variable has type annotation"""
    with open("src/generators/actions/step_compilers/rich_type_handler.py") as f:
        tree = ast.parse(f.read())

    # Find the assignment to 'base_fields'
    found_annotation = False
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "base_fields"
        ):
            found_annotation = True
            break

    assert found_annotation, "base_fields must have type annotation"
