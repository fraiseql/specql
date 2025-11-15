"""
GitLab CI Parser

Reverse engineers GitLab CI YAML to universal pipeline format.
"""

import yaml
from typing import Dict, Any, List, Optional
from src.cicd.universal_pipeline_schema import (
    UniversalPipeline,
    Stage, Job, Step, StepType,
    Runtime, Service
)


class GitLabCIParser:
    """Parse GitLab CI YAML to universal format"""

    def parse(self, yaml_content: str) -> UniversalPipeline:
        """
        Parse GitLab CI YAML to UniversalPipeline

        Args:
            yaml_content: GitLab CI YAML content

        Returns:
            UniversalPipeline object
        """
        data = yaml.safe_load(yaml_content)

        # Extract stages and jobs
        stages_config = data.get("stages", [])
        jobs_config = {k: v for k, v in data.items() if k not in ["stages", "variables", "include"]}

        stages = self._parse_stages(stages_config, jobs_config)

        return UniversalPipeline(
            name="GitLab CI Pipeline",
            stages=stages,
            global_environment=data.get("variables", {})
        )

    def _parse_stages(self, stages_config: List[str], jobs_config: Dict[str, Any]) -> List[Stage]:
        """Parse stages from GitLab CI"""
        stages = []

        # Group jobs by stage
        jobs_by_stage = {}
        for job_name, job_config in jobs_config.items():
            stage_name = job_config.get("stage", "test")
            if stage_name not in jobs_by_stage:
                jobs_by_stage[stage_name] = []
            jobs_by_stage[stage_name].append(self._parse_job(job_name, job_config))

        # Create stages in order
        if stages_config:
            for stage_name in stages_config:
                if stage_name in jobs_by_stage:
                    stages.append(Stage(name=stage_name, jobs=jobs_by_stage[stage_name]))
        else:
            # If no explicit stages, create one stage per job
            for stage_name, jobs in jobs_by_stage.items():
                stages.append(Stage(name=stage_name, jobs=jobs))

        return stages

    def _parse_job(self, job_name: str, job_config: Dict[str, Any]) -> Job:
        """Parse single job"""
        return Job(
            name=job_name,
            steps=self._parse_steps(job_config),
            runtime=self._detect_runtime(job_config),
            services=self._parse_services(job_config.get("services", [])),
            environment=job_config.get("variables", {}),
            if_condition=self._parse_rules(job_config.get("rules"))
        )

    def _parse_services(self, services_config: List[str]) -> List[Service]:
        """Parse services"""
        services = []

        for service in services_config:
            if ":" in service:
                name, version = service.split(":", 1)
            else:
                name, version = service, "latest"

            services.append(Service(name=name, version=version))

        return services

    def _parse_steps(self, job_config: Dict[str, Any]) -> List[Step]:
        """Parse script/commands to universal steps"""
        steps = []

        # Before script
        before_script = job_config.get("before_script", [])
        if before_script:
            if isinstance(before_script, str):
                before_script = [before_script]
            for script in before_script:
                steps.append(Step(
                    name="before_script",
                    type=StepType.RUN,
                    command=script
                ))

        # Main script
        script = job_config.get("script", [])
        if isinstance(script, str):
            script = [script]
        for script_cmd in script:
            steps.append(Step(
                name="script",
                type=StepType.RUN,
                command=script_cmd
            ))

        # After script
        after_script = job_config.get("after_script", [])
        if after_script:
            if isinstance(after_script, str):
                after_script = [after_script]
            for script in after_script:
                steps.append(Step(
                    name="after_script",
                    type=StepType.RUN,
                    command=script
                ))

        return steps

    def _detect_runtime(self, job_config: Dict[str, Any]) -> Optional[Runtime]:
        """Detect runtime from job config"""
        # GitLab CI doesn't have explicit runtime setup like GitHub Actions
        # We could detect from image or assume defaults
        image = job_config.get("image")
        if image:
            if "python" in image:
                return Runtime(language="python", version="3.11")
            elif "node" in image:
                return Runtime(language="node", version="18")
            elif "golang" in image or "go:" in image:
                return Runtime(language="go", version="1.21")

        return None

    def _parse_rules(self, rules_config: Any) -> Optional[str]:
        """Parse rules to if condition"""
        if not rules_config:
            return None

        # Simple case: convert first rule's if condition
        if isinstance(rules_config, list) and rules_config:
            first_rule = rules_config[0]
            if isinstance(first_rule, dict) and "if" in first_rule:
                return first_rule["if"]

        return None