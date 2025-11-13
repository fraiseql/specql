"""Tests for GitLab CI → Universal Pipeline parser"""

import pytest
from src.cicd.parsers.gitlab_ci_parser import GitLabCIParser
from src.cicd.universal_pipeline_schema import UniversalPipeline, TriggerType, StepType


class TestGitLabCIParser:
    """Test parsing GitLab CI YAML to universal format"""

    @pytest.fixture
    def parser(self):
        return GitLabCIParser()

    def test_parse_simple_pipeline(self, parser):
        """Test parsing basic GitLab CI pipeline"""
        yaml_content = """stages:
  - test
  - deploy

test:
  stage: test
  script:
    - echo "Running tests"
    - pytest

deploy:
  stage: deploy
  script:
    - echo "Deploying"
  only:
    - main
"""

        # Act
        pipeline = parser.parse(yaml_content)

        # Assert
        assert len(pipeline.stages) == 2
        assert pipeline.stages[0].name == "test"
        assert pipeline.stages[1].name == "deploy"

        test_job = pipeline.stages[0].jobs[0]
        assert test_job.name == "test"
        assert len(test_job.steps) == 2
        assert test_job.steps[0].command == 'echo "Running tests"'
        assert test_job.steps[1].command == "pytest"

        deploy_job = pipeline.stages[1].jobs[0]
        assert deploy_job.name == "deploy"
        assert len(deploy_job.steps) == 1
        assert deploy_job.steps[0].command == 'echo "Deploying"'

    def test_parse_with_services(self, parser):
        """Test parsing pipeline with services"""
        yaml_content = """test:
  services:
    - postgres:15
  variables:
    POSTGRES_PASSWORD: test
  script:
    - pytest tests/integration
"""

        # Act
        pipeline = parser.parse(yaml_content)

        # Assert
        job = pipeline.stages[0].jobs[0]
        assert len(job.services) == 1
        assert job.services[0].name == "postgres"
        assert job.services[0].version == "15"
        assert job.environment["POSTGRES_PASSWORD"] == "test"

    def test_parse_with_rules(self, parser):
        """Test parsing rules as triggers"""
        yaml_content = """deploy:
  script:
    - deploy
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: always
    - when: never
"""

        # Act
        pipeline = parser.parse(yaml_content)

        # Assert
        job = pipeline.stages[0].jobs[0]
        assert job.if_condition == '$CI_COMMIT_BRANCH == "main"'