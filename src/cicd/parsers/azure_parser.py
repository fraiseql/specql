"""
Azure DevOps Parser

Reverse engineers Azure DevOps azure-pipelines.yml to universal pipeline format.
"""

import yaml
from typing import Dict, Any, List
from src.cicd.universal_pipeline_schema import (
    UniversalPipeline,
    Trigger, TriggerType,
    Stage, Job, Step, StepType,
    Runtime
)


class AzureParser:
    """Parse Azure DevOps azure-pipelines.yml to universal format"""

    def parse(self, yaml_content: str) -> UniversalPipeline:
        """
        Parse Azure DevOps YAML to UniversalPipeline

        Args:
            yaml_content: Azure DevOps pipeline YAML

        Returns:
            UniversalPipeline object
        """
        data = yaml.safe_load(yaml_content)

        return UniversalPipeline(
            name="Azure Pipeline",
            triggers=self._parse_triggers(data),
            stages=self._parse_stages(data.get("stages", [])),
            global_environment=data.get("variables", {})
        )

    def _parse_triggers(self, data: Dict[str, Any]) -> List[Trigger]:
        """Parse triggers section"""
        triggers = []

        # Parse push triggers
        if "trigger" in data:
            trigger_config = data["trigger"]
            if isinstance(trigger_config, list):
                branches = trigger_config
            elif isinstance(trigger_config, dict):
                branches = trigger_config.get("branches", {}).get("include", [])
            else:
                branches = [trigger_config] if trigger_config else []

            if branches:
                triggers.append(Trigger(
                    type=TriggerType.PUSH,
                    branches=branches
                ))

        # Parse schedule triggers
        if "schedules" in data:
            for schedule_config in data["schedules"]:
                cron_expr = schedule_config.get("cron")
                branches = schedule_config.get("branches", {}).get("include", [])

                triggers.append(Trigger(
                    type=TriggerType.SCHEDULE,
                    schedule=cron_expr,
                    branches=branches
                ))

        return triggers

    def _parse_stages(self, stages_config: List[Dict[str, Any]]) -> List[Stage]:
        """Parse stages to universal format"""
        stages = []

        for stage_config in stages_config:
            stage_name = stage_config.get("stage")
            jobs_config = stage_config.get("jobs", [])

            jobs = []
            for job_config in jobs_config:
                job_name = job_config.get("job")
                steps_config = job_config.get("steps", [])

                steps = []
                for step_config in steps_config:
                    step = self._parse_step(step_config)
                    if step:
                        steps.append(step)

                jobs.append(Job(
                    name=job_name,
                    steps=steps,
                    runtime=self._detect_runtime(job_config)
                ))

            stages.append(Stage(name=stage_name, jobs=jobs))

        return stages

    def _parse_step(self, step_config: Dict[str, Any]) -> Step:
        """Parse individual step"""
        if "script" in step_config:
            command = step_config["script"]
            step_type = self._detect_step_type(command)
            return Step(
                name=f"Execute: {command[:30]}...",
                type=step_type,
                command=command
            )

        return None

    def _detect_step_type(self, command: str) -> StepType:
        """Detect step type from command"""
        command_lower = command.lower()

        if "pip install" in command_lower or "npm install" in command_lower:
            return StepType.INSTALL_DEPS
        elif "pytest" in command_lower or "npm test" in command_lower:
            return StepType.RUN_TESTS
        elif "checkout" in command_lower:
            return StepType.CHECKOUT
        elif "docker build" in command_lower:
            return StepType.BUILD
        elif "kubectl" in command_lower or "deploy" in command_lower:
            return StepType.DEPLOY

        return StepType.RUN

    def _detect_runtime(self, job_config: Dict[str, Any]) -> Runtime:
        """Detect runtime from job configuration"""
        pool_config = job_config.get("pool", {})
        vm_image = pool_config.get("vmImage", "")

        if "ubuntu" in vm_image:
            return Runtime(language="python", version="3.11")  # Default assumption
        elif "windows" in vm_image:
            return Runtime(language="python", version="3.11")
        elif "macos" in vm_image:
            return Runtime(language="python", version="3.11")

        return None