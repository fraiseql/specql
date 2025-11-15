"""
Jenkins Generator

Converts universal pipeline format to Jenkinsfile (Groovy DSL).
"""

from src.cicd.universal_pipeline_schema import UniversalPipeline, Step


class JenkinsGenerator:
    """Generate Jenkinsfile from universal format"""

    def generate(self, pipeline: UniversalPipeline) -> str:
        """
        Generate Jenkinsfile from universal pipeline

        Args:
            pipeline: UniversalPipeline to convert

        Returns:
            Jenkinsfile content
        """
        lines = ["pipeline {"]

        # Agent
        lines.append("    agent any")
        lines.append("")

        # Triggers
        if pipeline.triggers:
            trigger_lines = self._generate_triggers(pipeline.triggers)
            if trigger_lines:
                lines.extend(trigger_lines)
                lines.append("")

        # Environment
        if pipeline.global_environment:
            env_lines = self._generate_environment(pipeline.global_environment)
            lines.extend(env_lines)
            lines.append("")

        # Stages
        lines.append("    stages {")
        for stage in pipeline.stages:
            stage_lines = self._generate_stage(stage)
            lines.extend(stage_lines)
        lines.append("    }")

        lines.append("}")

        return "\n".join(lines)

    def _generate_triggers(self, triggers) -> list[str]:
        """Generate triggers block"""
        lines = ["    triggers {"]

        for trigger in triggers:
            if trigger.type == "schedule" and trigger.schedule:
                lines.append(f"        cron('{trigger.schedule}')")

        if len(lines) > 1:  # More than just the opening brace
            lines.append("    }")
            return lines

        return []  # No triggers to add

    def _generate_environment(self, environment: dict) -> list[str]:
        """Generate environment block"""
        lines = ["    environment {"]

        for key, value in environment.items():
            lines.append(f"        {key} = '{value}'")

        lines.append("    }")
        return lines

    def _generate_stage(self, stage) -> list[str]:
        """Generate a single stage"""
        lines = [f"        stage('{stage.name}') {{"]

        # For simplicity, assume single job per stage
        if stage.jobs:
            job = stage.jobs[0]  # Take first job
            lines.append("            steps {")

            for step in job.steps:
                step_line = self._generate_step(step)
                if step_line:
                    lines.append(f"                {step_line}")

            lines.append("            }")

        lines.append("        }")
        return lines

    def _generate_step(self, step: Step) -> str:
        """Generate a single step"""
        if step.command:
            return f"sh '{step.command}'"

        return None