# Project configuration for SpecQL
"""Project-level configuration for SpecQL projects."""

from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from reverse_engineering.table_parser import ParsedTable


@dataclass
class SchemaConfig:
    """Configuration for a PostgreSQL schema."""

    name: str
    description: str = ""
    multi_tenant: bool = False


@dataclass
class ProjectConfig:
    """Project-level configuration for SpecQL."""

    version: str = "1.0"
    name: str = ""
    description: str = ""
    schemas: list[SchemaConfig] = field(default_factory=list)
    extensions: list[str] = field(default_factory=lambda: ["uuid-ossp"])
    registry_enabled: bool = False
    registry_path: str = "registry/domain_registry.yaml"
    output_format: str = "confiture"
    trinity_pattern: bool = True
    audit_fields: bool = True
    soft_delete: bool = True

    @classmethod
    def from_yaml(cls, path: Path) -> "ProjectConfig":
        """Load project config from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)

        # Handle nested structure
        if "settings" in data:
            settings = data.pop("settings")
            data.update(settings)

        # Convert schema dicts to SchemaConfig objects
        if "schemas" in data and data["schemas"]:
            data["schemas"] = [SchemaConfig(**schema) for schema in data["schemas"]]

        # Remove metadata if present
        data.pop("_metadata", None)

        return cls(**data)

    def to_yaml(self) -> str:
        """Serialize project config to YAML."""
        # Convert to dict for YAML serialization
        data = {
            "version": self.version,
            "name": self.name,
            "description": self.description,
            "schemas": [
                {
                    "name": schema.name,
                    "description": schema.description,
                    "multi_tenant": schema.multi_tenant,
                }
                for schema in self.schemas
            ],
            "extensions": self.extensions,
            "settings": {
                "output_format": self.output_format,
                "trinity_pattern": self.trinity_pattern,
                "audit_fields": self.audit_fields,
                "soft_delete": self.soft_delete,
            },
            "_metadata": {
                "generated_at": datetime.now().isoformat(),
                "generated_by": "specql-reverse-sql",
            },
        }
        return yaml.dump(data, default_flow_style=False, sort_keys=False)

    def generate_registry_yaml(self) -> str:
        """Generate a basic domain registry from the project config."""
        from datetime import datetime

        # Create a simple registry structure based on schemas
        registry = {
            "last_updated": datetime.now().isoformat(),
            "schema_layers": {
                "00": "common",
                "01": "write_side",
                "02": "read_side",
            },
            "domains": {},
        }

        # Group schemas into domains
        domain_counter = 1
        for schema in self.schemas:
            domain_key = str(domain_counter)
            registry["domains"][domain_key] = {
                "name": schema.name,
                "description": schema.description,
                "multi_tenant": schema.multi_tenant,
                "subdomains": {
                    "01": {
                        "name": "core",
                        "description": f"Core {schema.name} entities",
                        "next_entity_sequence": 1,
                        "entities": {},
                    }
                },
            }
            domain_counter += 1

        return yaml.dump(registry, default_flow_style=False, sort_keys=False)

    @classmethod
    def from_reverse_engineering(
        cls, parsed_tables: list["ParsedTable"], source_path: str
    ) -> "ProjectConfig":
        """Create ProjectConfig from reverse-engineered tables."""
        # Extract unique schemas
        schemas = {}
        extensions = set(["uuid-ossp"])  # Default extension

        for table in parsed_tables:
            if table.schema and table.schema not in schemas:
                # Determine if schema is multi-tenant based on naming patterns
                is_multi_tenant = table.schema.lower() in ["tenant", "client", "organization"]
                description = f"Schema containing {table.table_name} and related entities"

                schemas[table.schema] = SchemaConfig(
                    name=table.schema,
                    description=description,
                    multi_tenant=is_multi_tenant,
                )

            # Detect extensions based on column types and defaults
            for column in table.columns:
                # Check for UUID generation functions
                if column.default and "gen_random_uuid" in column.default:
                    extensions.add("uuid-ossp")
                # Check for cryptographic functions
                if column.default and ("crypt(" in column.default or "gen_salt(" in column.default):
                    extensions.add("pgcrypto")
                # Check for fuzzy text search (trigrams)
                if column.specql_type.lower().startswith("text") and "similarity(" in str(
                    column.default or ""
                ):
                    extensions.add("pg_trgm")
                # Check for UUID type usage
                if "uuid" in column.specql_type.lower():
                    extensions.add("uuid-ossp")
                # Check for array types
                if column.specql_type.endswith("[]"):
                    extensions.add("intarray")  # For array operations

        # Extract project name from source path
        source_name = Path(source_path).stem
        if source_name.startswith("db") or source_name.startswith("database"):
            project_name = source_name
        else:
            project_name = f"{source_name}_project"

        return cls(
            name=project_name,
            description=f"Reverse-engineered from {source_path}",
            schemas=list(schemas.values()),
            extensions=sorted(list(extensions)),
        )
