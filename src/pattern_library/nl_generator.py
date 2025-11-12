"""Natural Language Pattern Generator using Grok LLM."""

import json
import re
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import os

from src.reverse_engineering.grok_provider import GrokProvider


class NLPatternGenerator:
    """
    Generate SpecQL patterns from natural language descriptions using Grok LLM.

    Features:
    - Converts NL descriptions to structured patterns
    - Validates generated patterns against SpecQL conventions
    - Scores pattern quality and confidence
    - Stores generated patterns in PostgreSQL
    """

    def __init__(self, log_to_db: bool = True):
        """
        Initialize NL pattern generator.

        Args:
            log_to_db: Whether to log Grok calls to PostgreSQL
        """
        self.grok = GrokProvider(log_to_db=log_to_db)
        self.template_path = Path(__file__).parent.parent / "reverse_engineering" / "prompts" / "nl_pattern_generation.jinja2"

        # Load template
        if self.template_path.exists():
            with open(self.template_path, 'r') as f:
                self.template = f.read()
        else:
            raise FileNotFoundError(f"Template not found: {self.template_path}")

        print("✓ NL Pattern Generator ready (Grok-powered)")

    def generate(
        self,
        description: str,
        category: Optional[str] = None,
        max_retries: int = 3
    ) -> Tuple[Dict[str, Any], float, str]:
        """
        Generate a SpecQL pattern from natural language description.

        Args:
            description: Natural language description of the pattern
            category: Optional category hint (workflow, validation, etc.)
            max_retries: Maximum retries for generation/validation

        Returns:
            Tuple of (pattern_dict, confidence_score, validation_message)
        """
        for attempt in range(max_retries):
            try:
                # Generate pattern using Grok
                pattern = self._generate_with_grok(description, category)

                # Validate pattern
                is_valid, validation_msg = self._validate_pattern(pattern)

                if is_valid:
                    # Score confidence
                    confidence = self._score_confidence(pattern, description)
                    return pattern, confidence, validation_msg

                # If invalid, retry with more specific instructions
                if attempt < max_retries - 1:
                    description = f"{description}\n\nPrevious attempt failed: {validation_msg}\nPlease fix these issues and generate a valid SpecQL pattern."

            except Exception as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Failed to generate pattern after {max_retries} attempts: {e}")
                continue

        raise RuntimeError(f"Failed to generate valid pattern after {max_retries} attempts")

    def _generate_with_grok(self, description: str, category: Optional[str] = None) -> Dict[str, Any]:
        """Generate pattern using Grok LLM."""
        # Prepare prompt
        prompt = self.template.replace("{{ description }}", description)
        if category:
            prompt = prompt.replace("{{ category }}", category)
        else:
            prompt = prompt.replace("Category: {{ category }}", "Category: (choose appropriate)")

        # Call Grok
        response = self.grok.call_json(prompt, task_type="pattern_generation")

        return response

    def _validate_pattern(self, pattern: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate generated pattern against SpecQL conventions.

        Returns:
            Tuple of (is_valid, validation_message)
        """
        errors = []

        # Required fields
        required_fields = ['name', 'category', 'description', 'parameters', 'implementation']
        for field in required_fields:
            if field not in pattern:
                errors.append(f"Missing required field: {field}")

        if errors:
            return False, f"Missing fields: {', '.join(errors)}"

        # Validate name (snake_case, no spaces)
        name = pattern.get('name', '')
        if not re.match(r'^[a-z][a-z0-9_]*$', name):
            errors.append("Pattern name must be snake_case (lowercase, underscores only)")

        # Validate category
        valid_categories = {
            'workflow', 'validation', 'audit', 'hierarchy', 'state_machine',
            'approval', 'notification', 'calculation', 'soft_delete', 'security'
        }
        category = pattern.get('category', '')
        if category not in valid_categories:
            errors.append(f"Invalid category '{category}'. Must be one of: {', '.join(valid_categories)}")

        # Validate parameters structure
        parameters = pattern.get('parameters', {})
        if not isinstance(parameters, dict):
            errors.append("Parameters must be a JSON object")
        else:
            # Check for entity parameter (required for most patterns)
            if 'entity' not in parameters:
                errors.append("Parameters must include 'entity' field")

        # Validate implementation structure
        implementation = pattern.get('implementation', {})
        if not isinstance(implementation, dict):
            errors.append("Implementation must be a JSON object")

        # Check for fields or actions
        has_fields = 'fields' in implementation and isinstance(implementation['fields'], list)
        has_actions = 'actions' in implementation and isinstance(implementation['actions'], list)

        if not has_fields and not has_actions:
            errors.append("Implementation must include either 'fields' or 'actions' (or both)")

        # Validate fields structure
        if has_fields:
            for i, field in enumerate(implementation['fields']):
                if not isinstance(field, dict):
                    errors.append(f"Field {i} must be a JSON object")
                    continue

                required_field_props = ['name', 'type']
                for prop in required_field_props:
                    if prop not in field:
                        errors.append(f"Field {i} missing required property: {prop}")

                # Validate field name (snake_case)
                field_name = field.get('name', '')
                if not re.match(r'^[a-z][a-z0-9_]*$', field_name):
                    errors.append(f"Field name '{field_name}' must be snake_case")

        # Validate actions structure
        if has_actions:
            for i, action in enumerate(implementation['actions']):
                if not isinstance(action, dict):
                    errors.append(f"Action {i} must be a JSON object")
                    continue

                if 'name' not in action:
                    errors.append(f"Action {i} missing required property: name")

                if 'steps' in action:
                    if not isinstance(action['steps'], list):
                        errors.append(f"Action {i} steps must be a list")
                    else:
                        for j, step in enumerate(action['steps']):
                            if not isinstance(step, dict):
                                errors.append(f"Action {i} step {j} must be a JSON object")

        # Check for SpecQL conventions
        if has_fields:
            field_names = [f.get('name', '') for f in implementation['fields']]

            # Check for trinity pattern (at least pk_*, id, identifier should be mentioned)
            has_pk = any('pk_' in name for name in field_names)
            has_id = 'id' in field_names
            has_identifier = 'identifier' in field_names

            if not (has_pk or has_id or has_identifier):
                errors.append("Consider adding SpecQL trinity fields: pk_*, id, identifier")

            # Check for audit fields
            audit_fields = ['created_at', 'updated_at', 'deleted_at']
            has_audit = any(field in field_names for field in audit_fields)
            if not has_audit:
                errors.append("Consider adding audit fields: created_at, updated_at, deleted_at")

        if errors:
            return False, f"Validation errors: {'; '.join(errors)}"

        return True, "Pattern validation passed"

    def _score_confidence(self, pattern: Dict[str, Any], original_description: str) -> float:
        """
        Score the confidence/quality of the generated pattern.

        Returns:
            Float between 0.0 and 1.0
        """
        score = 0.0
        max_score = 0.0

        # Structure completeness (20 points)
        max_score += 20
        if all(key in pattern for key in ['name', 'category', 'description', 'parameters', 'implementation']):
            score += 20

        # Parameter quality (15 points)
        max_score += 15
        parameters = pattern.get('parameters', {})
        if isinstance(parameters, dict) and len(parameters) > 0:
            score += 10  # Has parameters
            if 'entity' in parameters:
                score += 5  # Has entity parameter

        # Implementation quality (25 points)
        max_score += 25
        implementation = pattern.get('implementation', {})
        if isinstance(implementation, dict):
            has_fields = 'fields' in implementation and len(implementation['fields']) > 0
            has_actions = 'actions' in implementation and len(implementation['actions']) > 0

            if has_fields:
                score += 10
            if has_actions:
                score += 10
            if has_fields and has_actions:
                score += 5  # Bonus for complete implementation

        # Convention compliance (20 points)
        max_score += 20
        implementation = pattern.get('implementation', {})
        if 'fields' in implementation:
            field_names = [f.get('name', '') for f in implementation['fields']]

            # Trinity pattern
            has_pk = any('pk_' in name for name in field_names)
            has_id = 'id' in field_names
            has_identifier = 'identifier' in field_names

            trinity_score = (has_pk + has_id + has_identifier) / 3.0 * 8
            score += trinity_score

            # Audit fields
            audit_fields = ['created_at', 'updated_at', 'deleted_at']
            audit_present = sum(1 for field in audit_fields if field in field_names)
            score += (audit_present / 3.0) * 7

            # Naming conventions
            valid_names = sum(1 for name in field_names if re.match(r'^[a-z][a-z0-9_]*$', name))
            if field_names:
                naming_score = (valid_names / len(field_names)) * 5
                score += naming_score

        # Description relevance (20 points)
        max_score += 20
        pattern_desc = pattern.get('description', '').lower()
        orig_desc = original_description.lower()

        # Simple keyword matching
        desc_words = set(re.findall(r'\b\w+\b', orig_desc))
        pattern_words = set(re.findall(r'\b\w+\b', pattern_desc))

        overlap = len(desc_words.intersection(pattern_words))
        total_words = len(desc_words.union(pattern_words))

        if total_words > 0:
            relevance = overlap / total_words
            score += relevance * 20

        # Calculate final score
        final_score = score / max_score if max_score > 0 else 0.0

        # Ensure bounds
        return max(0.0, min(1.0, final_score))

    def save_pattern(self, pattern: Dict[str, Any], confidence: float) -> int:
        """
        Save generated pattern to PostgreSQL database.

        Returns:
            Pattern ID
        """
        import psycopg

        conn_string = os.getenv('SPECQL_DB_URL')
        if not conn_string:
            raise ValueError("SPECQL_DB_URL environment variable not set")

        with psycopg.connect(conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO pattern_library.domain_patterns
                    (name, category, description, parameters, implementation, source_type, complexity_score)
                    VALUES (%s, %s, %s, %s, %s, 'llm_generated', %s)
                    RETURNING id
                    """,
                    (
                        pattern['name'],
                        pattern['category'],
                        pattern['description'],
                        json.dumps(pattern.get('parameters', {})),
                        json.dumps(pattern.get('implementation', {})),
                        confidence
                    )
                )

                result = cursor.fetchone()
                if result is None:
                    raise RuntimeError("Failed to insert pattern - no ID returned")

                pattern_id = result[0]
                conn.commit()

                return pattern_id

    def close(self):
        """Close Grok provider connection."""
        self.grok.close()