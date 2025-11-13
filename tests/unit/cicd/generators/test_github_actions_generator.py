"""Tests for Universal → GitHub Actions generator"""

import pytest
from src.cicd.generators.github_actions_generator import GitHubActionsGenerator
from src.cicd.universal_pipeline_schema import *


class TestGitHubActionsGenerator:
    """Test generating GitHub Actions YAML from universal format"""

    @pytest.fixture
    def generator(self):
        return GitHubActionsGenerator()

    def test_generate_simple_workflow(self, generator):
        """Test generating basic workflow"""
        pipeline = UniversalPipeline(
            name="CI",
            triggers=[
                Trigger(type=TriggerType.PUSH, branches=["main"]),
                Trigger(type=TriggerType.PULL_REQUEST)
            ],
            stages=[
                Stage(
                    name="test",
                    jobs=[
                        Job(
                            name="test",
                            runtime=Runtime(language="python", version="3.11"),
                            steps=[
                                Step(name="Checkout", type=StepType.CHECKOUT),
                                Step(name="Setup", type=StepType.SETUP_RUNTIME),
                                Step(name="Test", type=StepType.RUN_TESTS, command="pytest")
                            ]
                        )
                    ]
                )
            ]
        )

        # Act
        yaml_output = generator.generate(pipeline)

        # Assert
        assert "name: CI" in yaml_output
        assert '"on":' in yaml_output
        assert "push:" in yaml_output
        assert "branches: [main]" in yaml_output
        assert "pull_request:" in yaml_output
        assert "jobs:" in yaml_output
        assert "runs-on: ubuntu-latest" in yaml_output
        assert "uses: actions/checkout@v4" in yaml_output
        assert "uses: actions/setup-python@v5" in yaml_output
        assert "run: pytest" in yaml_output