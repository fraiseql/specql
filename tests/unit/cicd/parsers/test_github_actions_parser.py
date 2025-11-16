"""Tests for GitHub Actions → Universal Pipeline parser"""

import pytest
from src.cicd.parsers.github_actions_parser import GitHubActionsParser
from src.cicd.universal_pipeline_schema import TriggerType, StepType


class TestGitHubActionsParser:
    """Test parsing GitHub Actions YAML to universal format"""

    @pytest.fixture
    def parser(self):
        return GitHubActionsParser()

    def test_parse_simple_workflow(self, parser):
        """Test parsing basic GitHub Actions workflow"""
        yaml_content = """name: CI
"on":
  push:
    branches:
      - main
  pull_request:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -e .[dev]
      - name: Run tests
        run: pytest
"""

        # Act
        pipeline = parser.parse(yaml_content)

        # Assert
        assert pipeline.name == "CI"
        assert len(pipeline.triggers) == 2
        assert pipeline.triggers[0].type == TriggerType.PUSH
        assert pipeline.triggers[0].branches == ["main"]
        assert pipeline.triggers[1].type == TriggerType.PULL_REQUEST

        assert len(pipeline.stages) == 1
        assert pipeline.stages[0].name == "default"

        job = pipeline.stages[0].jobs[0]
        assert job.name == "test"
        assert len(job.steps) == 4

        # Check steps
        assert job.steps[0].type == StepType.CHECKOUT
        assert job.steps[1].type == StepType.SETUP_RUNTIME
        assert job.steps[2].type == StepType.INSTALL_DEPS
        assert job.steps[3].type == StepType.RUN_TESTS

    def test_parse_with_services(self, parser):
        """Test parsing workflow with services"""
        yaml_content = """name: Integration Tests
"on":
  push:
jobs:
  test:
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
    steps:
      - run: pytest tests/integration
"""

        # Act
        pipeline = parser.parse(yaml_content)

        # Assert
        job = pipeline.stages[0].jobs[0]
        assert len(job.services) == 1
        assert job.services[0].name == "postgres"
        assert job.services[0].version == "15"
        assert job.services[0].environment["POSTGRES_PASSWORD"] == "test"

    def test_parse_with_matrix(self, parser):
        """Test parsing matrix builds"""
        yaml_content = """name: Matrix Build
"on":
  push:
jobs:
  test:
    strategy:
      matrix:
        python: ['3.10', '3.11', '3.12']
        os: [ubuntu-latest, macos-latest]
    steps:
      - run: pytest
"""

        # Act
        pipeline = parser.parse(yaml_content)

        # Assert
        job = pipeline.stages[0].jobs[0]
        assert job.matrix is not None
        assert job.matrix["python"] == ["3.10", "3.11", "3.12"]
        assert job.matrix["os"] == ["ubuntu-latest", "macos-latest"]
