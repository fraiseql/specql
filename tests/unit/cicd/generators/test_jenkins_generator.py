"""Tests for Universal → Jenkins generator"""

import pytest
from src.cicd.generators.jenkins_generator import JenkinsGenerator
from src.cicd.universal_pipeline_schema import *


class TestJenkinsGenerator:
    """Test generating Jenkinsfile from universal format"""

    @pytest.fixture
    def generator(self):
        return JenkinsGenerator()

    def test_generate_simple_pipeline(self, generator):
        """Test generating basic Jenkins pipeline"""
        pipeline = UniversalPipeline(
            name="build_and_test",
            stages=[
                Stage(
                    name="Build",
                    jobs=[
                        Job(
                            name="build",
                            steps=[
                                Step(name="Checkout", type=StepType.CHECKOUT),
                                Step(name="Install deps", type=StepType.INSTALL_DEPS, command="pip install -r requirements.txt"),
                            ]
                        )
                    ]
                ),
                Stage(
                    name="Test",
                    jobs=[
                        Job(
                            name="test",
                            steps=[
                                Step(name="Run tests", type=StepType.RUN_TESTS, command="pytest")
                            ]
                        )
                    ]
                )
            ]
        )

        # Act
        jenkinsfile_content = generator.generate(pipeline)

        # Assert
        assert "pipeline {" in jenkinsfile_content
        assert "agent any" in jenkinsfile_content
        assert "stages {" in jenkinsfile_content
        assert "stage('Build')" in jenkinsfile_content
        assert "stage('Test')" in jenkinsfile_content
        assert "sh 'pip install -r requirements.txt'" in jenkinsfile_content
        assert "sh 'pytest'" in jenkinsfile_content

    def test_generate_with_triggers(self, generator):
        """Test generating pipeline with triggers"""
        pipeline = UniversalPipeline(
            name="nightly",
            triggers=[
                Trigger(type=TriggerType.SCHEDULE, schedule="H 2 * * *")
            ],
            stages=[
                Stage(
                    name="Test",
                    jobs=[
                        Job(
                            name="test",
                            steps=[
                                Step(name="Run tests", type=StepType.RUN, command="pytest")
                            ]
                        )
                    ]
                )
            ]
        )

        # Act
        jenkinsfile_content = generator.generate(pipeline)

        # Assert
        assert "triggers {" in jenkinsfile_content
        assert "cron('H 2 * * *')" in jenkinsfile_content

    def test_generate_with_environment(self, generator):
        """Test generating pipeline with environment variables"""
        pipeline = UniversalPipeline(
            name="with_env",
            global_environment={"DATABASE_URL": "postgres://localhost", "API_KEY": "secret"},
            stages=[
                Stage(
                    name="Deploy",
                    jobs=[
                        Job(
                            name="deploy",
                            steps=[
                                Step(name="Deploy app", type=StepType.RUN, command="deploy.sh")
                            ]
                        )
                    ]
                )
            ]
        )

        # Act
        jenkinsfile_content = generator.generate(pipeline)

        # Assert
        assert "environment {" in jenkinsfile_content
        assert "DATABASE_URL = 'postgres://localhost'" in jenkinsfile_content
        assert "API_KEY = 'secret'" in jenkinsfile_content