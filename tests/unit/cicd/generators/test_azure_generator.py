"""Tests for Universal → Azure DevOps generator"""

import pytest
from src.cicd.generators.azure_generator import AzureGenerator
from src.cicd.universal_pipeline_schema import *


class TestAzureGenerator:
    """Test generating Azure DevOps azure-pipelines.yml from universal format"""

    @pytest.fixture
    def generator(self):
        return AzureGenerator()

    def test_generate_simple_pipeline(self, generator):
        """Test generating basic Azure DevOps pipeline"""
        pipeline = UniversalPipeline(
            name="build_and_test",
            triggers=[
                Trigger(type=TriggerType.PUSH, branches=["main", "develop"])
            ],
            stages=[
                Stage(
                    name="Build",
                    jobs=[
                        Job(
                            name="build",
                            runtime=Runtime(language="python", version="3.11"),
                            steps=[
                                Step(name="Checkout", type=StepType.CHECKOUT),
                                Step(name="Install deps", type=StepType.INSTALL_DEPS, command="pip install -r requirements.txt"),
                                Step(name="Run tests", type=StepType.RUN_TESTS, command="pytest")
                            ]
                        )
                    ]
                ),
                Stage(
                    name="Test",
                    jobs=[
                        Job(
                            name="test",
                            runtime=Runtime(language="python", version="3.11"),
                            steps=[
                                Step(name="Run tests", type=StepType.RUN_TESTS, command="pytest")
                            ]
                        )
                    ]
                )
            ]
        )

        # Act
        yaml_output = generator.generate(pipeline)

        # Assert
        assert "trigger:" in yaml_output
        assert "- main" in yaml_output
        assert "- develop" in yaml_output
        assert "stages:" in yaml_output
        assert "stage: Build" in yaml_output
        assert "stage: Test" in yaml_output
        assert "job: build" in yaml_output
        assert "job: test" in yaml_output
        assert "pool:" in yaml_output
        assert "vmImage: ubuntu-latest" in yaml_output
        assert "- checkout: self" in yaml_output
        assert "script: pip install -r requirements.txt" in yaml_output
        assert "script: pytest" in yaml_output

    def test_generate_with_schedule_trigger(self, generator):
        """Test generating pipeline with schedule triggers"""
        pipeline = UniversalPipeline(
            name="nightly_build",
            triggers=[
                Trigger(type=TriggerType.SCHEDULE, schedule="0 2 * * *", branches=["main"])
            ],
            stages=[
                Stage(
                    name="Test",
                    jobs=[
                        Job(
                            name="test",
                            runtime=Runtime(language="python", version="3.11"),
                            steps=[
                                Step(name="Run tests", type=StepType.RUN_TESTS, command="pytest")
                            ]
                        )
                    ]
                )
            ]
        )

        # Act
        yaml_output = generator.generate(pipeline)

        # Assert
        assert "schedules:" in yaml_output
        assert "cron: \"0 2 * * *\"" in yaml_output
        assert "displayName: Scheduled build" in yaml_output
        assert "branches:" in yaml_output
        assert "include:" in yaml_output
        assert "- main" in yaml_output

    def test_generate_with_environment_variables(self, generator):
        """Test generating pipeline with environment variables"""
        pipeline = UniversalPipeline(
            name="env_test",
            global_environment={
                "ENV": "production",
                "DEBUG": "false"
            },
            stages=[
                Stage(
                    name="Deploy",
                    jobs=[
                        Job(
                            name="deploy",
                            environment={
                                "DEPLOY_ENV": "prod",
                                "API_KEY": "$(secret-api-key)"
                            },
                            steps=[
                                Step(name="Deploy", type=StepType.DEPLOY, command="echo Deploying to production")
                            ]
                        )
                    ]
                )
            ]
        )

        # Act
        yaml_output = generator.generate(pipeline)

        # Assert
        assert "variables:" in yaml_output
        assert "ENV: production" in yaml_output
        assert "DEBUG: false" in yaml_output
        assert "variables:" in yaml_output  # Job-level variables
        assert "DEPLOY_ENV: prod" in yaml_output
        assert "API_KEY: $(secret-api-key)" in yaml_output