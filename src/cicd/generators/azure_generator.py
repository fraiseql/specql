"""
Azure DevOps Generator

Converts universal pipeline format to Azure DevOps azure-pipelines.yml.
"""

from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from src.cicd.universal_pipeline_schema import UniversalPipeline, Step, StepType


class AzureGenerator:
    """Generate Azure DevOps azure-pipelines.yml from universal format"""

    def __init__(self, template_dir: Path = None):
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent.parent / "templates" / "cicd"

        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.template = self.env.get_template("azure-pipelines.yml.j2")

        # Add custom filters
        self.env.filters["render_step"] = self._render_step
        self.env.filters["render_runtime"] = self._render_runtime
        self.env.filters["render_triggers"] = self._render_triggers

    def generate(self, pipeline: UniversalPipeline) -> str:
        """
        Generate Azure DevOps azure-pipelines.yml from universal pipeline

        Args:
            pipeline: UniversalPipeline to convert

        Returns:
            Azure DevOps pipeline YAML content
        """
        return self.template.render(
            pipeline=pipeline,
            _render_step=self._render_step,
            _render_runtime=self._render_runtime,
            _render_triggers=self._render_triggers
        )

    def _render_step(self, step: Step) -> str:
        """Convert universal step to Azure DevOps step"""

        # Map step types to Azure DevOps syntax
        step_map = {
            StepType.CHECKOUT: "      - checkout: self",
            StepType.SETUP_RUNTIME: self._render_setup_runtime(step),
            StepType.CACHE_RESTORE: self._render_cache_step(step, "Cache"),
            StepType.CACHE_SAVE: self._render_cache_step(step, "Cache"),
            StepType.UPLOAD_ARTIFACT: self._render_artifact_step(step, "PublishBuildArtifacts"),
            StepType.DOWNLOAD_ARTIFACT: self._render_artifact_step(step, "DownloadBuildArtifacts"),
        }

        if step.type in step_map:
            return step_map[step.type]

        # Default: run command
        if step.command:
            step_yaml = f"      - script: {step.command}"
            if step.name and step.name != f"Execute: {step.command[:30]}...":
                step_yaml += f"\n        displayName: '{step.name}'"
            if step.environment:
                env_lines = "\n".join(f"        {k}: {v}" for k, v in step.environment.items())
                step_yaml += f"\n        env:\n{env_lines}"
            return step_yaml

        return f"      - script: echo '{step.name}'"

    def _render_setup_runtime(self, step: Step) -> str:
        """Render setup for runtime environment"""
        # Azure DevOps typically handles runtime via pool/vmImage
        # This is usually handled at the job level, not step level
        return "      - script: echo 'Runtime setup handled at job level'"

    def _render_cache_step(self, step: Step, action: str) -> str:
        """Render cache step"""
        key = step.with_params.get("key", "cache-key") if step.with_params else "cache-key"
        paths = step.with_params.get("paths", []) if step.with_params else []

        step_yaml = f"      - task: {action}@2"
        if key:
            step_yaml += f"\n        inputs:\n          key: '{key}'"
        if paths:
            paths_str = " | ".join(paths)
            step_yaml += f"\n          path: '{paths_str}'"

        return step_yaml

    def _render_artifact_step(self, step: Step, action: str) -> str:
        """Render artifact publish/download step"""
        artifact_name = step.with_params.get("name", "drop") if step.with_params else "drop"
        path = step.with_params.get("path", "$(Build.ArtifactStagingDirectory)") if step.with_params else "$(Build.ArtifactStagingDirectory)"

        step_yaml = f"      - task: {action}@1"
        step_yaml += f"\n        inputs:\n          artifactName: '{artifact_name}'"
        if action == "PublishBuildArtifacts":
            step_yaml += f"\n          pathtoPublish: '{path}'"
        else:
            step_yaml += f"\n          downloadPath: '{path}'"

        return step_yaml

    def _render_runtime(self, runtime) -> str:
        """Convert runtime to Azure DevOps pool vmImage"""
        if not runtime:
            return "ubuntu-latest"

        language_images = {
            "python": "ubuntu-latest",  # Python available by default
            "node": "ubuntu-latest",    # Node available by default
            "go": "ubuntu-latest",      # Go available by default
            "rust": "ubuntu-latest",    # Rust available by default
            "ruby": "ubuntu-latest",    # Ruby available by default
            "java": "ubuntu-latest",    # Java available by default
        }

        return language_images.get(runtime.language, "ubuntu-latest")

    def _render_triggers(self, triggers) -> str:
        """Convert triggers to Azure DevOps trigger format"""
        if not triggers:
            return ""

        trigger_yaml = ""

        # Handle push triggers
        push_triggers = [t for t in triggers if t.type == "push"]
        if push_triggers:
            trigger_yaml += "trigger:\n"
            all_branches = []
            for trigger in push_triggers:
                if trigger.branches:
                    all_branches.extend(trigger.branches)
            if all_branches:
                for branch in all_branches:
                    trigger_yaml += f"  - {branch}\n"
            else:
                trigger_yaml += "  - '*'\n"
            trigger_yaml += "\n"

        # Handle schedule triggers
        schedule_triggers = [t for t in triggers if t.type == "schedule"]
        if schedule_triggers:
            trigger_yaml += "schedules:\n"
            for trigger in schedule_triggers:
                trigger_yaml += "- cron: \"" + trigger.schedule + "\"\n"
                trigger_yaml += "  displayName: Scheduled build\n"
                if trigger.branches:
                    trigger_yaml += "  branches:\n    include:\n"
                    for branch in trigger.branches:
                        trigger_yaml += f"    - {branch}\n"
                trigger_yaml += "\n"

        return trigger_yaml