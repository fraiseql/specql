"""
GitLab CI Generator

Converts universal pipeline format to GitLab CI YAML.
"""

from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Optional
from src.cicd.universal_pipeline_schema import UniversalPipeline


class GitLabCIGenerator:
    """Generate GitLab CI pipelines from universal format"""

    def __init__(self, template_dir: Optional[Path] = None):
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent.parent / "templates" / "cicd"

        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.template = self.env.get_template("gitlab_ci.yml.j2")

    def generate(self, pipeline: UniversalPipeline) -> str:
        """
        Generate GitLab CI YAML from universal pipeline

        Args:
            pipeline: UniversalPipeline to convert

        Returns:
            GitLab CI YAML content
        """
        return self.template.render(pipeline=pipeline)