"""
SpecQL YAML Generator

Generates SpecQL YAML from UniversalEntity with organization metadata support.
"""

from datetime import datetime
from src.core.yaml_serializer import YAMLSerializer
from src.core.universal_ast import UniversalEntity


class SpecQLGenerator:
    """Generate SpecQL YAML from UniversalEntity"""

    def __init__(self):
        self.serializer = YAMLSerializer()

    def generate_yaml(self, entity: UniversalEntity) -> str:
        """Generate YAML with organization metadata"""

        yaml_dict = self.serializer._entity_to_dict(entity)

        # Add description if present
        if entity.description:
            yaml_dict["description"] = entity.description

        # Add organization metadata (NEW)
        if entity.organization:
            yaml_dict["organization"] = entity.organization

        # Add metadata section
        yaml_dict["_metadata"] = {
            "source": "reverse-schema",
            "generated_at": datetime.now().isoformat(),
            "original_schema": entity.schema,
            "original_table": f"{entity.schema}.{entity.name.lower()}",
        }

        # Use serializer to dump to YAML
        import yaml

        return yaml.dump(
            yaml_dict, default_flow_style=False, sort_keys=False, allow_unicode=True
        )
