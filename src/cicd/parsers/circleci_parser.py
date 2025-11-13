"""
CircleCI Parser

Reverse engineers CircleCI config.yml to universal pipeline format.
"""

import yaml
from typing import Dict, Any, List
from src.cicd.universal_pipeline_schema import (
    UniversalPipeline,
    Trigger, TriggerType,
    Stage, Job, Step, StepType,
    Runtime, Service
)


class CircleCIParser:
    """Parse CircleCI config.yml to universal format"""

    def parse(self, yaml_content: str) -> UniversalPipeline:
        """
        Parse CircleCI YAML to UniversalPipeline

        Args:
            yaml_content: CircleCI config.yml content

        Returns:
            UniversalPipeline object
        """
        data = yaml.safe_load(yaml_content)

        # CircleCI has workflows that contain jobs
        # We'll convert workflows to stages
        workflows = data.get("workflows", {})
        jobs_config = data.get("jobs", {})

        if workflows:
            workflow_name = list(workflows.keys())[0]
            workflow_config = list(workflows.values())[0]
        else:
            # If no workflows defined, create a default one with all jobs
            workflow_name = "default"
            workflow_config = {"jobs": list(jobs_config.keys())}

        return UniversalPipeline(
            name=workflow_name,
            triggers=self._parse_triggers(workflow_config),
            stages=self._parse_workflows({workflow_name: workflow_config}, jobs_config),
            global_environment=data.get("env", {})
        )

    def _parse_triggers(self, workflow_config: Dict[str, Any]) -> List[Trigger]:
        """Parse workflow triggers"""
        triggers = []

        # Check for schedule triggers
        workflow_triggers = workflow_config.get("triggers", [])
        for trigger_config in workflow_triggers:
            if "schedule" in trigger_config:
                schedule_config = trigger_config["schedule"]
                branches = schedule_config.get("filters", {}).get("branches", {}).get("only")
                # Ensure branches is a list
                if isinstance(branches, str):
                    branches = [branches]
                trigger = Trigger(
                    type=TriggerType.SCHEDULE,
                    schedule=schedule_config.get("cron"),
                    branches=branches
                )
                triggers.append(trigger)

        # If no explicit triggers, assume push (CircleCI default behavior)
        if not triggers:
            triggers.append(Trigger(type=TriggerType.PUSH))

        return triggers

    def _parse_workflows(self, workflows: Dict[str, Any], jobs_config: Dict[str, Any]) -> List[Stage]:
        """Parse workflows to universal stages"""
        stages = []

        for workflow_name, workflow_config in workflows.items():
            jobs = workflow_config.get("jobs", [])

            # Convert workflow jobs to universal jobs
            universal_jobs = []
            for job_config in jobs:
                if isinstance(job_config, str):
                    # Simple job reference
                    job_name = job_config
                    job_details = jobs_config.get(job_name, {})
                    universal_jobs.append(self._parse_job(job_name, job_details, {}))
                elif isinstance(job_config, dict):
                    # Job with parameters
                    job_name = list(job_config.keys())[0]
                    job_params = job_config[job_name]
                    job_details = jobs_config.get(job_name, {})
                    universal_jobs.append(self._parse_job(job_name, job_details, job_params))

            stages.append(Stage(name=workflow_name, jobs=universal_jobs))

        return stages

    def _parse_job(self, job_name: str, job_config: Dict[str, Any], job_params: Dict[str, Any]) -> Job:
        """Parse single job"""
        # Handle matrix builds
        matrix = None
        if "matrix" in job_params:
            matrix_config = job_params["matrix"]
            if "parameters" in matrix_config:
                matrix = {}
                for param_name, param_values in matrix_config["parameters"].items():
                    matrix[param_name] = [str(v) for v in param_values]

        return Job(
            name=job_name,
            steps=self._parse_steps(job_config.get("steps", [])),
            runtime=self._detect_runtime(job_config),
            services=self._parse_services(job_config),
            needs=job_params.get("requires", []) if isinstance(job_params.get("requires"), list) else [job_params.get("requires")] if job_params.get("requires") else [],
            matrix=matrix,
            environment=job_config.get("environment", {})
        )

    def _parse_steps(self, steps_config: List[Dict[str, Any]]) -> List[Step]:
        """Parse steps to universal format"""
        steps = []

        for step_config in steps_config:
            step_type = self._detect_step_type(step_config)

            # Handle different step formats
            if isinstance(step_config, str):
                # Simple step like "checkout"
                step = Step(
                    name=step_config,
                    type=step_type,
                    command=step_config
                )
            else:
                # Complex step with parameters
                step_name = step_config.get("name", list(step_config.keys())[0] if step_config else "Unnamed step")
                command = step_config.get("command") or step_config.get("run")

                step = Step(
                    name=step_name,
                    type=step_type,
                    command=command,
                    with_params=step_config.get("with", {}),
                    environment=step_config.get("environment", {}),
                    continue_on_error=step_config.get("continue_on_error", False)
                )

            steps.append(step)

        return steps

    def _detect_step_type(self, step_config: Any) -> StepType:
        """Detect step type from configuration"""

        if isinstance(step_config, str):
            step_name = step_config
            command = ""
        else:
            # Find the primary action
            step_name = None
            command = ""

            for key in step_config.keys():
                if key not in ["name", "environment", "continue_on_error", "with"]:
                    step_name = key
                    # If the value is a dict, look for command inside it
                    if isinstance(step_config[key], dict):
                        command = step_config[key].get("command", "")
                    break

            if not step_name:
                step_name = step_config.get("run", "")
                command = step_config.get("command", "")

            # Also check direct command field
            if not command:
                command = step_config.get("command", "") or step_config.get("run", "")

        # Map CircleCI steps to universal types
        if "checkout" in step_name:
            return StepType.CHECKOUT
        elif "setup_remote_docker" in step_name:
            return StepType.RUN
        elif "persist_to_workspace" in step_name:
            return StepType.UPLOAD_ARTIFACT
        elif "attach_workspace" in step_name:
            return StepType.DOWNLOAD_ARTIFACT
        elif "save_cache" in step_name:
            return StepType.CACHE_SAVE
        elif "restore_cache" in step_name:
            return StepType.CACHE_RESTORE

        # Check command content for install commands
        if "pip install" in command or "npm install" in command or "yarn install" in command:
            return StepType.INSTALL_DEPS
        elif "pytest" in command or "npm test" in command or "yarn test" in command:
            return StepType.RUN_TESTS
        elif "ruff" in command or "eslint" in command or "black" in command:
            return StepType.LINT
        elif "docker build" in command or "npm run build" in command:
            return StepType.BUILD
        elif "kubectl" in command or "deploy" in command:
            return StepType.DEPLOY

        return StepType.RUN

    def _parse_services(self, job_config: Dict[str, Any]) -> List[Service]:
        """Parse services (additional Docker images)"""
        services = []

        # In CircleCI, additional docker images beyond the primary one are services
        docker_config = job_config.get("docker", [])
        if len(docker_config) > 1:
            for docker_image in docker_config[1:]:  # Skip primary image
                if isinstance(docker_image, str):
                    name, _, version = docker_image.partition(":")
                    services.append(Service(
                        name=name or "docker",
                        version=version or "latest"
                    ))
                elif isinstance(docker_image, dict):
                    image = docker_image.get("image", "")
                    name, _, version = image.partition(":")
                    services.append(Service(
                        name=name or "docker",
                        version=version or "latest",
                        environment=docker_image.get("environment", {}),
                        ports=[int(p.split(":")[0]) for p in docker_image.get("ports", [])]
                    ))

        return services

    def _detect_runtime(self, job_config: Dict[str, Any]) -> Runtime:
        """Detect runtime from Docker image"""
        docker_config = job_config.get("docker", [])
        if not docker_config:
            return None

        primary_image = docker_config[0]
        if isinstance(primary_image, str):
            image = primary_image
        elif isinstance(primary_image, dict):
            image = primary_image.get("image", "")
        else:
            return None

        # Detect language from image name
        image_lower = image.lower()
        if "python" in image_lower or "cimg/python" in image_lower:
            return Runtime(language="python", version="3.11")
        elif "node" in image_lower or "cimg/node" in image_lower:
            return Runtime(language="node", version="18")
        elif "golang" in image_lower or "cimg/go" in image_lower:
            return Runtime(language="go", version="1.21")
        elif "rust" in image_lower or "cimg/rust" in image_lower:
            return Runtime(language="rust", version="1.70")

        return None