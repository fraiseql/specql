"""Tests for Azure DevOps → Universal Pipeline parser"""

import pytest
from src.cicd.parsers.azure_parser import AzureParser
from src.cicd.universal_pipeline_schema import UniversalPipeline, TriggerType, StepType


class TestAzureParser:
    """Test parsing Azure DevOps azure-pipelines.yml to universal format"""

    @pytest.fixture
    def parser(self):
        return AzureParser()

    def test_parse_simple_pipeline(self, parser):
        """Test parsing basic Azure DevOps pipeline"""
        yaml_content = """
trigger:
  - main
  - develop

pool:
  vmImage: 'ubuntu-latest'

stages:
- stage: Build
  jobs:
  - job: build
    steps:
    - script: echo "Building..."
    - script: pip install -r requirements.txt

- stage: Test
  jobs:
  - job: test
    steps:
    - script: pytest
"""

        # Act
        pipeline = parser.parse(yaml_content)

        # Assert
        assert pipeline.name == "Azure Pipeline"
        assert len(pipeline.triggers) == 1
        assert pipeline.triggers[0].type == TriggerType.PUSH
        assert pipeline.triggers[0].branches == ["main", "develop"]

        assert len(pipeline.stages) == 2

        # Check build stage
        build_stage = next(s for s in pipeline.stages if s.name == "Build")
        assert len(build_stage.jobs) == 1
        build_job = build_stage.jobs[0]
        assert len(build_job.steps) == 2
        assert build_job.steps[0].type == StepType.RUN
        assert build_job.steps[1].type == StepType.INSTALL_DEPS

        # Check test stage
        test_stage = next(s for s in pipeline.stages if s.name == "Test")
        assert len(test_stage.jobs) == 1
        test_job = test_stage.jobs[0]
        assert len(test_job.steps) == 1
        assert test_job.steps[0].type == StepType.RUN_TESTS

    def test_parse_with_schedule_trigger(self, parser):
        """Test parsing pipeline with schedule triggers"""
        yaml_content = """
schedules:
- cron: "0 2 * * *"
  displayName: Nightly build
  branches:
    include:
    - main

stages:
- stage: Test
  jobs:
  - job: test
    steps:
    - script: pytest
"""

        # Act
        pipeline = parser.parse(yaml_content)

        # Assert
        assert len(pipeline.triggers) == 1
        trigger = pipeline.triggers[0]
        assert trigger.type == TriggerType.SCHEDULE
        assert trigger.schedule == "0 2 * * *"
        assert trigger.branches == ["main"]