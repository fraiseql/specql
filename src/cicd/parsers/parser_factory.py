"""Parser factory for detecting and using correct parser"""

from pathlib import Path
from typing import Union
from src.cicd.parsers.github_actions_parser import GitHubActionsParser
from src.cicd.parsers.gitlab_ci_parser import GitLabCIParser
from src.cicd.parsers.circleci_parser import CircleCIParser
from src.cicd.parsers.jenkins_parser import JenkinsParser
from src.cicd.parsers.azure_parser import AzureParser
from src.cicd.universal_pipeline_schema import UniversalPipeline


class ParserFactory:
    """Factory for auto-detecting platform and parsing"""

    @staticmethod
    def parse_file(file_path: Path) -> UniversalPipeline:
        """
        Auto-detect platform and parse file

        Args:
            file_path: Path to CI/CD config file

        Returns:
            UniversalPipeline
        """
        content = file_path.read_text()

        # Detect platform from file path
        if ".github/workflows" in str(file_path):
            parser = GitHubActionsParser()
        elif ".gitlab-ci.yml" in file_path.name:
            parser = GitLabCIParser()
        elif "azure-pipelines.yml" in file_path.name:
            parser = AzureParser()
        elif "Jenkinsfile" in file_path.name:
            parser = JenkinsParser()
        elif ".circleci/config.yml" in str(file_path):
            parser = CircleCIParser()
        else:
            # Detect from content
            parser = ParserFactory._detect_from_content(content)

        return parser.parse(content)

    @staticmethod
    def _detect_from_content(content: str) -> Union[GitHubActionsParser, GitLabCIParser, CircleCIParser, JenkinsParser, AzureParser]:
        """Detect platform from YAML content"""
        if "jobs:" in content and "runs-on:" in content:
            return GitHubActionsParser()
        elif "stages:" in content and "script:" in content and ("pool:" in content or "trigger:" in content):
            return AzureParser()
        elif "stages:" in content and "script:" in content:
            return GitLabCIParser()
        elif "version: 2.1" in content and "workflows:" in content:
            return CircleCIParser()
        elif "pipeline {" in content and "agent" in content:
            return JenkinsParser()
        else:
            # Default to GitHub Actions
            return GitHubActionsParser()