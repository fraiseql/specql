"""
CircleCI Generator

Converts universal pipeline format to CircleCI config.yml.
"""

from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from src.cicd.universal_pipeline_schema import UniversalPipeline, Step, StepType


class CircleCIGenerator:
    """Generate CircleCI config.yml from universal format"""

    def __init__(self, template_dir: Path = None):
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent.parent / "templates" / "cicd"

        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.template = self.env.get_template("circleci.yml.j2")

        # Add custom filters
        self.env.filters["render_step"] = self._render_step
        self.env.filters["render_runtime"] = self._render_runtime
        self.env.filters["render_triggers"] = self._render_triggers

    def generate(self, pipeline: UniversalPipeline) -> str:
        """
        Generate CircleCI config.yml from universal pipeline

        Args:
            pipeline: UniversalPipeline to convert

        Returns:
            CircleCI config.yml content
        """
        return self.template.render(
            pipeline=pipeline,
            _render_step=self._render_step,
            _render_runtime=self._render_runtime,
            _render_triggers=self._render_triggers
        )

    def _render_step(self, step: Step) -> str:
        """Convert universal step to CircleCI step"""

        # Map step types to CircleCI syntax
        step_map = {
            StepType.CHECKOUT: "- checkout",
            StepType.SETUP_RUNTIME: self._render_setup_runtime(step),
            StepType.CACHE_RESTORE: self._render_cache_step(step, "restore_cache"),
            StepType.CACHE_SAVE: self._render_cache_step(step, "save_cache"),
            StepType.UPLOAD_ARTIFACT: self._render_workspace_step(step, "persist_to_workspace"),
            StepType.DOWNLOAD_ARTIFACT: self._render_workspace_step(step, "attach_workspace"),
        }

        if step.type in step_map:
            return step_map[step.type]

        # Default: run command
        if step.command:
            step_yaml = f"      - run:\n          name: {step.name}\n          command: {step.command}"
            if step.environment:
                env_lines = "\n".join(f"          {k}: {v}" for k, v in step.environment.items())
                step_yaml += f"\n          environment:\n{env_lines}"
            return step_yaml

        return f"      - run: {step.name}"

    def _render_setup_runtime(self, step: Step) -> str:
        """Render setup for runtime environment"""
        # CircleCI typically handles runtime via Docker images
        # This is usually handled at the job level, not step level
        return "      - run: echo 'Runtime setup handled at job level'"

    def _render_cache_step(self, step: Step, action: str) -> str:
        """Render cache save/restore step"""
        key = step.with_params.get("key", "cache-key") if step.with_params else "cache-key"
        paths = step.with_params.get("paths", []) if step.with_params else []

        step_yaml = f"      - {action}:"
        if key:
            step_yaml += f"\n          key: {key}"
        if paths and action == "save_cache":
            paths_yaml = "\n".join(f"          - {path}" for path in paths)
            step_yaml += f"\n          paths:{paths_yaml}"

        return step_yaml

    def _render_workspace_step(self, step: Step, action: str) -> str:
        """Render workspace persist/attach step"""
        root = step.with_params.get("root", ".") if step.with_params else "."
        paths = step.with_params.get("paths", ["."]) if step.with_params else ["."]

        step_yaml = f"      - {action}:"
        if root:
            step_yaml += f"\n          root: {root}"
        if paths:
            paths_yaml = "\n".join(f"          - {path}" for path in paths)
            step_yaml += f"\n          paths:{paths_yaml}"

        return step_yaml

    def _render_runtime(self, runtime) -> str:
        """Convert runtime to CircleCI Docker image"""
        if not runtime:
            return "cimg/base:stable"

        language_images = {
            "python": f"cimg/python:{runtime.version}",
            "node": f"cimg/node:{runtime.version}",
            "go": f"cimg/go:{runtime.version}",
            "rust": "cimg/rust:1.70",
            "ruby": f"cimg/ruby:{runtime.version}",
            "java": f"cimg/openjdk:{runtime.version}",
        }

        return language_images.get(runtime.language, "cimg/base:stable")

    def _render_triggers(self, triggers) -> str:
        """Convert triggers to CircleCI trigger format"""
        if not triggers:
            return ""

        # CircleCI triggers are workflow-level
        trigger_yaml = "    triggers:\n"
        for trigger in triggers:
            if trigger.type == "schedule":
                trigger_yaml += "      - schedule:\n"
                if trigger.schedule:
                    trigger_yaml += f"          cron: \"{trigger.schedule}\"\n"
                if trigger.branches:
                    trigger_yaml += "          filters:\n"
                    trigger_yaml += "            branches:\n"
                    trigger_yaml += f"              only: {' '.join(trigger.branches)}\n"

        return trigger_yaml