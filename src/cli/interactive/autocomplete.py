"""
Context-aware auto-completion for SpecQL YAML

Provides intelligent suggestions based on current cursor position
and SpecQL syntax rules.
"""

from dataclasses import dataclass
from typing import List
from enum import Enum


class CompletionType(Enum):
    """Type of completion suggestion"""
    KEYWORD = "keyword"
    FIELD_TYPE = "field_type"
    PATTERN = "pattern"
    ENTITY_REFERENCE = "entity_reference"
    STEP_TYPE = "step_type"
    SNIPPET = "snippet"


@dataclass
class Completion:
    """Auto-completion suggestion"""
    text: str
    type: CompletionType
    description: str
    insert_text: str  # Text to insert (may include template)
    score: float = 1.0  # Relevance score


class AutoCompleter:
    """
    Context-aware auto-completion for SpecQL YAML

    Features:
    - Field type suggestions
    - Pattern snippets
    - Entity references
    - Action step templates
    """

    def __init__(self):
        self.field_types = [
            'text', 'integer', 'float', 'boolean',
            'date', 'timestamp', 'uuid', 'json',
            'enum', 'ref', 'list'
        ]

        self.step_types = [
            'validate', 'if', 'update', 'insert',
            'delete', 'call', 'notify', 'foreach', 'return'
        ]

        self.patterns = [
            'audit_trail', 'soft_delete', 'state_machine',
            'multi_tenant', 'versioning', 'archival'
        ]

    def get_completions(
        self,
        current_line: str,
        full_text: str,
        cursor_position: int
    ) -> List[Completion]:
        """
        Get completions for current cursor position

        Args:
            current_line: Line where cursor is
            full_text: Complete YAML text
            cursor_position: Cursor position in full text

        Returns:
            List of completion suggestions
        """
        context = self._determine_context(current_line, full_text)

        if context == "field_definition":
            return self._field_type_completions()

        elif context == "action_step":
            return self._step_type_completions()

        elif context == "pattern":
            return self._pattern_completions()

        elif context == "entity_level":
            return self._entity_keyword_completions()

        else:
            return self._general_completions()

    def _determine_context(self, current_line: str, full_text: str) -> str:
        """Determine completion context from current position"""
        stripped = current_line.strip()

        # In fields section?
        if 'fields:' in full_text:
            lines_before = full_text[:full_text.rfind(current_line)].split('\n')
            in_fields = False
            for line in reversed(lines_before):
                if line.strip() == 'fields:':
                    in_fields = True
                    break
                elif line.strip() in ['actions:', 'views:']:
                    break

            if in_fields and ':' in stripped:
                return "field_definition"

        # In actions section?
        if 'actions:' in full_text and 'steps:' in full_text:
            if stripped.startswith('-'):
                return "action_step"

        # At entity level?
        if not stripped or stripped.endswith(':'):
            return "entity_level"

        return "general"

    def _field_type_completions(self) -> List[Completion]:
        """Completions for field types"""
        completions = []

        # Simple types
        for field_type in self.field_types:
            if field_type in ['text', 'integer', 'boolean', 'date']:
                completions.append(Completion(
                    text=field_type,
                    type=CompletionType.FIELD_TYPE,
                    description=f"{field_type.capitalize()} field",
                    insert_text=field_type,
                    score=1.0
                ))

        # Enum with template
        completions.append(Completion(
            text="enum",
            type=CompletionType.SNIPPET,
            description="Enum field with values",
            insert_text="""enum
    values: [value1, value2, value3]""",
            score=0.9
        ))

        # Ref with template
        completions.append(Completion(
            text="ref",
            type=CompletionType.SNIPPET,
            description="Reference to another entity",
            insert_text="ref(EntityName)",
            score=0.9
        ))

        return completions

    def _step_type_completions(self) -> List[Completion]:
        """Completions for action steps"""
        completions = []

        # Validate step
        completions.append(Completion(
            text="validate",
            type=CompletionType.SNIPPET,
            description="Validation step",
            insert_text="validate: field = 'value'",
            score=1.0
        ))

        # Update step
        completions.append(Completion(
            text="update",
            type=CompletionType.SNIPPET,
            description="Update entity field",
            insert_text="update: EntityName SET field = 'value'",
            score=1.0
        ))

        # Insert step
        completions.append(Completion(
            text="insert",
            type=CompletionType.SNIPPET,
            description="Insert new record",
            insert_text="""insert:
          entity: EntityName
          fields:
            field1: value1
            field2: value2""",
            score=0.9
        ))

        # If/then/else
        completions.append(Completion(
            text="if",
            type=CompletionType.SNIPPET,
            description="Conditional logic",
            insert_text="""if: condition
          then:
            - step1
          else:
            - step2""",
            score=0.9
        ))

        return completions

    def _pattern_completions(self) -> List[Completion]:
        """Completions for pattern application"""
        completions = []

        # Audit trail pattern
        completions.append(Completion(
            text="audit_trail",
            type=CompletionType.PATTERN,
            description="Add created_at, updated_at, created_by, updated_by",
            insert_text="""patterns:
  - audit_trail

# Adds fields:
# created_at: timestamp
# updated_at: timestamp
# created_by: text
# updated_by: text""",
            score=1.0
        ))

        # Soft delete pattern
        completions.append(Completion(
            text="soft_delete",
            type=CompletionType.PATTERN,
            description="Add deleted_at field for soft deletion",
            insert_text="""patterns:
  - soft_delete

# Adds field:
# deleted_at: timestamp""",
            score=1.0
        ))

        return completions

    def _entity_keyword_completions(self) -> List[Completion]:
        """Completions for entity-level keywords"""
        return [
            Completion(
                text="entity",
                type=CompletionType.KEYWORD,
                description="Entity name",
                insert_text="entity: EntityName",
                score=1.0
            ),
            Completion(
                text="schema",
                type=CompletionType.KEYWORD,
                description="Database schema",
                insert_text="schema: schema_name",
                score=1.0
            ),
            Completion(
                text="fields",
                type=CompletionType.KEYWORD,
                description="Entity fields",
                insert_text="""fields:
  field_name: text""",
                score=1.0
            ),
            Completion(
                text="actions",
                type=CompletionType.KEYWORD,
                description="Entity actions",
                insert_text="""actions:
  - name: action_name
    steps:
      - validate: condition""",
                score=1.0
            ),
        ]

    def _general_completions(self) -> List[Completion]:
        """General completions (fallback)"""
        return self._field_type_completions() + self._entity_keyword_completions()