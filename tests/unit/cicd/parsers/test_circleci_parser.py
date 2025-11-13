"""Tests for CircleCI → Universal Pipeline parser"""

import pytest
from src.cicd.parsers.circleci_parser import CircleCIParser
from src.cicd.universal_pipeline_schema import UniversalPipeline, TriggerType, StepType


class TestCircleCIParser:
    """Test parsing CircleCI config.yml to universal format"""

    @pytest.fixture
    def parser(self):
        return CircleCIParser()

    def test_parse_simple_workflow(self, parser):
        """Test parsing basic CircleCI workflow"""
        yaml_content = """
version: 2.1

workflows:
  build_and_test:
    jobs:
      - build
      - test:
          requires:
            - build

jobs:
  build:
    docker:
      - image: cimg/python:3.11
    steps:
      - checkout
      - run: echo "Building..."
      - run:
          name: Install dependencies
          command: pip install -r requirements.txt

  test:
    docker:
      - image: cimg/python:3.11
    steps:
      - checkout
      - run:
          name: Run tests
          command: pytest
"""

        # Act
        pipeline = parser.parse(yaml_content)

        # Assert
        assert pipeline.name == "build_and_test"
        assert len(pipeline.stages) == 1  # CircleCI workflows become stages

        stage = pipeline.stages[0]
        assert len(stage.jobs) == 2

        # Check build job
        build_job = next(j for j in stage.jobs if j.name == "build")
        assert len(build_job.steps) == 3
        assert build_job.steps[0].type == StepType.CHECKOUT
        assert build_job.steps[1].type == StepType.RUN
        assert build_job.steps[2].type == StepType.INSTALL_DEPS

        # Check test job
        test_job = next(j for j in stage.jobs if j.name == "test")
        assert len(test_job.needs) == 1
        assert "build" in test_job.needs
        assert len(test_job.steps) == 2
        assert test_job.steps[1].type == StepType.RUN_TESTS

    def test_parse_with_triggers(self, parser):
        """Test parsing workflow with triggers"""
        yaml_content = """
version: 2.1

workflows:
  nightly:
    triggers:
      - schedule:
          cron: "0 0 * * *"
          filters:
            branches:
              only: main
    jobs:
      - test

jobs:
  test:
    docker:
      - image: cimg/python:3.11
    steps:
      - run: echo "Nightly test"
"""

        # Act
        pipeline = parser.parse(yaml_content)

        # Assert
        assert len(pipeline.triggers) == 1
        trigger = pipeline.triggers[0]
        assert trigger.type == TriggerType.SCHEDULE
        assert trigger.schedule == "0 0 * * *"
        assert trigger.branches == ["main"]

    def test_parse_with_services(self, parser):
        """Test parsing workflow with services"""
        yaml_content = """
version: 2.1

jobs:
  test:
    docker:
      - image: cimg/python:3.11
      - image: postgres:15
        environment:
          POSTGRES_PASSWORD: test
        ports:
          - "5432:5432"
    steps:
      - run: pytest tests/integration
"""

        # Act
        pipeline = parser.parse(yaml_content)

        # Assert
        job = pipeline.stages[0].jobs[0]
        assert len(job.services) == 1
        service = job.services[0]
        assert service.name == "postgres"
        assert service.version == "15"
        assert service.environment["POSTGRES_PASSWORD"] == "test"
        assert 5432 in service.ports

    def test_parse_with_matrix(self, parser):
        """Test parsing parameterized jobs (matrix builds)"""
        yaml_content = """
version: 2.1

workflows:
  matrix_test:
    jobs:
      - test:
          matrix:
            parameters:
              python-version: ["3.10", "3.11", "3.12"]
              os: [ubuntu, macos]

jobs:
  test:
    parameters:
      python-version:
        type: string
        default: "3.11"
      os:
        type: string
        default: "ubuntu"
    docker:
      - image: << parameters.python-version >>
    steps:
      - run: echo "Testing on << parameters.os >> with Python << parameters.python-version >>"
"""

        # Act
        pipeline = parser.parse(yaml_content)

        # Assert
        job = pipeline.stages[0].jobs[0]
        assert job.matrix is not None
        assert job.matrix["python-version"] == ["3.10", "3.11", "3.12"]
        assert job.matrix["os"] == ["ubuntu", "macos"]