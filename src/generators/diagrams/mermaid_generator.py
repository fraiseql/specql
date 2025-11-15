from typing import Optional
from pathlib import Path

from src.generators.diagrams.relationship_extractor import (
    RelationshipExtractor
)

class MermaidGenerator:
    """
    Generate Mermaid ER diagrams

    Mermaid format is embeddable in Markdown:
    ```mermaid
    erDiagram
        CONTACT ||--o{ ORDER : places
        CONTACT {
            uuid id
            text email
        }
    ```

    Features:
    - ERD syntax
    - Relationship notation
    - Field lists
    - Comments
    """

    def __init__(self, extractor: RelationshipExtractor):
        self.extractor = extractor

    def generate(
        self,
        output_path: Optional[str] = None,
        title: Optional[str] = None,
        show_fields: bool = True,
        show_trinity: bool = False,
    ) -> str:
        """
        Generate Mermaid ERD

        Args:
            output_path: Path to save Markdown file (if None, returns string)
            title: Diagram title
            show_fields: Show field lists
            show_trinity: Show Trinity pattern fields

        Returns:
            Mermaid diagram string

        Raises:
            RuntimeError: If diagram generation fails
        """
        if not self.extractor.entities:
            raise ValueError("No entities found in extractor. Run extract_from_entities() first.")

        try:
            lines = []

            # Title
            if title:
                lines.append(f"# {title}\n")

            # Start Mermaid block
            lines.append("```mermaid")
            lines.append("erDiagram")

            # Relationships
            for rel in self.extractor.relationships:
                notation = self._get_mermaid_notation(rel)
                lines.append(f"    {rel.from_entity} {notation} {rel.to_entity} : \"{rel.from_field}\"")

            # Entity definitions (if showing fields)
            if show_fields:
                lines.append("")
                for entity_name, entity_node in self.extractor.entities.items():
                    lines.append(f"    {entity_name} {{")

                    for field in entity_node.fields:
                        field_name = field['name']

                        # Skip Trinity if not showing
                        if not show_trinity and field_name in ['pk_' + entity_name.lower(), 'id', 'identifier']:
                            continue

                        field_type = field['type'].lower()
                        pk_marker = ' PK' if field.get('is_pk') else ''
                        fk_marker = ' FK' if field.get('is_fk') else ''

                        lines.append(f"        {field_type} {field_name}{pk_marker}{fk_marker}")

                    lines.append("    }")

            # End Mermaid block
            lines.append("```")

            mermaid_source = '\n'.join(lines)

            # Save if path provided
            if output_path:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                Path(output_path).write_text(mermaid_source)

            return mermaid_source

        except Exception as e:
            raise RuntimeError(f"Failed to generate Mermaid diagram: {e}") from e

    def _get_mermaid_notation(self, rel) -> str:
        """
        Get Mermaid relationship notation

        Mermaid ERD syntax:
        ||--||  one-to-one
        ||--o{  one-to-many
        }o--o{  many-to-many
        ||--o|  one-to-zero-or-one
        """
        if rel.nullable:
            # Optional relationship
            return "||--o{"
        else:
            # Required relationship
            return "||--||"