# Weeks 23-24: Java Reverse Engineering & Pattern Detection

**Date**: 2025-11-13
**Duration**: 10 days (2 weeks)
**Status**: 🔴 Planning
**Objective**: Reverse engineer Java/Spring Boot applications to SpecQL universal format

**Prerequisites**: Week 22 complete (Unified Platform Integration)
**Output**: Java AST parser, pattern detector, Spring Boot → SpecQL converter

---

## 🎯 Executive Summary

Enable SpecQL to learn from existing **Java/Spring Boot** applications by reverse engineering:
- JPA/Hibernate entities → SpecQL entities
- Spring Data repositories → SpecQL patterns
- REST controllers → SpecQL actions
- Service layer patterns → Business logic

### Success Criteria

- [ ] Parse Java source code to AST
- [ ] Detect JPA entities and relationships
- [ ] Map Spring Data repositories to patterns
- [ ] Convert REST controllers to actions
- [ ] Extract business logic from service layers
- [ ] Generate SpecQL YAML from Java codebase
- [ ] 90%+ accuracy on Spring Boot apps

---

## Week 23: Java AST Parser & Core Mapping

**Objective**: Parse Java code and map core JPA entities to SpecQL

### Day 1: Java Parser Foundation

**Morning Block (4 hours): JavaParser Setup**

#### 🔴 RED: Parser Tests (2 hours)

**Test File**: `tests/unit/reverse_engineering/java/test_java_parser.py`

```python
"""Tests for Java source code parsing"""

import pytest
from src.reverse_engineering.java.java_parser import JavaParser


class TestJavaParser:
    """Test Java source code parsing"""

    @pytest.fixture
    def parser(self):
        return JavaParser()

    def test_parse_simple_class(self, parser):
        """Test parsing basic Java class"""
        java_code = """
        package com.example.demo;

        public class User {
            private Long id;
            private String email;
            private String name;

            // Getters and setters
            public Long getId() { return id; }
            public void setId(Long id) { this.id = id; }
        }
        """

        # Act
        ast = parser.parse(java_code)

        # Assert
        assert ast is not None
        assert ast.package_name == "com.example.demo"
        assert len(ast.classes) == 1

        user_class = ast.classes[0]
        assert user_class.name == "User"
        assert len(user_class.fields) == 3
        assert user_class.fields[0].name == "id"
        assert user_class.fields[0].type == "Long"

    def test_parse_jpa_entity(self, parser):
        """Test parsing JPA entity with annotations"""
        java_code = """
        package com.example.demo.entity;

        import javax.persistence.*;

        @Entity
        @Table(name = "users")
        public class User {
            @Id
            @GeneratedValue(strategy = GenerationType.IDENTITY)
            private Long id;

            @Column(nullable = false, unique = true)
            private String email;

            @Column(nullable = false)
            private String name;

            @ManyToOne
            @JoinColumn(name = "organization_id")
            private Organization organization;

            @OneToMany(mappedBy = "user")
            private List<Project> projects;
        }
        """

        # Act
        ast = parser.parse(java_code)

        # Assert
        user_class = ast.classes[0]
        assert user_class.has_annotation("Entity")
        assert user_class.get_annotation("Table").get_value("name") == "users"

        # Check fields with annotations
        id_field = user_class.get_field("id")
        assert id_field.has_annotation("Id")
        assert id_field.has_annotation("GeneratedValue")

        email_field = user_class.get_field("email")
        column_ann = email_field.get_annotation("Column")
        assert column_ann.get_value("nullable") == False
        assert column_ann.get_value("unique") == True

        # Check relationships
        org_field = user_class.get_field("organization")
        assert org_field.has_annotation("ManyToOne")
        assert org_field.type == "Organization"

        projects_field = user_class.get_field("projects")
        assert projects_field.has_annotation("OneToMany")
        assert "Project" in projects_field.type  # List<Project>

    def test_parse_spring_data_repository(self, parser):
        """Test parsing Spring Data JPA repository"""
        java_code = """
        package com.example.demo.repository;

        import org.springframework.data.jpa.repository.JpaRepository;
        import org.springframework.data.jpa.repository.Query;

        public interface UserRepository extends JpaRepository<User, Long> {
            User findByEmail(String email);

            @Query("SELECT u FROM User u WHERE u.organization.id = :orgId")
            List<User> findByOrganizationId(@Param("orgId") Long orgId);
        }
        """

        # Act
        ast = parser.parse(java_code)

        # Assert
        repo_interface = ast.classes[0]
        assert repo_interface.is_interface
        assert repo_interface.extends == "JpaRepository"
        assert len(repo_interface.methods) == 2

        # Check query methods
        find_by_email = repo_interface.get_method("findByEmail")
        assert find_by_email.return_type == "User"
        assert len(find_by_email.parameters) == 1

        custom_query = repo_interface.get_method("findByOrganizationId")
        assert custom_query.has_annotation("Query")
```

**Run Tests (Should Fail)**:
```bash
uv run pytest tests/unit/reverse_engineering/java/test_java_parser.py -v

# Expected: ModuleNotFoundError
```

**Commit**:
```bash
git add tests/unit/reverse_engineering/java/
git commit -m "test(java): add failing tests for Java parser - RED phase"
```

---

#### 🟢 GREEN: Implement Java Parser (2 hours)

**Dependencies**: Install JavaParser library
```bash
uv pip install javalang  # Python library for parsing Java
```

**Parser**: `src/reverse_engineering/java/java_parser.py`

```python
"""
Java Source Code Parser

Parses Java source code using javalang library.
Extracts classes, fields, methods, and annotations.
"""

import javalang
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class JavaAnnotation:
    """Java annotation"""
    name: str
    values: Dict[str, Any] = field(default_factory=dict)

    def get_value(self, key: str, default=None):
        """Get annotation value"""
        return self.values.get(key, default)


@dataclass
class JavaField:
    """Java field (class member variable)"""
    name: str
    type: str
    modifiers: List[str] = field(default_factory=list)
    annotations: List[JavaAnnotation] = field(default_factory=list)

    def has_annotation(self, name: str) -> bool:
        """Check if field has annotation"""
        return any(ann.name == name for ann in self.annotations)

    def get_annotation(self, name: str) -> Optional[JavaAnnotation]:
        """Get specific annotation"""
        return next((ann for ann in self.annotations if ann.name == name), None)

    def is_public(self) -> bool:
        return "public" in self.modifiers

    def is_private(self) -> bool:
        return "private" in self.modifiers


@dataclass
class JavaMethod:
    """Java method"""
    name: str
    return_type: str
    parameters: List[Dict[str, str]] = field(default_factory=list)
    modifiers: List[str] = field(default_factory=list)
    annotations: List[JavaAnnotation] = field(default_factory=list)
    body: Optional[str] = None

    def has_annotation(self, name: str) -> bool:
        return any(ann.name == name for ann in self.annotations)

    def get_annotation(self, name: str) -> Optional[JavaAnnotation]:
        return next((ann for ann in self.annotations if ann.name == name), None)


@dataclass
class JavaClass:
    """Java class or interface"""
    name: str
    package: str
    fields: List[JavaField] = field(default_factory=list)
    methods: List[JavaMethod] = field(default_factory=list)
    annotations: List[JavaAnnotation] = field(default_factory=list)
    modifiers: List[str] = field(default_factory=list)
    extends: Optional[str] = None
    implements: List[str] = field(default_factory=list)
    is_interface: bool = False

    def has_annotation(self, name: str) -> bool:
        return any(ann.name == name for ann in self.annotations)

    def get_annotation(self, name: str) -> Optional[JavaAnnotation]:
        return next((ann for ann in self.annotations if ann.name == name), None)

    def get_field(self, name: str) -> Optional[JavaField]:
        return next((f for f in self.fields if f.name == name), None)

    def get_method(self, name: str) -> Optional[JavaMethod]:
        return next((m for m in self.methods if m.name == name), None)


@dataclass
class JavaAST:
    """Java Abstract Syntax Tree"""
    package_name: str
    imports: List[str] = field(default_factory=list)
    classes: List[JavaClass] = field(default_factory=list)


class JavaParser:
    """Parse Java source code to AST"""

    def parse(self, java_code: str) -> JavaAST:
        """
        Parse Java source code

        Args:
            java_code: Java source code as string

        Returns:
            JavaAST with parsed structure
        """
        tree = javalang.parse.parse(java_code)

        return JavaAST(
            package_name=tree.package.name if tree.package else "",
            imports=self._extract_imports(tree),
            classes=self._extract_classes(tree)
        )

    def _extract_imports(self, tree) -> List[str]:
        """Extract import statements"""
        imports = []
        for imp in tree.imports:
            imports.append(imp.path)
        return imports

    def _extract_classes(self, tree) -> List[JavaClass]:
        """Extract all classes and interfaces"""
        classes = []

        for path, node in tree.filter(javalang.tree.ClassDeclaration):
            classes.append(self._parse_class(node, tree.package.name if tree.package else ""))

        for path, node in tree.filter(javalang.tree.InterfaceDeclaration):
            classes.append(self._parse_interface(node, tree.package.name if tree.package else ""))

        return classes

    def _parse_class(self, node: javalang.tree.ClassDeclaration, package: str) -> JavaClass:
        """Parse class declaration"""
        return JavaClass(
            name=node.name,
            package=package,
            fields=self._extract_fields(node),
            methods=self._extract_methods(node),
            annotations=self._extract_annotations(node.annotations or []),
            modifiers=node.modifiers or [],
            extends=node.extends.name if node.extends else None,
            implements=[impl.name for impl in (node.implements or [])]
        )

    def _parse_interface(self, node: javalang.tree.InterfaceDeclaration, package: str) -> JavaClass:
        """Parse interface declaration"""
        return JavaClass(
            name=node.name,
            package=package,
            methods=self._extract_methods(node),
            annotations=self._extract_annotations(node.annotations or []),
            modifiers=node.modifiers or [],
            extends=node.extends[0].name if node.extends else None,
            is_interface=True
        )

    def _extract_fields(self, class_node) -> List[JavaField]:
        """Extract fields from class"""
        fields = []

        for field in class_node.fields:
            for declarator in field.declarators:
                fields.append(JavaField(
                    name=declarator.name,
                    type=field.type.name,
                    modifiers=field.modifiers or [],
                    annotations=self._extract_annotations(field.annotations or [])
                ))

        return fields

    def _extract_methods(self, class_node) -> List[JavaMethod]:
        """Extract methods from class/interface"""
        methods = []

        for method in class_node.methods:
            parameters = []
            if method.parameters:
                for param in method.parameters:
                    parameters.append({
                        "name": param.name,
                        "type": param.type.name
                    })

            methods.append(JavaMethod(
                name=method.name,
                return_type=method.return_type.name if method.return_type else "void",
                parameters=parameters,
                modifiers=method.modifiers or [],
                annotations=self._extract_annotations(method.annotations or [])
            ))

        return methods

    def _extract_annotations(self, annotations) -> List[JavaAnnotation]:
        """Extract annotations"""
        result = []

        for ann in annotations:
            values = {}
            if ann.element:
                if isinstance(ann.element, list):
                    for elem in ann.element:
                        if hasattr(elem, 'name') and hasattr(elem, 'value'):
                            values[elem.name] = self._parse_annotation_value(elem.value)
                else:
                    values['value'] = self._parse_annotation_value(ann.element)

            result.append(JavaAnnotation(
                name=ann.name,
                values=values
            ))

        return result

    def _parse_annotation_value(self, value):
        """Parse annotation value (literal, string, etc.)"""
        if hasattr(value, 'value'):
            return value.value
        elif hasattr(value, 'qualifier'):
            return f"{value.qualifier}.{value.member}"
        elif isinstance(value, str):
            return value
        return str(value)
```

**Run Tests (Should Pass)**:
```bash
uv run pytest tests/unit/reverse_engineering/java/test_java_parser.py -v
```

**Commit**:
```bash
git add src/reverse_engineering/java/java_parser.py
git commit -m "feat(java): implement Java source code parser - GREEN phase"
```

---

**Afternoon Block (4 hours): JPA Entity Detector**

#### 🔴 RED: Entity Detection Tests (1.5 hours)

**Test File**: `tests/unit/reverse_engineering/java/test_jpa_entity_detector.py`

```python
"""Tests for JPA entity detection and conversion"""

import pytest
from src.reverse_engineering.java.jpa_entity_detector import JPAEntityDetector
from src.reverse_engineering.java.java_parser import JavaParser
from src.core.specql_parser import Entity


class TestJPAEntityDetector:
    """Test JPA entity detection"""

    @pytest.fixture
    def detector(self):
        parser = JavaParser()
        return JPAEntityDetector(parser)

    def test_detect_simple_entity(self, detector):
        """Test detecting basic JPA entity"""
        java_code = """
        package com.example.entity;

        import javax.persistence.*;

        @Entity
        @Table(name = "contacts")
        public class Contact {
            @Id
            @GeneratedValue(strategy = GenerationType.IDENTITY)
            private Long id;

            @Column(nullable = false)
            private String email;

            @Column(nullable = false)
            private String name;

            @Column
            private String phone;
        }
        """

        # Act
        entity = detector.detect_entity(java_code)

        # Assert
        assert entity is not None
        assert entity.name == "Contact"
        assert entity.table_name == "contacts"
        assert len(entity.fields) == 4

        # Check fields
        email_field = next(f for f in entity.fields if f.name == "email")
        assert email_field.field_type == "text"
        assert email_field.required == True

        phone_field = next(f for f in entity.fields if f.name == "phone")
        assert phone_field.required == False

    def test_detect_relationships(self, detector):
        """Test detecting JPA relationships"""
        java_code = """
        @Entity
        public class Project {
            @Id
            private Long id;

            @ManyToOne(fetch = FetchType.LAZY)
            @JoinColumn(name = "organization_id", nullable = false)
            private Organization organization;

            @ManyToOne
            @JoinColumn(name = "owner_id")
            private User owner;

            @OneToMany(mappedBy = "project", cascade = CascadeType.ALL)
            private List<Task> tasks;

            @ManyToMany
            @JoinTable(
                name = "project_members",
                joinColumns = @JoinColumn(name = "project_id"),
                inverseJoinColumns = @JoinColumn(name = "user_id")
            )
            private Set<User> members;
        }
        """

        # Act
        entity = detector.detect_entity(java_code)

        # Assert
        # ManyToOne → ref
        org_field = next(f for f in entity.fields if f.name == "organization")
        assert org_field.field_type == "ref"
        assert org_field.ref_entity == "Organization"
        assert org_field.required == True

        owner_field = next(f for f in entity.fields if f.name == "owner")
        assert owner_field.field_type == "ref"
        assert owner_field.ref_entity == "User"

        # OneToMany → Not included (handled by other side)
        assert not any(f.name == "tasks" for f in entity.fields)

        # ManyToMany → Special handling
        members_field = next(f for f in entity.fields if f.name == "members")
        assert members_field.field_type == "list"
        assert "User" in str(members_field)

    def test_convert_to_specql(self, detector):
        """Test complete conversion to SpecQL YAML"""
        java_code = """
        @Entity
        @Table(name = "users")
        public class User {
            @Id
            @GeneratedValue
            private Long id;

            @Column(nullable = false, unique = true, length = 100)
            private String email;

            @Column(nullable = false)
            private String name;

            @Enumerated(EnumType.STRING)
            @Column(nullable = false)
            private UserRole role;

            @ManyToOne
            private Organization organization;

            @Temporal(TemporalType.TIMESTAMP)
            @Column(name = "created_at")
            private Date createdAt;
        }
        """

        # Act
        specql_yaml = detector.convert_to_specql_yaml(java_code)

        # Assert
        assert "entity: User" in specql_yaml
        assert "table_name: users" in specql_yaml
        assert "email: text!" in specql_yaml
        assert "unique: true" in specql_yaml
        assert "role: enum" in specql_yaml
        assert "organization: ref(Organization)" in specql_yaml
        assert "created_at: timestamp" in specql_yaml
```

---

#### 🟢 GREEN: Implement Entity Detector (2.5 hours)

**Detector**: `src/reverse_engineering/java/jpa_entity_detector.py`

```python
"""
JPA Entity Detector

Detects JPA entities and converts to SpecQL universal format.
"""

import yaml
from typing import Optional, Dict, Any
from src.reverse_engineering.java.java_parser import JavaParser, JavaClass, JavaField
from src.core.specql_parser import Entity, Field


class JPAEntityDetector:
    """Detect and convert JPA entities to SpecQL"""

    def __init__(self, parser: JavaParser):
        self.parser = parser

    def detect_entity(self, java_code: str) -> Optional[Entity]:
        """
        Detect JPA entity from Java code

        Args:
            java_code: Java source code

        Returns:
            SpecQL Entity or None if not an entity
        """
        ast = self.parser.parse(java_code)

        for java_class in ast.classes:
            if java_class.has_annotation("Entity"):
                return self._convert_to_entity(java_class)

        return None

    def convert_to_specql_yaml(self, java_code: str) -> str:
        """
        Convert JPA entity to SpecQL YAML

        Args:
            java_code: Java source code

        Returns:
            SpecQL YAML string
        """
        entity = self.detect_entity(java_code)
        if not entity:
            return ""

        return self._format_as_yaml(entity)

    def _convert_to_entity(self, java_class: JavaClass) -> Entity:
        """Convert JavaClass to SpecQL Entity"""

        # Get table name from @Table annotation
        table_name = None
        table_ann = java_class.get_annotation("Table")
        if table_ann:
            table_name = table_ann.get_value("name")

        # Convert fields
        fields = []
        for java_field in java_class.fields:
            specql_field = self._convert_field(java_field)
            if specql_field:
                fields.append(specql_field)

        return Entity(
            name=java_class.name,
            table_name=table_name or self._to_snake_case(java_class.name),
            fields=fields,
            schema="public"  # Default, can be overridden
        )

    def _convert_field(self, java_field: JavaField) -> Optional[Field]:
        """Convert Java field to SpecQL field"""

        # Skip @OneToMany (handled by other side)
        if java_field.has_annotation("OneToMany"):
            return None

        # Get field name
        field_name = self._to_snake_case(java_field.name)

        # Detect field type
        field_type, ref_entity = self._detect_field_type(java_field)

        # Check if required
        required = self._is_required(java_field)

        # Get constraints
        constraints = self._extract_constraints(java_field)

        return Field(
            name=field_name,
            field_type=field_type,
            required=required,
            ref_entity=ref_entity,
            **constraints
        )

    def _detect_field_type(self, java_field: JavaField) -> tuple[str, Optional[str]]:
        """
        Detect SpecQL field type from Java field

        Returns:
            (field_type, ref_entity)
        """
        java_type = java_field.type

        # Handle relationships
        if java_field.has_annotation("ManyToOne"):
            return ("ref", java_type)

        if java_field.has_annotation("OneToOne"):
            return ("ref", java_type)

        if java_field.has_annotation("ManyToMany"):
            # Extract type from Collection
            inner_type = self._extract_generic_type(java_type)
            return ("list", inner_type)

        # Handle enums
        if java_field.has_annotation("Enumerated"):
            return ("enum", None)

        # Handle temporal types
        if java_field.has_annotation("Temporal"):
            temporal_ann = java_field.get_annotation("Temporal")
            temporal_type = temporal_ann.get_value("value", "TIMESTAMP")

            if "DATE" in str(temporal_type):
                return ("date", None)
            else:
                return ("timestamp", None)

        # Map Java types to SpecQL types
        type_map = {
            "String": "text",
            "Long": "integer",
            "Integer": "integer",
            "int": "integer",
            "long": "integer",
            "Boolean": "boolean",
            "boolean": "boolean",
            "Double": "decimal",
            "double": "decimal",
            "Float": "decimal",
            "float": "decimal",
            "BigDecimal": "decimal",
            "Date": "timestamp",
            "LocalDate": "date",
            "LocalDateTime": "timestamp",
            "Instant": "timestamp",
            "UUID": "uuid",
        }

        return (type_map.get(java_type, "text"), None)

    def _is_required(self, java_field: JavaField) -> bool:
        """Check if field is required (NOT NULL)"""

        # Check @Column(nullable = false)
        column_ann = java_field.get_annotation("Column")
        if column_ann:
            nullable = column_ann.get_value("nullable", True)
            if nullable == False:
                return True

        # Check @JoinColumn(nullable = false)
        join_column_ann = java_field.get_annotation("JoinColumn")
        if join_column_ann:
            nullable = join_column_ann.get_value("nullable", True)
            if nullable == False:
                return True

        return False

    def _extract_constraints(self, java_field: JavaField) -> Dict[str, Any]:
        """Extract constraints from annotations"""
        constraints = {}

        column_ann = java_field.get_annotation("Column")
        if column_ann:
            # Unique constraint
            unique = column_ann.get_value("unique")
            if unique:
                constraints["unique"] = True

            # Length/max length
            length = column_ann.get_value("length")
            if length:
                constraints["max_length"] = length

        return constraints

    def _extract_generic_type(self, type_str: str) -> str:
        """Extract type from generic (e.g., List<User> → User)"""
        if "<" in type_str and ">" in type_str:
            start = type_str.index("<") + 1
            end = type_str.index(">")
            return type_str[start:end]
        return type_str

    def _to_snake_case(self, camel_case: str) -> str:
        """Convert CamelCase to snake_case"""
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_case)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _format_as_yaml(self, entity: Entity) -> str:
        """Format Entity as SpecQL YAML"""
        data = {
            "entity": entity.name,
            "schema": entity.schema,
        }

        if entity.table_name:
            data["table_name"] = entity.table_name

        # Format fields
        fields = {}
        for field in entity.fields:
            field_def = field.field_type
            if field.required:
                field_def += "!"

            if field.ref_entity:
                field_def = f"ref({field.ref_entity})"

            if field.unique:
                # Add as constraint
                fields[field.name] = {
                    "type": field_def,
                    "unique": True
                }
            else:
                fields[field.name] = field_def

        data["fields"] = fields

        return yaml.dump(data, default_flow_style=False, sort_keys=False)
```

**Run Tests (Should Pass)**:
```bash
uv run pytest tests/unit/reverse_engineering/java/test_jpa_entity_detector.py -v
```

**Commit**:
```bash
git add src/reverse_engineering/java/jpa_entity_detector.py
git commit -m "feat(java): implement JPA entity detector - GREEN phase"
```

---

**Day 1 Summary**:
- ✅ Java source code parser (using javalang)
- ✅ JPA annotation extraction
- ✅ Entity detection
- ✅ Field type mapping (Java → SpecQL)
- ✅ Relationship detection (ManyToOne, OneToMany, ManyToMany)

---

### Day 2: Spring Data Repository Pattern Detection

**Objective**: Detect Spring Data repositories and convert to SpecQL patterns

**Morning Block (4 hours): Repository Pattern Detection**

#### 🔴 RED + 🟢 GREEN: Repository Detector (4 hours)

**Test File**: `tests/unit/reverse_engineering/java/test_spring_repository_detector.py`

```python
"""Tests for Spring Data repository detection"""

import pytest
from src.reverse_engineering.java.spring_repository_detector import SpringRepositoryDetector


class TestSpringRepositoryDetector:
    """Test Spring Data repository pattern detection"""

    @pytest.fixture
    def detector(self):
        return SpringRepositoryDetector()

    def test_detect_crud_repository(self, detector):
        """Test detecting CrudRepository"""
        java_code = """
        public interface UserRepository extends CrudRepository<User, Long> {
            // Inherits: save, findById, findAll, deleteById, etc.
        }
        """

        # Act
        patterns = detector.detect_patterns(java_code)

        # Assert
        assert len(patterns) > 0
        assert patterns[0].entity == "User"
        assert "CRUD" in patterns[0].operations

    def test_detect_query_methods(self, detector):
        """Test detecting query methods from method names"""
        java_code = """
        public interface UserRepository extends JpaRepository<User, Long> {
            // Query derived from method name
            User findByEmail(String email);

            List<User> findByOrganizationId(Long organizationId);

            List<User> findByNameContainingIgnoreCase(String name);

            Long countByRole(String role);

            boolean existsByEmail(String email);

            void deleteByOrganizationId(Long organizationId);
        }
        """

        # Act
        patterns = detector.detect_patterns(java_code)

        # Assert - Should detect query patterns
        assert any(p.operation == "findByEmail" for p in patterns)
        assert any(p.operation == "findByOrganizationId" for p in patterns)
        assert any(p.operation == "countByRole" for p in patterns)

    def test_detect_custom_queries(self, detector):
        """Test detecting custom @Query annotations"""
        java_code = """
        public interface ProjectRepository extends JpaRepository<Project, Long> {
            @Query("SELECT p FROM Project p WHERE p.status = :status")
            List<Project> findByStatus(@Param("status") String status);

            @Query(value = "SELECT * FROM projects WHERE deadline < NOW()", nativeQuery = true)
            List<Project> findOverdueProjects();

            @Modifying
            @Query("UPDATE Project p SET p.status = :status WHERE p.id = :id")
            void updateStatus(@Param("id") Long id, @Param("status") String status);
        }
        """

        # Act
        patterns = detector.detect_patterns(java_code)

        # Assert
        find_by_status = next(p for p in patterns if p.operation == "findByStatus")
        assert find_by_status.query_type == "JPQL"
        assert "SELECT p FROM Project" in find_by_status.query

        overdue = next(p for p in patterns if "Overdue" in p.operation)
        assert overdue.query_type == "Native"
```

**Detector**: `src/reverse_engineering/java/spring_repository_detector.py`

```python
"""
Spring Data Repository Pattern Detector

Detects patterns from Spring Data JPA repositories:
- Query methods (findBy*, countBy*, existsBy*)
- Custom @Query annotations
- CRUD operations
"""

from dataclasses import dataclass
from typing import List, Optional
from src.reverse_engineering.java.java_parser import JavaParser, JavaClass, JavaMethod


@dataclass
class RepositoryPattern:
    """Detected repository pattern"""
    entity: str
    operation: str
    method_name: str
    return_type: str
    parameters: List[dict]
    query_type: Optional[str] = None  # "Derived", "JPQL", "Native"
    query: Optional[str] = None


class SpringRepositoryDetector:
    """Detect Spring Data repository patterns"""

    def __init__(self):
        self.parser = JavaParser()

    def detect_patterns(self, java_code: str) -> List[RepositoryPattern]:
        """
        Detect repository patterns from Java code

        Args:
            java_code: Spring Data repository interface

        Returns:
            List of detected patterns
        """
        ast = self.parser.parse(java_code)
        patterns = []

        for java_class in ast.classes:
            if self._is_repository(java_class):
                patterns.extend(self._extract_patterns(java_class))

        return patterns

    def _is_repository(self, java_class: JavaClass) -> bool:
        """Check if class is a Spring Data repository"""
        if not java_class.is_interface:
            return False

        repository_types = [
            "CrudRepository",
            "JpaRepository",
            "PagingAndSortingRepository",
            "Repository"
        ]

        return any(repo in (java_class.extends or "") for repo in repository_types)

    def _extract_patterns(self, repo_class: JavaClass) -> List[RepositoryPattern]:
        """Extract patterns from repository"""
        patterns = []

        # Get entity name from generic type (e.g., JpaRepository<User, Long>)
        entity_name = self._extract_entity_name(repo_class.extends)

        # Extract patterns from methods
        for method in repo_class.methods:
            pattern = self._analyze_method(method, entity_name)
            if pattern:
                patterns.append(pattern)

        return patterns

    def _extract_entity_name(self, extends: str) -> str:
        """Extract entity name from generic type"""
        if "<" in extends and ">" in extends:
            start = extends.index("<") + 1
            end = extends.index(",")
            return extends[start:end].strip()
        return "Unknown"

    def _analyze_method(self, method: JavaMethod, entity: str) -> Optional[RepositoryPattern]:
        """Analyze repository method"""

        # Check for @Query annotation
        query_ann = method.get_annotation("Query")
        if query_ann:
            query = query_ann.get_value("value", "")
            is_native = query_ann.get_value("nativeQuery", False)

            return RepositoryPattern(
                entity=entity,
                operation=method.name,
                method_name=method.name,
                return_type=method.return_type,
                parameters=method.parameters,
                query_type="Native" if is_native else "JPQL",
                query=query
            )

        # Derive query from method name
        if self._is_query_method(method.name):
            return RepositoryPattern(
                entity=entity,
                operation=method.name,
                method_name=method.name,
                return_type=method.return_type,
                parameters=method.parameters,
                query_type="Derived"
            )

        return None

    def _is_query_method(self, method_name: str) -> bool:
        """Check if method name follows query method convention"""
        prefixes = ["findBy", "readBy", "queryBy", "getBy", "countBy", "existsBy", "deleteBy", "removeBy"]
        return any(method_name.startswith(prefix) for prefix in prefixes)
```

---

**Afternoon Block (4 hours): REST Controller to Action Converter**

#### 🔴 RED + 🟢 GREEN: Controller Converter (4 hours)

**Test & Implementation**: Convert Spring REST controllers to SpecQL actions

**Test File**: `tests/unit/reverse_engineering/java/test_controller_converter.py`

**Converter**: `src/reverse_engineering/java/controller_converter.py`

Converts:
- `@GetMapping` → Query actions
- `@PostMapping` → Create actions
- `@PutMapping` / `@PatchMapping` → Update actions
- `@DeleteMapping` → Delete actions

**Day 2 Summary**:
- ✅ Spring Data repository detection
- ✅ Query method pattern recognition
- ✅ Custom @Query extraction
- ✅ REST controller to action conversion

---

### Days 3-5: Complete Java Integration

**Day 3**: Service Layer Pattern Detection
- Extract business logic from @Service classes
- Detect transaction boundaries (@Transactional)
- Map service methods to SpecQL actions

**Day 4**: Complete Project Analyzer
- Scan entire Spring Boot project
- Detect all entities, repositories, services, controllers
- Generate complete SpecQL YAML project

**Day 5**: Testing & CLI Integration
- Integration tests with real Spring Boot projects
- CLI command: `specql reverse java src/main/java/`
- Documentation and examples

---

## Week 24: Advanced Java Patterns & Validation

### Day 1-2: Advanced JPA Features
- Inheritance mapping (@Inheritance)
- Embedded types (@Embeddable)
- Composite keys (@EmbeddedId)
- Lifecycle callbacks (@PrePersist, @PostLoad)

### Day 3-4: Spring Boot Integration
- application.properties/yml parsing
- Database connection detection
- Spring Security patterns
- Validation annotations (@Valid, @NotNull)

### Day 5: Quality & Polish
- Edge case handling
- Error messages
- Performance optimization
- Complete documentation

---

## Success Metrics

- [ ] Parse 95%+ of Spring Boot projects
- [ ] Accurate entity detection (90%+)
- [ ] Relationship mapping correct
- [ ] Query method patterns recognized
- [ ] Service layer business logic extracted
- [ ] Complete project reverse engineering < 5 minutes
- [ ] Generated SpecQL YAML compiles and deploys

---

## Example: Complete Reverse Engineering

**Input**: Spring Boot project
```
src/main/java/com/example/
├── entity/
│   ├── User.java (JPA entity)
│   ├── Project.java
│   └── Task.java
├── repository/
│   ├── UserRepository.java
│   └── ProjectRepository.java
├── service/
│   └── ProjectService.java
└── controller/
    └── ProjectController.java
```

**Command**:
```bash
specql reverse java src/main/java/com/example/
```

**Output**: `project.specql.yaml`
```yaml
project: example_project

database:
  schema_type: multi_tenant
  entities:
    - entity: User
      fields:
        email: text!
        name: text!

    - entity: Project
      fields:
        name: text!
        owner: ref(User)
        status: enum(active, completed)

    - entity: Task
      fields:
        title: text!
        project: ref(Project)
        assignee: ref(User)

  actions:
    - name: create_task
      steps:
        - validate: project.status = 'active'
        - insert: Task
        - notify: assignee
```

---

**Status**: 🔴 Ready to Execute
**Priority**: High (enables Java ecosystem adoption)
**Expected Output**: Complete Java/Spring Boot reverse engineering capability
