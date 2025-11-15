"""
PatternLibrary API for database-driven code generation

Usage:
    # Using repository pattern (recommended)
    from src.infrastructure.repositories.sqlite_pattern_repository import SQLitePatternRepository
    from src.application.services.pattern_service import PatternService

    repo = SQLitePatternRepository("pattern_library.db")
    service = PatternService(repo)
    library = PatternLibrary(service)

    # Legacy direct usage (deprecated)
    library = PatternLibrary(db_path="pattern_library.db")

    # Add pattern
    library.add_pattern(
        name="declare",
        category="primitive",
        abstract_syntax={...}
    )

    # Add implementation
    library.add_implementation(
        pattern_name="declare",
        language_name="postgresql",
        template="..."
    )

    # Compile
    code = library.compile_pattern(
        pattern_name="declare",
        language_name="postgresql",
        context={...}
    )
"""

import sqlite3
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from functools import lru_cache
from jinja2 import Template

if TYPE_CHECKING:
    from src.application.services.pattern_service import PatternService


class PatternLibrary:
    """Database-driven pattern library for multi-language code generation"""

    def __init__(self, pattern_service: Optional["PatternService"] = None, db_path: str = "pattern_library.db"):
        """
        Initialize pattern library

        Args:
            pattern_service: PatternService instance (uses repository pattern)
            db_path: Path to SQLite database (legacy, for backward compatibility)
        """
        if pattern_service:
            # New repository-based approach
            self.pattern_service = pattern_service
            self.db_path = None
            self.db = None
            self._legacy_mode = False
        else:
            # Legacy direct database access (deprecated)
            self.pattern_service = None
            self.db_path = db_path
            self.db = sqlite3.connect(db_path)
            self.db.row_factory = sqlite3.Row  # Return rows as dicts
            self._initialize_schema()
            self._legacy_mode = True

    def _initialize_schema(self):
        """Create database schema if not exists"""
        schema_path = Path(__file__).parent / "schema.sql"

        if not schema_path.exists():
            # For testing, allow empty initialization
            return

        # Check if tables already exist
        cursor = self.db.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='patterns'
        """)
        if cursor.fetchone():
            # Schema already exists, skip initialization
            return

        with open(schema_path) as f:
            self.db.executescript(f.read())

        self.db.commit()

    # ===== Pattern Management =====

    def add_pattern(
        self,
        name: str,
        category: str,
        abstract_syntax: Dict[str, Any],
        description: str = "",
        complexity_score: int = 1
    ) -> int:
        """Add a pattern to the library"""
        if self.pattern_service:
            # Use repository pattern
            pattern = self.pattern_service.create_pattern(
                name=name,
                category=category,
                description=description,
                parameters=abstract_syntax,
                complexity_score=float(complexity_score),
                source_type="manual"
            )
            return pattern.id or 0
        else:
            # Legacy direct database access
            cursor = self.db.execute(
                """
                INSERT INTO patterns (pattern_name, pattern_category, abstract_syntax, description, complexity_score)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, category, json.dumps(abstract_syntax), description, complexity_score)
            )
            self.db.commit()
            return cursor.lastrowid or 0

    @lru_cache(maxsize=128)
    def get_pattern(self, name: str) -> Optional[Dict[str, Any]]:
        """Get pattern by name"""
        cursor = self.db.execute(
            "SELECT * FROM patterns WHERE pattern_name = ?",
            (name,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_patterns(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all patterns, optionally filtered by category"""
        if category:
            cursor = self.db.execute(
                "SELECT * FROM patterns WHERE pattern_category = ? ORDER BY pattern_name",
                (category,)
            )
        else:
            cursor = self.db.execute("SELECT * FROM patterns ORDER BY pattern_name")

        return [dict(row) for row in cursor.fetchall()]

    # ===== Language Management =====

    def add_language(
        self,
        name: str,
        ecosystem: str,
        paradigm: str,
        version: str = "",
        supported: bool = True
    ) -> int:
        """Add a target language"""
        cursor = self.db.execute(
            """
            INSERT INTO languages (language_name, ecosystem, paradigm, version, supported)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, ecosystem, paradigm, version, supported)
        )
        self.db.commit()
        return cursor.lastrowid or 0

    @lru_cache(maxsize=32)
    def get_language(self, name: str) -> Optional[Dict[str, Any]]:
        """Get language by name"""
        cursor = self.db.execute(
            "SELECT * FROM languages WHERE language_name = ?",
            (name,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_languages(self, supported_only: bool = True) -> List[Dict[str, Any]]:
        """Get all languages"""
        if supported_only:
            cursor = self.db.execute(
                "SELECT * FROM languages WHERE supported = TRUE ORDER BY language_name"
            )
        else:
            cursor = self.db.execute("SELECT * FROM languages ORDER BY language_name")

        return [dict(row) for row in cursor.fetchall()]

    # ===== Implementation Management =====

    def add_implementation(
        self,
        pattern_name: str,
        language_name: str,
        template: str,
        supported: bool = True,
        version: str = "1.0.0"
    ) -> int:
        """Add pattern implementation for a language"""

        # Get IDs
        pattern = self.get_pattern(pattern_name)
        language = self.get_language(language_name)

        if not pattern:
            raise ValueError(f"Pattern not found: {pattern_name}")
        if not language:
            raise ValueError(f"Language not found: {language_name}")

        cursor = self.db.execute(
            """
            INSERT INTO pattern_implementations
            (pattern_id, language_id, implementation_template, supported, version)
            VALUES (?, ?, ?, ?, ?)
            """,
            (pattern["pattern_id"], language["language_id"], template, supported, version)
        )
        self.db.commit()
        return cursor.lastrowid or 0

    def add_or_update_implementation(
        self,
        pattern_name: str,
        language_name: str,
        template: str,
        supported: bool = True,
        version: str = "1.0.0"
    ) -> int:
        """Add or update pattern implementation for a language"""
        existing = self.get_implementation(pattern_name, language_name)
        if existing:
            # Update existing implementation
            self.db.execute(
                "UPDATE pattern_implementations SET implementation_template = ?, supported = ?, version = ? WHERE implementation_id = ?",
                (template, supported, version, existing["implementation_id"])
            )
            self.db.commit()
            return existing["implementation_id"]
        else:
            # Add new implementation
            return self.add_implementation(pattern_name, language_name, template, supported, version)

    @lru_cache(maxsize=256)
    def get_implementation(
        self,
        pattern_name: str,
        language_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get implementation for pattern + language"""
        cursor = self.db.execute(
            """
            SELECT pi.*
            FROM pattern_implementations pi
            JOIN patterns p ON pi.pattern_id = p.pattern_id
            JOIN languages l ON pi.language_id = l.language_id
            WHERE p.pattern_name = ? AND l.language_name = ?
            """,
            (pattern_name, language_name)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    # ===== Compilation =====

    def compile_pattern(
        self,
        pattern_name: str,
        language_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Compile a pattern to target language code

        Args:
            pattern_name: Name of pattern to compile
            language_name: Target language
            context: Variables to inject into template

        Returns:
            Generated code string

        Raises:
            ValueError: If pattern or implementation not found
        """
        impl = self.get_implementation(pattern_name, language_name)

        if not impl:
            raise ValueError(
                f"No implementation found for pattern '{pattern_name}' in language '{language_name}'"
            )

        template = Template(impl["implementation_template"])
        return template.render(**context)

    # ===== Type Management =====

    def add_universal_type(
        self,
        type_name: str,
        type_category: str,
        description: str = "",
        json_schema: Optional[Dict] = None
    ) -> int:
        """Add universal type to library"""
        cursor = self.db.execute(
            """
            INSERT INTO universal_types (type_name, type_category, description, json_schema)
            VALUES (?, ?, ?, ?)
            """,
            (type_name, type_category, description, json.dumps(json_schema) if json_schema else None)
        )
        self.db.commit()
        return cursor.lastrowid or 0

    def add_type_mapping(
        self,
        universal_type_name: str,
        language_name: str,
        language_type: str,
        import_statement: Optional[str] = None
    ) -> int:
        """Map universal type to language-specific type"""

        # Get IDs
        cursor = self.db.execute(
            "SELECT type_id FROM universal_types WHERE type_name = ?",
            (universal_type_name,)
        )
        type_row = cursor.fetchone()
        if not type_row:
            raise ValueError(f"Universal type not found: {universal_type_name}")

        language = self.get_language(language_name)
        if not language:
            raise ValueError(f"Language not found: {language_name}")

        cursor = self.db.execute(
            """
            INSERT INTO type_mappings (universal_type_id, language_id, language_type, import_statement)
            VALUES (?, ?, ?, ?)
            """,
            (type_row["type_id"], language["language_id"], language_type, import_statement)
        )
        self.db.commit()
        return cursor.lastrowid or 0

    def get_type_mapping(
        self,
        universal_type_name: str,
        language_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get type mapping for universal type in target language"""
        cursor = self.db.execute(
            """
            SELECT tm.*, ut.type_name, l.language_name
            FROM type_mappings tm
            JOIN universal_types ut ON tm.universal_type_id = ut.type_id
            JOIN languages l ON tm.language_id = l.language_id
            WHERE ut.type_name = ? AND l.language_name = ?
            """,
            (universal_type_name, language_name)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    # ===== Batch Operations =====

    def batch_add_patterns(self, patterns: List[Dict[str, Any]]) -> List[int]:
        """Batch insert multiple patterns"""
        ids = []
        for pattern in patterns:
            pattern_id = self.add_pattern(
                name=pattern["name"],
                category=pattern["category"],
                abstract_syntax=pattern["abstract_syntax"],
                description=pattern.get("description", ""),
                complexity_score=pattern.get("complexity_score", 1)
            )
            ids.append(pattern_id)
        return ids

    def batch_add_languages(self, languages: List[Dict[str, Any]]) -> List[int]:
        """Batch insert multiple languages"""
        ids = []
        for language in languages:
            lang_id = self.add_language(
                name=language["name"],
                ecosystem=language["ecosystem"],
                paradigm=language["paradigm"],
                version=language.get("version", ""),
                supported=language.get("supported", True)
            )
            ids.append(lang_id)
        return ids

    def batch_add_implementations(self, implementations: List[Dict[str, Any]]) -> List[int]:
        """Batch insert multiple pattern implementations"""
        ids = []
        for impl in implementations:
            impl_id = self.add_implementation(
                pattern_name=impl["pattern_name"],
                language_name=impl["language_name"],
                template=impl["template"],
                supported=impl.get("supported", True),
                version=impl.get("version", "1.0.0")
            )
            ids.append(impl_id)
        return ids

    # ===== Tier 2: Domain Patterns =====

    def add_domain_pattern(
        self,
        name: str,
        category: str,
        description: str,
        parameters: Dict[str, Any],
        implementation: Dict[str, Any],
        tags: str = "",
        icon: str = ""
    ) -> int:
        """Add a domain pattern (Tier 2)"""
        cursor = self.db.execute(
            """
            INSERT INTO domain_patterns
            (pattern_name, pattern_category, description, parameters, implementation, tags, icon)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (name, category, description, json.dumps(parameters), json.dumps(implementation), tags, icon)
        )
        self.db.commit()
        return cursor.lastrowid or 0

    def get_domain_pattern(self, name: str) -> Optional[Dict[str, Any]]:
        """Get domain pattern by name"""
        cursor = self.db.execute(
            "SELECT * FROM domain_patterns WHERE pattern_name = ?",
            (name,)
        )
        row = cursor.fetchone()
        if row:
            result = dict(row)
            result["parameters"] = json.loads(result["parameters"])
            result["implementation"] = json.loads(result["implementation"])
            return result
        return None

    def get_all_domain_patterns(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all domain patterns, optionally filtered by category"""
        if category:
            cursor = self.db.execute(
                "SELECT * FROM domain_patterns WHERE pattern_category = ? ORDER BY popularity_score DESC",
                (category,)
            )
        else:
            cursor = self.db.execute(
                "SELECT * FROM domain_patterns ORDER BY popularity_score DESC"
            )

        results = []
        for row in cursor.fetchall():
            result = dict(row)
            result["parameters"] = json.loads(result["parameters"])
            result["implementation"] = json.loads(result["implementation"])
            results.append(result)

        return results

    def instantiate_domain_pattern(
        self,
        pattern_name: str,
        entity_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Instantiate a domain pattern for a specific entity

        Returns:
            Dictionary with instantiated fields, actions, etc.
        """
        pattern = self.get_domain_pattern(pattern_name)
        if not pattern:
            raise ValueError(f"Domain pattern not found: {pattern_name}")

        # Validate parameters
        self._validate_pattern_parameters(pattern["parameters"], parameters)

        # Instantiate implementation
        instantiated = self._instantiate_implementation(
            pattern["implementation"],
            entity_name,
            parameters
        )

        # Record instantiation
        self.db.execute(
            """
            INSERT INTO pattern_instantiations (entity_name, domain_pattern_id, parameters)
            VALUES (?, ?, ?)
            """,
            (entity_name, pattern["domain_pattern_id"], json.dumps(parameters))
        )
        self.db.commit()

        return instantiated

    def _validate_pattern_parameters(
        self,
        param_schema: Dict[str, Any],
        provided_params: Dict[str, Any]
    ):
        """Validate provided parameters against schema"""
        for param_name, param_def in param_schema.items():
            if param_def.get("required", False) and param_name not in provided_params:
                raise ValueError(f"Required parameter missing: {param_name}")

    def _instantiate_implementation(
        self,
        implementation: Dict[str, Any],
        entity_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Instantiate pattern implementation with entity-specific values

        Replaces placeholders like {entity}, {state}, etc. with actual values
        """
        from jinja2 import Template

        # Convert implementation to JSON string, replace placeholders, parse back
        impl_json = json.dumps(implementation)
        template = Template(impl_json)

        context = {
            "entity": entity_name,
            **parameters
        }

        instantiated_json = template.render(**context)
        instantiated = json.loads(instantiated_json)

        return instantiated

    def compose_patterns(
        self,
        entity_name: str,
        patterns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compose multiple domain patterns into single entity definition

        Args:
            entity_name: Name of entity
            patterns: List of {"pattern": "pattern_name", "params": {...}}

        Returns:
            Composed entity definition with merged fields, actions, etc.
        """
        composed = {
            "entity": entity_name,
            "fields": [],
            "actions": [],
            "triggers": [],
            "indexes": [],
            "tables": []
        }

        # Track field names to detect conflicts
        field_names = set()
        action_names = set()

        for pattern_spec in patterns:
            pattern_name = pattern_spec["pattern"]
            params = pattern_spec.get("params", {})

            instantiated = self.instantiate_domain_pattern(
                pattern_name, entity_name, params
            )

            # Merge fields with conflict detection
            if "fields" in instantiated:
                for field in instantiated["fields"]:
                    field_name = field["name"]
                    if field_name in field_names:
                        # For now, allow duplicates but could be enhanced to merge intelligently
                        pass  # TODO: Implement intelligent field merging in future
                    else:
                        field_names.add(field_name)
                        composed["fields"].append(field)

            # Merge actions with conflict detection
            if "actions" in instantiated:
                for action in instantiated["actions"]:
                    action_name = action["name"]
                    if action_name in action_names:
                        # Rename conflicting actions
                        action["name"] = f"{pattern_name}_{action_name}"
                    action_names.add(action["name"])
                    composed["actions"].append(action)

            # Merge triggers
            if "triggers" in instantiated:
                composed["triggers"].extend(instantiated["triggers"])

            # Merge indexes
            if "indexes" in instantiated:
                composed["indexes"].extend(instantiated["indexes"])

            # Merge tables
            if "tables" in instantiated:
                composed["tables"].extend(instantiated["tables"])

        return composed

    def validate_pattern_composition(
        self,
        patterns: List[str]
    ) -> Dict[str, Any]:
        """
        Validate that a set of patterns can be composed together

        Args:
            patterns: List of pattern names

        Returns:
            Validation result with conflicts and warnings
        """
        validation_result = {
            "valid": True,
            "conflicts": [],
            "warnings": [],
            "pattern_details": []
        }

        pattern_details = []
        for pattern_name in patterns:
            pattern = self.get_domain_pattern(pattern_name)
            if not pattern:
                validation_result["valid"] = False
                validation_result["conflicts"].append(f"Pattern not found: {pattern_name}")
                continue
            pattern_details.append(pattern)

        # Check for field conflicts
        all_fields = {}
        for pattern in pattern_details:
            impl = pattern["implementation"]
            if "fields" in impl:
                for field in impl["fields"]:
                    field_name = field["name"]
                    if field_name in all_fields:
                        validation_result["conflicts"].append(
                            f"Field conflict: '{field_name}' defined in both "
                            f"{all_fields[field_name]} and {pattern['pattern_name']}"
                        )
                    else:
                        all_fields[field_name] = pattern["pattern_name"]

        # Check for action conflicts
        all_actions = {}
        for pattern in pattern_details:
            impl = pattern["implementation"]
            if "actions" in impl:
                for action in impl["actions"]:
                    action_name = action["name"]
                    if action_name in all_actions:
                        validation_result["warnings"].append(
                            f"Action conflict: '{action_name}' defined in both "
                            f"{all_actions[action_name]} and {pattern['pattern_name']}"
                        )
                    else:
                        all_actions[action_name] = pattern["pattern_name"]

        validation_result["pattern_details"] = pattern_details
        if validation_result["conflicts"]:
            validation_result["valid"] = False

        return validation_result

    def resolve_pattern_dependencies(
        self,
        pattern_names: List[str]
    ) -> List[str]:
        """
        Resolve pattern dependencies and return ordered list

        Args:
            pattern_names: Initial pattern names

        Returns:
            Ordered list with dependencies first
        """
        # For now, return as-is. Could be enhanced to check pattern_dependencies table
        # and perform topological sort
        return pattern_names

    # ===== TIER 3: Entity Templates =====

    def add_entity_template(
        self,
        template_name: str,
        template_namespace: str,
        description: str,
        default_fields: Dict[str, Any],
        default_patterns: Dict[str, Any],
        default_actions: Dict[str, Any],
        configuration_options: Optional[Dict[str, Any]] = None,
        icon: str = "",
        tags: str = ""
    ) -> int:
        """Add an entity template (Tier 3)"""
        cursor = self.db.execute(
            """
            INSERT INTO entity_templates
            (template_name, template_namespace, description, default_fields, default_patterns, default_actions, configuration_options, icon, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (template_name, template_namespace, description, json.dumps(default_fields), json.dumps(default_patterns), json.dumps(default_actions), json.dumps(configuration_options) if configuration_options else None, icon, tags)
        )
        self.db.commit()
        return cursor.lastrowid or 0

    def get_entity_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get entity template by name"""
        cursor = self.db.execute(
            "SELECT * FROM entity_templates WHERE template_name = ?",
            (template_name,)
        )
        row = cursor.fetchone()
        if row:
            result = dict(row)
            result["default_fields"] = json.loads(result["default_fields"])
            result["default_patterns"] = json.loads(result["default_patterns"])
            result["default_actions"] = json.loads(result["default_actions"])
            if result["configuration_options"]:
                result["configuration_options"] = json.loads(result["configuration_options"])
            return result
        return None

    def get_entity_templates_by_namespace(self, namespace: str) -> List[Dict[str, Any]]:
        """Get all entity templates for a specific namespace"""
        cursor = self.db.execute(
            "SELECT * FROM entity_templates WHERE template_namespace = ? ORDER BY template_name",
            (namespace,)
        )

        results = []
        for row in cursor.fetchall():
            result = dict(row)
            result["default_fields"] = json.loads(result["default_fields"])
            result["default_patterns"] = json.loads(result["default_patterns"])
            result["default_actions"] = json.loads(result["default_actions"])
            result["configuration_options"] = json.loads(result["configuration_options"]) if result["configuration_options"] else {}
            results.append(result)

        return results

    def get_all_entity_templates(self) -> List[Dict[str, Any]]:
        """Get all entity templates across all namespaces"""
        cursor = self.db.execute(
            "SELECT * FROM entity_templates ORDER BY template_namespace, template_name"
        )

        results = []
        for row in cursor.fetchall():
            result = dict(row)
            result["default_fields"] = json.loads(result["default_fields"])
            result["default_patterns"] = json.loads(result["default_patterns"])
            result["default_actions"] = json.loads(result["default_actions"])
            result["configuration_options"] = json.loads(result["configuration_options"]) if result["configuration_options"] else {}
            results.append(result)

        return results

    def instantiate_entity_template(
        self,
        template_name: str,
        entity_name: str,
        custom_fields: Optional[Dict[str, Any]] = None,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Instantiate an entity template for a specific entity

        Args:
            template_name: Name of the template to instantiate
            entity_name: Name of the entity to create
            custom_fields: Additional custom fields to add
            custom_config: Configuration overrides

        Returns:
            Complete entity definition with all patterns applied
        """
        template = self.get_entity_template(template_name)
        if not template:
            raise ValueError(f"Entity template not found: {template_name}")

        # Start with template defaults
        entity_def = {
            "entity": entity_name,
            "schema": template["template_namespace"],
            "fields": template["default_fields"].copy(),
            "actions": template["default_actions"].copy(),
            "patterns": template["default_patterns"].copy()
        }

        # Apply custom configuration
        if custom_config and template["configuration_options"]:
            for key, value in custom_config.items():
                if key in template["configuration_options"]:
                    # Apply configuration logic here
                    pass

        # Add custom fields
        if custom_fields:
            entity_def["fields"].update(custom_fields)

        # Instantiate domain patterns
        pattern_instances = []
        for pattern_name, pattern_config in template["default_patterns"].items():
            try:
                # Ensure entity parameter is provided
                params = pattern_config.copy()
                if "entity" not in params:
                    params["entity"] = entity_name

                instantiated = self.instantiate_domain_pattern(
                    pattern_name, entity_name, params
                )
                pattern_instances.append(instantiated)
            except Exception as e:
                print(f"Warning: Failed to instantiate pattern {pattern_name}: {e}")
                continue

        # Merge pattern implementations
        merged_entity = self._merge_pattern_instances(entity_def, pattern_instances)

        # Record template instantiation
        self.db.execute(
            """
            INSERT INTO pattern_instantiations (entity_name, entity_template_id, parameters)
            VALUES (?, ?, ?)
            """,
            (entity_name, template["entity_template_id"], json.dumps({
                "template": template_name,
                "custom_fields": custom_fields or {},
                "custom_config": custom_config or {}
            }))
        )
        self.db.commit()

        return merged_entity

    def _merge_pattern_instances(
        self,
        base_entity: Dict[str, Any],
        pattern_instances: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Merge multiple pattern instances into a single entity definition

        Handles conflicts and combines fields, actions, triggers, etc.
        """
        merged = base_entity.copy()

        # Convert template fields dict to list format for consistency
        if isinstance(merged.get("fields"), dict):
            merged["fields"] = [{"name": k, **v} for k, v in merged["fields"].items()]

        # Convert template actions dict to list format for consistency
        if isinstance(merged.get("actions"), dict):
            merged["actions"] = [{"name": k, **v} for k, v in merged["actions"].items()]

        # Initialize collections
        merged.setdefault("actions", [])
        merged.setdefault("triggers", [])
        merged.setdefault("indexes", [])
        merged.setdefault("tables", [])

        for instance in pattern_instances:
            # Merge fields (avoid duplicates by name)
            if "fields" in instance:
                existing_field_names = {f.get("name") for f in merged["fields"] if isinstance(f, dict)}
                for field in instance["fields"]:
                    if isinstance(field, dict) and field.get("name") not in existing_field_names:
                        merged["fields"].append(field)

            # Merge actions (allow duplicates for now, could add conflict resolution)
            if "actions" in instance:
                if isinstance(instance["actions"], list):
                    merged["actions"].extend(instance["actions"])
                elif isinstance(instance["actions"], dict):
                    # Convert dict actions to list format
                    for name, action_def in instance["actions"].items():
                        merged["actions"].append({"name": name, **action_def})

            # Merge triggers
            if "triggers" in instance:
                merged["triggers"].extend(instance["triggers"])

            # Merge indexes
            if "indexes" in instance:
                merged["indexes"].extend(instance["indexes"])

            # Merge tables
            if "tables" in instance:
                merged["tables"].extend(instance["tables"])

        return merged

    def validate_entity_template(
        self,
        template_name: str
    ) -> Dict[str, Any]:
        """
        Validate an entity template for consistency and conflicts

        Returns validation result with any issues found
        """
        template = self.get_entity_template(template_name)
        if not template:
            return {"valid": False, "errors": [f"Template not found: {template_name}"]}

        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "pattern_validation": {}
        }

        # Validate that referenced patterns exist
        for pattern_name in template["default_patterns"].keys():
            pattern = self.get_domain_pattern(pattern_name)
            if not pattern:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Referenced pattern not found: {pattern_name}")
            else:
                # Validate pattern parameters
                pattern_validation = self.validate_pattern_composition(
                    [pattern_name]
                )
                validation_result["pattern_validation"][pattern_name] = pattern_validation

                if not pattern_validation["valid"]:
                    validation_result["valid"] = False
                    validation_result["errors"].extend(pattern_validation["conflicts"])

        return validation_result

    # ===== Utility Methods =====

    def close(self):
        """Close database connection"""
        self.db.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()