"""
GitHub Actions Parser

Reverse engineers GitHub Actions YAML to universal pipeline format.
"""

import yaml
from typing import Dict, Any, List, Optional
from src.cicd.universal_pipeline_schema import (
    UniversalPipeline,
    Trigger, TriggerType,
    Stage, Job, Step, StepType,
    Runtime, Service
)


class GitHubActionsParser:
    """Parse GitHub Actions workflows to universal format"""

    def parse(self, yaml_content: str) -> UniversalPipeline:
        """
        Parse GitHub Actions YAML to UniversalPipeline

        Args:
            yaml_content: GitHub Actions workflow YAML

        Returns:
            UniversalPipeline object
        """
        data = yaml.safe_load(yaml_content)

        return UniversalPipeline(
            name=data.get("name", "Unnamed Pipeline"),
            triggers=self._parse_triggers(data.get("on", {})),
            stages=self._parse_jobs(data.get("jobs", {})),
            global_environment=data.get("env", {})
        )

    def _parse_triggers(self, on_config: Any) -> List[Trigger]:
        """Parse 'on:' section to universal triggers"""
        triggers = []

        if isinstance(on_config, str):
            # Simple case: on: push
            triggers.append(Trigger(type=TriggerType(on_config)))

        elif isinstance(on_config, list):
            # List case: on: [push, pull_request]
            for trigger_type in on_config:
                triggers.append(Trigger(type=TriggerType(trigger_type)))

        elif isinstance(on_config, dict):
            # Complex case with branches/paths
            for trigger_type, config in on_config.items():
                if isinstance(config, dict):
                    triggers.append(Trigger(
                        type=TriggerType(trigger_type),
                        branches=config.get("branches"),
                        tags=config.get("tags"),
                        paths=config.get("paths")
                    ))
                else:
                    triggers.append(Trigger(type=TriggerType(trigger_type)))

        return triggers

    def _parse_jobs(self, jobs_config: Dict[str, Any]) -> List[Stage]:
        """Parse jobs to universal stages"""
        # GitHub Actions doesn't have explicit stages
        # We create a single stage with all jobs

        jobs = []
        for job_id, job_config in jobs_config.items():
            jobs.append(self._parse_job(job_id, job_config))

        return [Stage(name="default", jobs=jobs)]

    def _parse_job(self, job_id: str, job_config: Dict[str, Any]) -> Job:
        """Parse single job"""
        return Job(
            name=job_config.get("name", job_id),
            steps=self._parse_steps(job_config.get("steps", [])),
            runtime=self._detect_runtime(job_config),
            services=self._parse_services(job_config.get("services", {})),
            needs=job_config.get("needs", []) if isinstance(job_config.get("needs"), list) else [job_config.get("needs")] if job_config.get("needs") else [],
            if_condition=job_config.get("if"),
            matrix=self._parse_matrix(job_config.get("strategy", {}).get("matrix")),
            environment=job_config.get("env", {})
        )

    def _parse_steps(self, steps_config: List[Dict[str, Any]]) -> List[Step]:
        """Parse steps to universal format"""
        steps = []

        for step_config in steps_config:
            step_type = self._detect_step_type(step_config)

            steps.append(Step(
                name=step_config.get("name", "Unnamed step"),
                type=step_type,
                command=step_config.get("run"),
                with_params=step_config.get("with", {}),
                environment=step_config.get("env", {}),
                continue_on_error=step_config.get("continue-on-error", False),
                timeout_minutes=step_config.get("timeout-minutes")
            ))

        return steps

    def _detect_step_type(self, step_config: Dict[str, Any]) -> StepType:
        """Detect step type from configuration"""

        # Check 'uses' field for actions
        uses = step_config.get("uses", "")

        if "checkout" in uses:
            return StepType.CHECKOUT
        elif "setup-python" in uses or "setup-node" in uses or "setup-go" in uses:
            return StepType.SETUP_RUNTIME
        elif "cache" in uses:
            return StepType.CACHE_RESTORE
        elif "upload-artifact" in uses:
            return StepType.UPLOAD_ARTIFACT
        elif "download-artifact" in uses:
            return StepType.DOWNLOAD_ARTIFACT

        # Check 'run' field for commands
        run = step_config.get("run", "")

        if "pip install" in run or "npm install" in run or "go mod download" in run:
            return StepType.INSTALL_DEPS
        elif "pytest" in run or "npm test" in run or "go test" in run:
            return StepType.RUN_TESTS
        elif "ruff" in run or "eslint" in run or "go vet" in run:
            return StepType.LINT
        elif "docker build" in run or "npm run build" in run:
            return StepType.BUILD
        elif "kubectl" in run or "deploy" in run:
            return StepType.DEPLOY

        return StepType.RUN

    def _parse_services(self, services_config: Dict[str, Any]) -> List[Service]:
        """Parse services (databases, caches, etc.)"""
        services = []

        for service_name, service_config in services_config.items():
            image = service_config.get("image", "")
            name, _, version = image.partition(":")

            services.append(Service(
                name=name or service_name,
                version=version or "latest",
                environment=service_config.get("env", {}),
                ports=[int(p.split(":")[0]) for p in service_config.get("ports", [])]
            ))

        return services

    def _detect_runtime(self, job_config: Dict[str, Any]) -> Runtime:
        """Detect runtime from steps"""
        steps = job_config.get("steps", [])

        for step in steps:
            uses = step.get("uses", "")

            if "setup-python" in uses:
                version = step.get("with", {}).get("python-version", "3.11")
                return Runtime(language="python", version=str(version))
            elif "setup-node" in uses:
                version = step.get("with", {}).get("node-version", "18")
                return Runtime(language="node", version=str(version))
            elif "setup-go" in uses:
                version = step.get("with", {}).get("go-version", "1.21")
                return Runtime(language="go", version=str(version))

        return None

    def _parse_matrix(self, matrix_config: Any) -> Optional[Dict[str, List[str]]]:
        """Parse matrix strategy"""
        if not matrix_config:
            return None

        result = {}
        for key, values in matrix_config.items():
            if isinstance(values, list):
                result[key] = [str(v) for v in values]

        return result if result else None