"""
Jenkins Parser

Reverse engineers Jenkinsfile (Groovy DSL) to universal pipeline format.
"""

import re
from typing import Dict, List
from src.cicd.universal_pipeline_schema import (
    UniversalPipeline,
    Trigger, TriggerType,
    Stage, Job, Step, StepType,
    Runtime
)


class JenkinsParser:
    """Parse Jenkinsfile to universal format"""

    def parse(self, groovy_content: str) -> UniversalPipeline:
        """
        Parse Jenkinsfile Groovy DSL to UniversalPipeline

        Args:
            groovy_content: Jenkinsfile content

        Returns:
            UniversalPipeline object
        """
        # Simple approach: remove the 'pipeline {' prefix and '}' suffix
        # This works for the test cases
        if 'pipeline {' not in groovy_content:
            raise ValueError("No pipeline block found in Jenkinsfile")

        # Extract content between 'pipeline {' and the last '}'
        start = groovy_content.find('pipeline {') + len('pipeline {')
        # Find the matching closing brace (simplified - assumes well-formed)
        end = groovy_content.rfind('}')
        pipeline_content = groovy_content[start:end]

        # Parse different sections
        triggers = self._parse_triggers(pipeline_content)
        stages = self._parse_stages(pipeline_content)

        return UniversalPipeline(
            name="Jenkins Pipeline",
            triggers=triggers,
            stages=stages,
            global_environment=self._parse_environment(pipeline_content)
        )

    def _parse_triggers(self, pipeline_content: str) -> List[Trigger]:
        """Parse triggers section"""
        triggers = []

        # Look for triggers block
        triggers_match = re.search(r'triggers\s*\{(.*?)\}', pipeline_content, re.DOTALL)
        if triggers_match:
            triggers_content = triggers_match.group(1)

            # Parse cron triggers
            cron_matches = re.findall(r"cron\s*\(\s*'([^']+)'\s*\)", triggers_content)
            for cron_expr in cron_matches:
                triggers.append(Trigger(type=TriggerType.SCHEDULE, schedule=cron_expr))

            # Parse pollSCM triggers
            poll_matches = re.findall(r"pollSCM\s*\(\s*'([^']+)'\s*\)", triggers_content)
            for poll_expr in poll_matches:
                # pollSCM is similar to cron but for polling
                triggers.append(Trigger(type=TriggerType.SCHEDULE, schedule=poll_expr))

        return triggers

    def _parse_stages(self, pipeline_content: str) -> List[Stage]:
        """Parse stages section"""
        stages = []

        # Find stages block using brace counting
        stages_start = pipeline_content.find('stages {')
        if stages_start != -1:
            stages_content = self._extract_brace_block(pipeline_content[stages_start:])

            # Find all stage blocks - split by stage declarations to avoid nested parsing issues
            # This is a simpler approach: split by 'stage(' and process each one
            stage_blocks = re.split(r'(?=stage\s*\(\s*[\'"])', stages_content)
            for block in stage_blocks:
                if block.strip() and 'stage(' in block:
                    # Extract stage name
                    name_match = re.search(r'stage\s*\(\s*[\'"]([^\'"]+)[\'"]', block)
                    if name_match:
                        stage_name = name_match.group(1)
                        # Find the opening brace for this stage
                        brace_pos = block.find('{')
                        if brace_pos != -1:
                            stage_content = self._extract_brace_block(block[brace_pos:])

                            jobs = self._parse_stage_content(stage_name, stage_content)
                            stages.append(Stage(name=stage_name, jobs=jobs))

        # Also check for post block (converted to stages)
        post_stages = self._parse_post_actions(pipeline_content)
        stages.extend(post_stages)

        return stages

    def _extract_brace_block(self, content: str) -> str:
        """Extract content between matching braces"""
        brace_count = 0
        start_pos = content.find('{')
        if start_pos == -1:
            return ""

        for i, char in enumerate(content[start_pos:]):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return content[start_pos + 1:start_pos + i]

        return ""

    def _parse_stage_content(self, stage_name: str, stage_content: str) -> List[Job]:
        """Parse content of a single stage"""
        jobs = []

        # Check if this stage has parallel execution
        if 'parallel {' in stage_content:
            # Parse parallel stages as separate jobs within this stage
            parallel_start = stage_content.find('parallel {')
            parallel_content = self._extract_brace_block(stage_content[parallel_start:])

            # Find all parallel stages
            parallel_stage_pattern = r'stage\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)\s*\{'
            for match in re.finditer(parallel_stage_pattern, parallel_content):
                parallel_stage_name = match.group(1)
                start_pos = match.end() - 1
                parallel_stage_content = self._extract_brace_block(parallel_content[start_pos:])

                steps = self._parse_steps(parallel_stage_content)
                jobs.append(Job(
                    name=parallel_stage_name,
                    steps=steps,
                    runtime=self._detect_runtime(parallel_stage_content)
                ))
        else:
            # Single job stage
            steps = self._parse_steps(stage_content)
            jobs.append(Job(
                name=stage_name,
                steps=steps,
                runtime=self._detect_runtime(stage_content)
            ))

        return jobs

    def _parse_steps(self, content: str) -> List[Step]:
        """Parse steps within a stage/job"""
        steps = []

        # Look for steps block
        steps_match = re.search(r'steps\s*\{(.*?)\}', content, re.DOTALL)
        if steps_match:
            steps_content = self._extract_brace_block(content[content.find('steps {'):])

            # Find all step calls
            step_matches = re.findall(r'(\w+)\s+[\'"]([^\'"]+)[\'"]', steps_content)

            for step_name, step_args in step_matches:
                if step_name == 'sh':
                    # Shell command
                    command = step_args
                    step_type = self._detect_step_type(command)
                    steps.append(Step(
                        name=f"Execute: {command[:30]}...",
                        type=step_type,
                        command=command
                    ))

        return steps

    def _detect_step_type(self, command: str) -> StepType:
        """Detect step type from shell command"""
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

    def _detect_runtime(self, content: str) -> Runtime:
        """Detect runtime from stage content"""
        # Look for agent specification
        agent_match = re.search(r'agent\s*\{(.*?)\}', content, re.DOTALL)
        if agent_match:
            agent_content = agent_match.group(1)
            if 'docker' in agent_content:
                # Try to extract image
                image_match = re.search(r'image\s+[\'"]([^\'"]+)[\'"]', agent_content)
                if image_match:
                    image = image_match.group(1)
                    if 'python' in image:
                        return Runtime(language="python", version="3.11")
                    elif 'node' in image:
                        return Runtime(language="node", version="18")
                    elif 'golang' in image or 'go' in image:
                        return Runtime(language="go", version="1.21")

        return None

    def _parse_environment(self, pipeline_content: str) -> Dict[str, str]:
        """Parse environment variables"""
        env_vars = {}

        # Look for environment block
        env_match = re.search(r'environment\s*\{(.*?)\}', pipeline_content, re.DOTALL)
        if env_match:
            env_content = env_match.group(1)
            # Simple key-value extraction
            env_matches = re.findall(r'(\w+)\s*=\s*[\'"]([^\'"]+)[\'"]', env_content)
            env_vars.update(env_matches)

        return env_vars

    def _parse_post_actions(self, pipeline_content: str) -> List[Stage]:
        """Parse post-build actions as additional stages"""
        stages = []

        post_match = re.search(r'post\s*\{(.*?)\}', pipeline_content, re.DOTALL)
        if post_match:
            post_content = post_match.group(1)

            # Find post conditions
            conditions = ['always', 'success', 'failure', 'unstable', 'changed']
            for condition in conditions:
                condition_match = re.search(f'{condition}\s*{{(.*?)}}', post_content, re.DOTALL)
                if condition_match:
                    condition_content = condition_match.group(1)
                    steps = self._parse_steps(condition_content)
                    if steps:
                        stages.append(Stage(
                            name=f"Post-{condition}",
                            jobs=[Job(
                                name=f"post_{condition}",
                                steps=steps
                            )]
                        ))

        return stages