"""Tests for Universal → CircleCI generator"""

import pytest
from src.cicd.generators.circleci_generator import CircleCIGenerator
from src.cicd.universal_pipeline_schema import *


class TestCircleCIGenerator:
    """Test generating CircleCI config.yml from universal format"""

    @pytest.fixture
    def generator(self):
        return CircleCIGenerator()

    def test_generate_simple_workflow(self, generator):
        """Test generating basic CircleCI workflow"""
        pipeline = UniversalPipeline(
            name="build_and_test",
            triggers=[
                Trigger(type=TriggerType.PUSH, branches=["main"]),
                Trigger(type=TriggerType.PULL_REQUEST)
            ],
            stages=[
                Stage(
                    name="build_and_test",
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
                )
            ]
        )

        # Act
        yaml_output = generator.generate(pipeline)

        # Assert
        assert "version: 2.1" in yaml_output
        assert "workflows:" in yaml_output
        assert "build_and_test:" in yaml_output
        assert "jobs:" in yaml_output
        assert "- build" in yaml_output
        assert "docker:" in yaml_output
        assert "image: cimg/python:3.11" in yaml_output
        assert "- checkout" in yaml_output
        assert "command: pip install -r requirements.txt" in yaml_output
        assert "command: pytest" in yaml_output

    def test_generate_with_services(self, generator):
        """Test generating workflow with database services"""
        pipeline = UniversalPipeline(
            name="integration_tests",
            stages=[
                Stage(
                    name="test",
                    jobs=[
                        Job(
                            name="integration",
                            runtime=Runtime(language="python", version="3.11"),
                            services=[
                                Service(name="postgres", version="15", environment={"POSTGRES_PASSWORD": "test"}, ports=[5432])
                            ],
                            steps=[
                                Step(name="Checkout", type=StepType.CHECKOUT),
                                Step(name="Run integration tests", type=StepType.RUN_TESTS, command="pytest tests/integration")
                            ]
                        )
                    ]
                )
            ]
        )

        # Act
        yaml_output = generator.generate(pipeline)

        # Assert
        assert "docker:" in yaml_output
        assert "image: cimg/python:3.11" in yaml_output
        assert "image: postgres:15" in yaml_output
        assert "POSTGRES_PASSWORD: test" in yaml_output
        assert '"5432:5432"' in yaml_output

    def test_generate_with_matrix(self, generator):
        """Test generating matrix builds"""
        pipeline = UniversalPipeline(
            name="matrix_test",
            stages=[
                Stage(
                    name="test",
                    jobs=[
                        Job(
                            name="test",
                            runtime=Runtime(language="python", version="3.11"),
                            matrix={
                                "python-version": ["3.10", "3.11", "3.12"],
                                "os": ["ubuntu", "macos"]
                            },
                            steps=[
                                Step(name="Test", type=StepType.RUN, command="echo Testing")
                            ]
                        )
                    ]
                )
            ]
        )

        # Act
        yaml_output = generator.generate(pipeline)

        # Assert
        assert "matrix:" in yaml_output
        assert "parameters:" in yaml_output
        assert "python-version: [3.10, 3.11, 3.12]" in yaml_output
        assert "os: [ubuntu, macos]" in yaml_output

    def test_generate_with_schedule_trigger(self, generator):
        """Test generating workflow with schedule triggers"""
        pipeline = UniversalPipeline(
            name="nightly",
            triggers=[
                Trigger(type=TriggerType.SCHEDULE, schedule="0 0 * * *", branches=["main"])
            ],
            stages=[
                Stage(
                    name="nightly",
                    jobs=[
                        Job(
                            name="test",
                            runtime=Runtime(language="python", version="3.11"),
                            steps=[
                                Step(name="Run nightly tests", type=StepType.RUN, command="pytest")
                            ]
                        )
                    ]
                )
            ]
        )

        # Act
        yaml_output = generator.generate(pipeline)

        # Assert
        assert "triggers:" in yaml_output
        assert "schedule:" in yaml_output
        assert "cron: \"0 0 * * *\"" in yaml_output
        assert "filters:" in yaml_output
        assert "branches:" in yaml_output
        assert "only: main" in yaml_output