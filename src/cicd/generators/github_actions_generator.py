"""
GitHub Actions Generator

Converts universal pipeline format to GitHub Actions YAML.
"""

from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Optional
from src.cicd.universal_pipeline_schema import UniversalPipeline, Step, StepType


class GitHubActionsGenerator:
    """Generate GitHub Actions workflows from universal format"""

    def __init__(self, template_dir: Optional[Path] = None):
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent.parent / "templates" / "cicd"

        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.template = self.env.get_template("github_actions.yml.j2")

        # Add custom filter for step rendering
        self.env.filters["render_step"] = self._render_step

    def generate(self, pipeline: UniversalPipeline) -> str:
        """
        Generate GitHub Actions YAML from universal pipeline

        Args:
            pipeline: UniversalPipeline to convert

        Returns:
            GitHub Actions YAML content
        """
        return self.template.render(
            pipeline=pipeline,
            _render_step=self._render_step
        )

    def _render_step(self, step: Step) -> str:
        """Convert universal step to GitHub Actions step"""

        # Map step types to GitHub Actions syntax
        step_map = {
            StepType.CHECKOUT: "uses: actions/checkout@v4",
            StepType.SETUP_RUNTIME: self._render_setup_runtime(step),
            StepType.CACHE_RESTORE: "uses: actions/cache@v4",
            StepType.UPLOAD_ARTIFACT: "uses: actions/upload-artifact@v4",
            StepType.DOWNLOAD_ARTIFACT: "uses: actions/download-artifact@v4",
        }

        if step.type in step_map:
            action = step_map[step.type]
            if step.with_params:
                params = "\n".join(f"        {k}: {v}" for k, v in step.with_params.items())
                return f"{action}\n      with:\n{params}"
            return action

        # Default: run command
        return f"run: {step.command}"

    def _render_setup_runtime(self, step: Step) -> str:
        """Render setup-* action based on language"""
        language = step.with_params.get("language", "python")

        runtime_actions = {
            "python": "actions/setup-python@v5",
            "node": "actions/setup-node@v4",
            "go": "actions/setup-go@v5",
            "rust": "dtolnay/rust-toolchain@stable",
        }

        return f"uses: {runtime_actions.get(language, 'actions/setup-python@v5')}"