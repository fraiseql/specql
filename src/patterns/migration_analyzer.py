"""
Migration Analyzer for PrintOptim to SpecQL Patterns

This module provides utilities to analyze existing SpecQL entities and suggest
pattern-based improvements for migration from manual SQL to declarative patterns.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .pattern_loader import PatternLoader


@dataclass
class MigrationSuggestion:
    """A suggestion for migrating to patterns."""

    entity_name: str
    action_name: str
    pattern_type: str
    confidence: float  # 0.0 to 1.0
    description: str
    before_yaml: str
    after_yaml: str
    benefits: List[str]


class MigrationAnalyzer:
    """Analyzes SpecQL entities and suggests pattern migrations."""

    def __init__(self, stdlib_path: Optional[Path] = None):
        """Initialize the migration analyzer."""
        self.pattern_loader = PatternLoader(stdlib_path)

    def analyze_entity(self, entity_path: Path) -> List[MigrationSuggestion]:
        """Analyze a single entity file and suggest migrations."""
        with open(entity_path, "r") as f:
            entity_data = yaml.safe_load(f)

        entity_name = entity_data.get("entity", "Unknown")
        suggestions = []

        # Analyze actions
        actions = entity_data.get("actions", [])
        for action in actions:
            if isinstance(action, dict) and "name" in action:
                action_suggestions = self._analyze_action(entity_name, action)
                suggestions.extend(action_suggestions)

        return suggestions

    def _analyze_action(
        self, entity_name: str, action: Dict[str, Any]
    ) -> List[MigrationSuggestion]:
        """Analyze a single action and suggest pattern migrations."""
        suggestions = []
        action_name = action.get("name", "unknown")

        # Skip if already using patterns
        if "pattern" in action:
            return suggestions

        # Analyze action structure for pattern opportunities
        action.get("config", {})

        # Check for CRUD patterns
        crud_suggestion = self._analyze_crud_pattern(entity_name, action_name, action)
        if crud_suggestion:
            suggestions.append(crud_suggestion)

        # Check for state machine patterns
        state_machine_suggestion = self._analyze_state_machine_pattern(
            entity_name, action_name, action
        )
        if state_machine_suggestion:
            suggestions.append(state_machine_suggestion)

        # Check for validation patterns
        validation_suggestion = self._analyze_validation_pattern(entity_name, action_name, action)
        if validation_suggestion:
            suggestions.append(validation_suggestion)

        # Check for batch patterns
        batch_suggestion = self._analyze_batch_pattern(entity_name, action_name, action)
        if batch_suggestion:
            suggestions.append(batch_suggestion)

        return suggestions

    def _analyze_crud_pattern(
        self, entity_name: str, action_name: str, action: Dict[str, Any]
    ) -> Optional[MigrationSuggestion]:
        """Analyze action for CRUD pattern opportunities."""
        action_config = action.get("config", {})

        # Check for create patterns
        if "create" in action_name.lower():
            if self._has_duplicate_check(action_config):
                return MigrationSuggestion(
                    entity_name=entity_name,
                    action_name=action_name,
                    pattern_type="crud/create",
                    confidence=0.9,
                    description="Convert manual create with duplicate checking to pattern",
                    before_yaml=self._extract_action_yaml(action),
                    after_yaml=self._generate_crud_create_pattern(action_name, action_config),
                    benefits=[
                        "Automatic duplicate detection",
                        "Consistent error handling",
                        "Identifier recalculation",
                        "Projection refresh",
                    ],
                )

        # Check for update patterns
        elif "update" in action_name.lower():
            if self._has_partial_updates(action_config):
                return MigrationSuggestion(
                    entity_name=entity_name,
                    action_name=action_name,
                    pattern_type="crud/update",
                    confidence=0.8,
                    description="Convert manual update to enhanced CRUD pattern",
                    before_yaml=self._extract_action_yaml(action),
                    after_yaml=self._generate_crud_update_pattern(action_name, action_config),
                    benefits=[
                        "Partial updates with CASE expressions",
                        "Field change tracking",
                        "Identifier recalculation",
                        "Projection refresh",
                    ],
                )

        # Check for delete patterns
        elif "delete" in action_name.lower():
            if self._has_dependency_checks(action_config):
                return MigrationSuggestion(
                    entity_name=entity_name,
                    action_name=action_name,
                    pattern_type="crud/delete",
                    confidence=0.8,
                    description="Convert manual delete with dependencies to pattern",
                    before_yaml=self._extract_action_yaml(action),
                    after_yaml=self._generate_crud_delete_pattern(action_name, action_config),
                    benefits=[
                        "Automatic dependency checking",
                        "Hard delete support",
                        "Consistent error messages",
                    ],
                )

        return None

    def _analyze_state_machine_pattern(
        self, entity_name: str, action_name: str, action: Dict[str, Any]
    ) -> Optional[MigrationSuggestion]:
        """Analyze action for state machine pattern opportunities."""
        action_config = action.get("config", {})

        # Look for state transition patterns
        if self._has_state_transition(action_config):
            pattern_type = (
                "state_machine/guarded_transition"
                if self._has_guards(action_config)
                else "state_machine/transition"
            )

            return MigrationSuggestion(
                entity_name=entity_name,
                action_name=action_name,
                pattern_type=pattern_type,
                confidence=0.85,
                description=f"Convert manual state transition to {pattern_type} pattern",
                before_yaml=self._extract_action_yaml(action),
                after_yaml=self._generate_state_machine_pattern(
                    action_name, action_config, pattern_type
                ),
                benefits=[
                    "Declarative state validation",
                    "Automatic side effects",
                    "Consistent error handling",
                    "Audit trail generation",
                ],
            )

        return None

    def _analyze_validation_pattern(
        self, entity_name: str, action_name: str, action: Dict[str, Any]
    ) -> Optional[MigrationSuggestion]:
        """Analyze action for validation pattern opportunities."""
        action_config = action.get("config", {})

        if self._has_validation_chain(action_config):
            return MigrationSuggestion(
                entity_name=entity_name,
                action_name=action_name,
                pattern_type="validation/validation_chain",
                confidence=0.75,
                description="Convert manual validation logic to validation chain pattern",
                before_yaml=self._extract_action_yaml(action),
                after_yaml=self._generate_validation_pattern(action_name, action_config),
                benefits=[
                    "Configurable error handling",
                    "Collect all errors option",
                    "Consistent validation messages",
                    "Reusable validation rules",
                ],
            )

        return None

    def _analyze_batch_pattern(
        self, entity_name: str, action_name: str, action: Dict[str, Any]
    ) -> Optional[MigrationSuggestion]:
        """Analyze action for batch operation pattern opportunities."""
        action_config = action.get("config", {})

        if self._has_batch_operation(action_config):
            return MigrationSuggestion(
                entity_name=entity_name,
                action_name=action_name,
                pattern_type="batch/bulk_operation",
                confidence=0.8,
                description="Convert manual batch processing to bulk operation pattern",
                before_yaml=self._extract_action_yaml(action),
                after_yaml=self._generate_batch_pattern(action_name, action_config),
                benefits=[
                    "Automatic transaction handling",
                    "Configurable error handling",
                    "Progress tracking",
                    "Summary reporting",
                ],
            )

        return None

    # Helper methods to detect pattern opportunities
    def _has_duplicate_check(self, config: Dict[str, Any]) -> bool:
        """Check if config has duplicate checking logic."""
        return "duplicate_check" in config or "unique_check" in config

    def _has_partial_updates(self, config: Dict[str, Any]) -> bool:
        """Check if config has partial update logic."""
        return config.get("partial_updates", False) or "track_changes" in config

    def _has_dependency_checks(self, config: Dict[str, Any]) -> bool:
        """Check if config has dependency checking logic."""
        return "check_dependencies" in config or "dependency_check" in config

    def _has_state_transition(self, config: Dict[str, Any]) -> bool:
        """Check if config has state transition logic."""
        return "from_states" in config or "to_state" in config or "status" in str(config)

    def _has_guards(self, config: Dict[str, Any]) -> bool:
        """Check if config has guard conditions."""
        return "guards" in config or "validation_checks" in config

    def _has_validation_chain(self, config: Dict[str, Any]) -> bool:
        """Check if config has validation chain logic."""
        return "validations" in config or len(config.get("validate", [])) > 1

    def _has_batch_operation(self, config: Dict[str, Any]) -> bool:
        """Check if config has batch operation logic."""
        return "batch_input" in config or "bulk" in str(config).lower()

    # Helper methods to generate pattern YAML
    def _extract_action_yaml(self, action: Dict[str, Any]) -> str:
        """Extract action YAML for before comparison."""
        return yaml.dump(action, default_flow_style=False, indent=2)

    def _generate_crud_create_pattern(self, action_name: str, config: Dict[str, Any]) -> str:
        """Generate CRUD create pattern YAML."""
        pattern_config = {"name": action_name, "pattern": "crud/create", "config": {}}

        if "duplicate_check" in config:
            pattern_config["config"]["duplicate_check"] = config["duplicate_check"]

        return yaml.dump(pattern_config, default_flow_style=False, indent=2)

    def _generate_crud_update_pattern(self, action_name: str, config: Dict[str, Any]) -> str:
        """Generate CRUD update pattern YAML."""
        pattern_config = {
            "name": action_name,
            "pattern": "crud/update",
            "config": {
                "partial_updates": True,
                "track_updated_fields": config.get("track_updated_fields", False),
            },
        }

        return yaml.dump(pattern_config, default_flow_style=False, indent=2)

    def _generate_crud_delete_pattern(self, action_name: str, config: Dict[str, Any]) -> str:
        """Generate CRUD delete pattern YAML."""
        pattern_config = {
            "name": action_name,
            "pattern": "crud/delete",
            "config": {"supports_hard_delete": config.get("supports_hard_delete", False)},
        }

        if "check_dependencies" in config:
            pattern_config["config"]["check_dependencies"] = config["check_dependencies"]

        return yaml.dump(pattern_config, default_flow_style=False, indent=2)

    def _generate_state_machine_pattern(
        self, action_name: str, config: Dict[str, Any], pattern_type: str
    ) -> str:
        """Generate state machine pattern YAML."""
        pattern_config = {"name": action_name, "pattern": pattern_type, "config": {}}

        # Copy relevant config keys
        for key in [
            "from_states",
            "to_state",
            "guards",
            "validation_checks",
            "side_effects",
            "input_fields",
            "refresh_projection",
        ]:
            if key in config:
                pattern_config["config"][key] = config[key]

        return yaml.dump(pattern_config, default_flow_style=False, indent=2)

    def _generate_validation_pattern(self, action_name: str, config: Dict[str, Any]) -> str:
        """Generate validation pattern YAML."""
        pattern_config = {
            "name": action_name,
            "pattern": "validation/validation_chain",
            "config": {},
        }

        if "validations" in config:
            pattern_config["config"]["validations"] = config["validations"]
        if "stop_on_first_failure" in config:
            pattern_config["config"]["stop_on_first_failure"] = config["stop_on_first_failure"]
        if "collect_all_errors" in config:
            pattern_config["config"]["collect_all_errors"] = config["collect_all_errors"]

        return yaml.dump(pattern_config, default_flow_style=False, indent=2)

    def _generate_batch_pattern(self, action_name: str, config: Dict[str, Any]) -> str:
        """Generate batch pattern YAML."""
        pattern_config = {"name": action_name, "pattern": "batch/bulk_operation", "config": {}}

        # Copy relevant config keys
        for key in ["batch_input", "operation", "error_handling", "batch_size", "return_summary"]:
            if key in config:
                pattern_config["config"][key] = config[key]

        return yaml.dump(pattern_config, default_flow_style=False, indent=2)

    def analyze_directory(self, entities_dir: Path) -> List[MigrationSuggestion]:
        """Analyze all entity files in a directory."""
        suggestions = []

        for yaml_file in entities_dir.glob("*.yaml"):
            try:
                file_suggestions = self.analyze_entity(yaml_file)
                suggestions.extend(file_suggestions)
            except Exception as e:
                print(f"Error analyzing {yaml_file}: {e}")

        return suggestions

    def generate_migration_report(self, suggestions: List[MigrationSuggestion]) -> str:
        """Generate a comprehensive migration report."""
        report = ["# SpecQL Pattern Migration Report\n"]
        report.append(f"Found {len(suggestions)} migration opportunities\n")

        # Group by pattern type
        by_pattern = {}
        for suggestion in suggestions:
            pattern = suggestion.pattern_type
            if pattern not in by_pattern:
                by_pattern[pattern] = []
            by_pattern[pattern].append(suggestion)

        # Generate report sections
        for pattern_type, pattern_suggestions in by_pattern.items():
            report.append(f"## {pattern_type} ({len(pattern_suggestions)} suggestions)\n")

            for suggestion in pattern_suggestions:
                confidence_pct = int(suggestion.confidence * 100)
                report.append(f"### {suggestion.entity_name}.{suggestion.action_name}")
                report.append(f"**Confidence**: {confidence_pct}%")
                report.append(f"**Description**: {suggestion.description}")
                report.append("**Benefits**:")
                for benefit in suggestion.benefits:
                    report.append(f"- {benefit}")
                report.append("")
                report.append("**After (Pattern-based)**:")
                report.append("```yaml")
                report.append(suggestion.after_yaml.rstrip())
                report.append("```")
                report.append("")

        # Summary statistics
        total_actions = len(set((s.entity_name, s.action_name) for s in suggestions))
        (
            sum(s.confidence for s in suggestions) / len(suggestions) if suggestions else 0
        )

        report.append("## Migration Summary\n")
        report.append(f"- **Total Actions Analyzed**: {total_actions}")
        report.append(f"- **Migration Opportunities**: {len(suggestions)}")
        report.append(".1f")
        report.append(
            f"- **Estimated Effort**: {len(suggestions) * 30} minutes (30min per migration)"
        )

        return "\n".join(report)
