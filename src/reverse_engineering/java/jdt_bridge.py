"""
Eclipse JDT Bridge

Python bridge to Eclipse JDT for parsing Java code.
Uses Py4J to communicate with Java process running JDT.
"""

import subprocess
from pathlib import Path
from typing import Optional, Any
from py4j.java_gateway import JavaGateway, GatewayParameters
import atexit


class JDTBridge:
    """Bridge to Eclipse JDT Java parser"""

    def __init__(self):
        self.gateway: Optional[JavaGateway] = None
        self.jdt_process: Optional[subprocess.Popen] = None
        self._start_jdt_server()

    def _start_jdt_server(self):
        """Start JDT Java process"""
        try:
            # Find lib/jdt directory relative to project root
            # Assume we're running from project root or a subdirectory
            jdt_dir = Path("lib/jdt")
            if not jdt_dir.exists():
                # Try from current file's location
                project_root = Path(__file__).parent.parent.parent.parent
                jdt_dir = project_root / "lib" / "jdt"

            if not jdt_dir.exists():
                raise FileNotFoundError(f"JDT directory not found: {jdt_dir}")

            # Start Java process with JDT wrapper from lib/jdt directory
            # Include all Eclipse dependencies for standalone parsing
            classpath = ":".join(
                [
                    "org.eclipse.jdt.core-3.35.0.jar",
                    "org.eclipse.jdt.compiler.apt-1.5.100.jar",
                    "org.eclipse.core.resources-3.19.100.jar",
                    "org.eclipse.equinox.common-3.18.100.jar",
                    "py4j0.10.9.7.jar",
                    ".",
                ]
            )

            self.jdt_process = subprocess.Popen(
                ["java", "-cp", classpath, "JDTWrapper"], cwd=str(jdt_dir)
            )

            # Connect to gateway
            self.gateway = JavaGateway(
                gateway_parameters=GatewayParameters(auto_convert=True)
            )

            # Register cleanup
            atexit.register(self.shutdown)

        except (FileNotFoundError, subprocess.SubprocessError, Exception) as e:
            # Fallback to mock implementation if Java/JDT not available
            print(
                f"Warning: JDT bridge initialization failed ({e}), using mock implementation"
            )
            self._use_mock_implementation()

    def _use_mock_implementation(self):
        """Use mock implementation when JDT is not available"""
        self.mock_mode = True

    def parse_java(self, source_code: str) -> Any:
        """
        Parse Java source code to AST

        Args:
            source_code: Java source code as string

        Returns:
            CompilationUnit AST (or mock AST in fallback mode)
        """
        if hasattr(self, "mock_mode") and self.mock_mode:
            return self._mock_parse_java(source_code)

        if not self.gateway:
            raise RuntimeError("JDT gateway not initialized")

        try:
            wrapper = self.gateway.entry_point
            return wrapper.parse(source_code)
        except Exception as e:
            print(
                f"Warning: JDT parsing failed ({e}), falling back to mock implementation"
            )
            self._use_mock_implementation()
            return self._mock_parse_java(source_code)

    def _mock_parse_java(self, source_code: str) -> Any:
        """
        Mock Java parsing for development/testing when JDT is not available

        Returns a simplified AST-like structure that mimics basic JDT structure
        """

        class MockCompilationUnit:
            def __init__(self, source):
                self.source = source
                self._types = []

            def types(self):
                return self._types

        # Basic mock - identify class declarations with annotations
        cu = MockCompilationUnit(source_code)

        # Simple regex-based class extraction with @Entity or Spring annotations
        import re

        # Match @Entity followed by class declaration (allowing newlines and abstract)
        entity_pattern = r"@Entity[\s\S]*?public\s+(?:abstract\s+)?class\s+(\w+)[\s\S]*?\{([\s\S]*?)\}"
        entity_matches = re.findall(
            entity_pattern, source_code, re.MULTILINE | re.DOTALL
        )

        for match in entity_matches:
            class_name = match[0]
            class_body = match[1]
            mock_type = MockTypeDeclaration(class_name, source_code, class_body)
            cu._types.append(mock_type)

        # Match Spring components (@Service, @Controller, @RestController, @Repository, etc.)
        spring_pattern = r"(@(?:Service|Controller|RestController|Repository|Component|Configuration)[\s\S]*?)public\s+(?:abstract\s+)?class\s+(\w+)[\s\S]*?\{"
        spring_matches = re.findall(
            spring_pattern, source_code, re.MULTILINE | re.DOTALL
        )

        for match in spring_matches:
            annotations_text = match[0]
            class_name = match[1]

            # Find the full class declaration to locate the opening brace
            full_match_pattern = (
                re.escape(annotations_text)
                + r"public\s+(?:abstract\s+)?class\s+"
                + class_name
                + r"[\s\S]*?\{"
            )
            full_match = re.search(full_match_pattern, source_code, re.DOTALL)
            if full_match:
                brace_start = full_match.end() - 1  # Position of opening brace

                # Count braces to find class end
                brace_count = 1
                i = brace_start + 1
                while i < len(source_code) and brace_count > 0:
                    if source_code[i] == "{":
                        brace_count += 1
                    elif source_code[i] == "}":
                        brace_count -= 1
                    i += 1

                # Extract class body
                class_body = source_code[brace_start + 1 : i - 1]

                mock_type = MockSpringTypeDeclaration(
                    class_name, source_code, class_body, annotations_text
                )
                cu._types.append(mock_type)

        # Match repository interfaces (interfaces extending repository classes)
        repo_pattern = r"public\s+interface\s+(\w+)\s+extends\s+(?:JpaRepository|CrudRepository|PagingAndSortingRepository|Repository)"
        repo_matches = re.findall(repo_pattern, source_code, re.MULTILINE)

        for class_name in repo_matches:
            # Find the interface declaration
            interface_pattern = (
                r"public\s+interface\s+" + class_name + r"\s+extends[\s\S]*?\{"
            )
            interface_match = re.search(interface_pattern, source_code, re.DOTALL)
            if interface_match:
                brace_start = interface_match.end() - 1

                # Count braces to find interface end
                brace_count = 1
                i = brace_start + 1
                while i < len(source_code) and brace_count > 0:
                    if source_code[i] == "{":
                        brace_count += 1
                    elif source_code[i] == "}":
                        brace_count -= 1
                    i += 1

                # Extract interface body
                class_body = source_code[brace_start + 1 : i - 1]

                # Create mock type for repository interface
                mock_type = MockSpringTypeDeclaration(
                    class_name,
                    source_code,
                    class_body,
                    "",  # No annotations for repository interfaces
                )
                cu._types.append(mock_type)

        return cu

    def shutdown(self):
        """Shutdown JDT server"""
        if self.gateway:
            self.gateway.shutdown()
        if self.jdt_process:
            self.jdt_process.terminate()
            self.jdt_process.wait()


class MockTypeDeclaration:
    """Mock type declaration for fallback mode"""

    def __init__(self, class_name, source_code, class_body=None):
        self.class_name = class_name
        self.source_code = source_code
        self._class_body = class_body
        self._modifiers = self._extract_modifiers()
        self._body_declarations = self._extract_body_declarations()
        self._super_interfaces = self._extract_super_interfaces()

    def getName(self):
        return MockSimpleName(self.class_name)

    def modifiers(self):
        return self._modifiers

    def bodyDeclarations(self):
        return self._body_declarations

    def superInterfaceTypes(self):
        """Return list of super interfaces (for repository detection)"""
        return self._super_interfaces

    def isInterface(self):
        """Check if this is an interface"""
        # Check if the source contains "interface class_name"
        import re

        return bool(
            re.search(
                rf"\binterface\s+{re.escape(self.class_name)}\b", self.source_code
            )
        )

    def _extract_super_interfaces(self):
        """Extract super interfaces from extends clause"""
        import re

        interfaces = []

        # Match "extends Interface1, Interface2" for classes/interfaces
        extends_pattern = (
            rf"(?:class|interface)\s+{re.escape(self.class_name)}\s+extends\s+([^{{]+)"
        )
        extends_match = re.search(extends_pattern, self.source_code, re.DOTALL)

        if extends_match:
            extends_clause = extends_match.group(1).strip()
            # Split by comma and clean up
            interface_names = [name.strip() for name in extends_clause.split(",")]

            for interface_name in interface_names:
                # Create mock interface type
                interfaces.append(MockSimpleType(interface_name))

        return interfaces

    def _extract_modifiers(self):
        """Extract class-level annotations"""
        modifiers = [MockAnnotation("@Entity")]  # Always add @Entity

        # Extract @Table annotation if present
        import re

        table_pattern = r"@Table\(([^)]+)\)"
        table_match = re.search(table_pattern, self.source_code)
        if table_match:
            table_params = table_match.group(1)
            modifiers.append(MockTableAnnotation(table_params))

        return modifiers

    def _extract_body_declarations(self):
        """Extract both field and method declarations from the class/interface"""
        declarations = []
        import re

        # Check if this is an interface
        is_interface = self.isInterface()

        # Use the stored class body if available, otherwise find it
        if hasattr(self, "_class_body") and self._class_body:
            class_body = self._class_body
        else:
            # Find the class/interface body using brace counting
            class_body = self._extract_class_body_with_brace_counting()

        if is_interface:
            # For interfaces, extract method signatures (no bodies)
            method_declarations = self._extract_interface_methods(class_body)
            declarations.extend(method_declarations)
        else:
            # For classes, extract fields and methods with bodies
            # Extract field declarations (handle generics like List<Contact>)
            field_pattern = r"(?:@\w+(?:\([^)]*\))?\s+)*private\s+([\w<>\[\]]+)\s+(\w+)(?:\s*=\s*[^;]+)?\s*;"
            field_matches = re.findall(field_pattern, class_body)

            for java_type, field_name in field_matches:
                field_decl = MockFieldDeclaration(java_type, field_name, class_body)
                declarations.append(field_decl)

            # Extract method declarations using brace counting (handles nested braces)
            methods = self._extract_methods_with_brace_counting(class_body)
            declarations.extend(methods)

        return declarations

    def _extract_interface_methods(self, interface_body):
        """Extract method declarations from interface (no method bodies)"""
        import re

        methods = []

        # Match interface method signatures: @Annotations Type methodName(params);
        method_pattern = (
            r"((?:@\w+(?:\([^)]*\))?\s*)*)(\w+(?:<[^>]+>)?)\s+(\w+)\s*\((.*?)\)\s*;"
        )
        method_matches = re.finditer(method_pattern, interface_body, re.DOTALL)

        for match in method_matches:
            method_text = match.group(0)  # Include the semicolon
            try:
                method_decl = MockInterfaceMethodDeclaration(
                    method_text, interface_body
                )
                methods.append(method_decl)
            except Exception as e:
                print(
                    f"Error parsing interface method: {e}, text: {repr(method_text[:100])}"
                )
                # Continue without this method

        return methods

    def _extract_class_body_with_brace_counting(self):
        """Extract class body using brace counting to handle nested braces correctly"""
        import re

        # Find the class declaration start
        class_pattern = rf"(?:@\w+\s+)*(?:public\s+)?(?:class|interface)\s+{self.class_name}[^{{]*\{{"
        match = re.search(class_pattern, self.source_code, re.DOTALL)
        if not match:
            return ""

        # Find opening brace position
        brace_start = match.end() - 1  # -1 because match.end() is after the {

        # Count braces to find class end
        brace_count = 1
        i = brace_start + 1
        while i < len(self.source_code) and brace_count > 0:
            if self.source_code[i] == "{":
                brace_count += 1
            elif self.source_code[i] == "}":
                brace_count -= 1
            i += 1

        # Extract class body (everything between the braces)
        class_body = self.source_code[brace_start + 1 : i - 1]
        return class_body

    def _extract_methods_with_brace_counting(self, class_body):
        """Extract methods by counting braces to handle nested braces correctly"""
        import re

        methods = []
        i = 0
        while i < len(class_body):
            # Find method signature (without requiring closing brace in regex)
            sig_match = re.search(
                r"((?:@\w+(?:\([^)]*\))?\s+)*)(public|private|protected)\s+"
                r"(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)\s*"
                r"(?:throws\s+[\w\s,]+)?",
                class_body[i:],
            )
            if not sig_match:
                break

            # Find opening brace after the signature
            sig_end = i + sig_match.end()
            brace_start = class_body.find("{", sig_end)
            if brace_start == -1:
                i = sig_end
                continue

            # Count braces to find method end (handles nested braces)
            brace_count = 1
            j = brace_start + 1
            while j < len(class_body) and brace_count > 0:
                if class_body[j] == "{":
                    brace_count += 1
                elif class_body[j] == "}":
                    brace_count -= 1
                j += 1

            # Extract the complete method text
            method_text = class_body[i + sig_match.start() : j]
            methods.append(MockMethodDeclaration(method_text, class_body))
            i = j

        return methods


class MockSimpleName:
    """Mock simple name"""

    def __init__(self, identifier):
        self.identifier = identifier

    def getIdentifier(self):
        return self.identifier


class MockAnnotation:
    """Mock annotation"""

    def __init__(self, annotation_text):
        self.annotation_text = annotation_text
        # Extract annotation name from @Name format
        if annotation_text.startswith("@"):
            self.annotation_name = annotation_text[1:]
        else:
            self.annotation_name = annotation_text

    def isAnnotation(self):
        return True

    def getTypeName(self):
        return MockQualifiedName(self.annotation_name)

    def isSingleMemberAnnotation(self):
        return False

    def isNormalAnnotation(self):
        return True

    def values(self):
        return []

    def getValue(self):
        """For single member annotations"""
        return None


class MockTableAnnotation(MockAnnotation):
    """Mock @Table annotation"""

    def __init__(self, params_text):
        super().__init__("@Table")
        self.params_text = params_text

    def values(self):
        # Parse name = "contacts", schema = "test" from params
        import re

        values = []

        # Parse name
        name_match = re.search(r'name\s*=\s*"([^"]+)"', self.params_text)
        if name_match:
            values.append(MockAnnotationMemberValuePair("name", name_match.group(1)))

        # Parse schema
        schema_match = re.search(r'schema\s*=\s*"([^"]+)"', self.params_text)
        if schema_match:
            values.append(
                MockAnnotationMemberValuePair("schema", schema_match.group(1))
            )

        return values


class MockColumnAnnotation(MockAnnotation):
    """Mock @Column annotation"""

    def __init__(self, params_text):
        super().__init__("@Column")
        self.params_text = params_text

    def values(self):
        # Parse parameters like nullable = false, unique = true, etc.
        import re

        values = []

        # Parse name = "value"
        name_match = re.search(r'name\s*=\s*"([^"]+)"', self.params_text)
        if name_match:
            values.append(MockAnnotationMemberValuePair("name", name_match.group(1)))

        # Parse nullable = false/true
        nullable_match = re.search(
            r"nullable\s*=\s*(true|false)", self.params_text, re.IGNORECASE
        )
        if nullable_match:
            values.append(
                MockAnnotationMemberValuePair(
                    "nullable", nullable_match.group(1).lower() == "true"
                )
            )

        # Parse unique = false/true
        unique_match = re.search(
            r"unique\s*=\s*(true|false)", self.params_text, re.IGNORECASE
        )
        if unique_match:
            values.append(
                MockAnnotationMemberValuePair(
                    "unique", unique_match.group(1).lower() == "true"
                )
            )

        # Parse length = 100
        length_match = re.search(r"length\s*=\s*(\d+)", self.params_text)
        if length_match:
            values.append(
                MockAnnotationMemberValuePair("length", int(length_match.group(1)))
            )

        return values


class MockJoinColumnAnnotation(MockAnnotation):
    """Mock @JoinColumn annotation"""

    def __init__(self, params_text):
        super().__init__("@JoinColumn")
        self.params_text = params_text

    def values(self):
        # Parse parameters like name = "company_id"
        import re

        values = []

        # Parse name = "value"
        name_match = re.search(r'name\s*=\s*"([^"]+)"', self.params_text)
        if name_match:
            values.append(MockAnnotationMemberValuePair("name", name_match.group(1)))

        return values


class MockEnumeratedAnnotation(MockAnnotation):
    """Mock @Enumerated annotation"""

    def __init__(self, params_text):
        super().__init__("@Enumerated")
        self.params_text = params_text

    def values(self):
        # Parse parameters like EnumType.STRING or value = EnumType.STRING
        import re

        values = []

        # Try parsing value = EnumType.STRING first
        value_match = re.search(r"value\s*=\s*[^.]+\.(\w+)", self.params_text)
        if value_match:
            values.append(MockAnnotationMemberValuePair("value", value_match.group(1)))
        else:
            # Try parsing just EnumType.STRING (implicit value parameter)
            enum_match = re.search(r"([^.]+)\.(\w+)", self.params_text.strip())
            if enum_match:
                values.append(
                    MockAnnotationMemberValuePair("value", enum_match.group(2))
                )

        return values


class MockAnnotationMemberValuePair:
    """Mock annotation member value pair"""

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def getName(self):
        return MockSimpleName(self.name)

    def getValue(self):
        if isinstance(self.value, bool):
            return MockBooleanLiteral(self.value)
        elif isinstance(self.value, int):
            return MockNumberLiteral(self.value)
        else:
            return MockStringLiteral(str(self.value))


class MockStringLiteral:
    """Mock string literal"""

    STRING_LITERAL = "STRING_LITERAL"
    BOOLEAN_LITERAL = "BOOLEAN_LITERAL"
    NUMBER_LITERAL = "NUMBER_LITERAL"
    QUALIFIED_NAME = "QUALIFIED_NAME"

    def __init__(self, value):
        self.value = value

    def getNodeType(self):
        return "STRING_LITERAL"

    def getLiteralValue(self):
        return self.value


class MockBooleanLiteral:
    """Mock boolean literal"""

    STRING_LITERAL = "STRING_LITERAL"
    BOOLEAN_LITERAL = "BOOLEAN_LITERAL"
    NUMBER_LITERAL = "NUMBER_LITERAL"
    QUALIFIED_NAME = "QUALIFIED_NAME"

    def __init__(self, value):
        self.value = value

    def getNodeType(self):
        return "BOOLEAN_LITERAL"

    def booleanValue(self):
        return self.value


class MockNumberLiteral:
    """Mock number literal"""

    STRING_LITERAL = "STRING_LITERAL"
    BOOLEAN_LITERAL = "BOOLEAN_LITERAL"
    NUMBER_LITERAL = "NUMBER_LITERAL"
    QUALIFIED_NAME = "QUALIFIED_NAME"

    def __init__(self, value):
        self.value = value

    def getNodeType(self):
        return "NUMBER_LITERAL"

    def getToken(self):
        return str(self.value)


class MockSpringTypeDeclaration(MockTypeDeclaration):
    """Mock Spring component type declaration"""

    def __init__(self, class_name, source_code, class_body=None, annotations_text=""):
        super().__init__(class_name, source_code, class_body)
        self._annotations_text = annotations_text
        self._spring_modifiers = self._extract_spring_modifiers()

    def modifiers(self):
        return self._spring_modifiers

    def _extract_spring_modifiers(self):
        """Extract Spring annotations and modifiers"""
        modifiers = []

        # Add Spring stereotype annotations
        import re

        # Extract annotations like @Service, @RestController, etc.
        annotation_pattern = r"@(\w+)(?:\([^)]*\))?"
        annotations = re.findall(annotation_pattern, self._annotations_text)

        for annotation in annotations:
            if annotation in (
                "Service",
                "Controller",
                "RestController",
                "Repository",
                "Component",
                "Configuration",
            ):
                modifiers.append(MockAnnotation(f"@{annotation}"))
            elif annotation in ("RequestMapping"):
                # Extract RequestMapping with path
                mapping_match = re.search(
                    r"@RequestMapping\s*\(\s*\"([^\"]+)\"\s*\)", self._annotations_text
                )
                if mapping_match:
                    modifiers.append(
                        MockRequestMappingAnnotation(
                            "RequestMapping", f'"{mapping_match.group(1)}"'
                        )
                    )

        return modifiers


class MockRequestMappingAnnotation(MockAnnotation):
    """Mock @RequestMapping annotation"""

    def __init__(self, annotation_name, params=""):
        super().__init__(f"@{annotation_name}")
        self.annotation_name = annotation_name
        self.params = params
        self.path = self._extract_path(params)

    def _extract_path(self, params):
        """Extract path from annotation parameters"""
        if not params:
            return ""
        # Remove quotes and extract path
        import re

        path_match = re.search(r'["\']([^"\']+)["\']', params)
        if path_match:
            return path_match.group(1)
        return params.strip("\"'")

    def getTypeName(self):
        return MockQualifiedName(self.annotation_name)

    def values(self):
        if self.path:
            return [MockAnnotationMemberValuePair("value", self.path)]
        return []

    def isSingleMemberAnnotation(self):
        return bool(self.path)

    def isNormalAnnotation(self):
        return False

    def getValue(self):
        return MockStringLiteral(self.path) if self.path else None


class MockQualifiedName:
    """Mock qualified name"""

    def __init__(self, name):
        self.name = name

    def getFullyQualifiedName(self):
        return self.name


class MockFieldDeclaration:
    """Mock field declaration"""

    def __init__(self, java_type, field_name, class_body):
        self.java_type = java_type
        self.field_name = field_name
        self.class_body = class_body
        self._fragments = [MockVariableDeclarationFragment(field_name)]
        self._modifiers = self._extract_modifiers()

    def getNodeType(self):
        return self.FIELD_DECLARATION

    FIELD_DECLARATION = "FIELD_DECLARATION"

    def fragments(self):
        return self._fragments

    def getType(self):
        return MockSimpleType(self.java_type)

    def modifiers(self):
        return self._modifiers

    def _extract_modifiers(self):
        """Extract annotations and modifiers for this field"""
        modifiers = []
        import re

        # Find field declaration with annotations
        field_pattern = rf"((?:@\w+(?:\([^)]*\))?\s+)*)private\s+{self.java_type}\s+{self.field_name}\s*;"
        match = re.search(field_pattern, self.class_body)
        if match:
            annotations_text = match.group(1)
            # Extract individual annotations with parameters
            annotation_pattern = r"@(\w+)(?:\(([^)]*)\))?"
            annotation_matches = re.findall(annotation_pattern, annotations_text)

            for annotation_name, params_text in annotation_matches:
                if annotation_name == "Column":
                    modifiers.append(MockColumnAnnotation(params_text))
                elif annotation_name == "Table":
                    modifiers.append(MockTableAnnotation(params_text))
                elif annotation_name == "JoinColumn":
                    modifiers.append(MockJoinColumnAnnotation(params_text))
                elif annotation_name == "Enumerated":
                    modifiers.append(MockEnumeratedAnnotation(params_text))
                else:
                    modifiers.append(MockAnnotation(f"@{annotation_name}"))

        return modifiers


class MockSimpleType:
    """Mock simple type"""

    def __init__(self, type_name):
        self.type_name = type_name

    def toString(self):
        return self.type_name


class MockMethodDeclaration:
    """Mock method declaration for Spring Boot methods"""

    METHOD_DECLARATION = "METHOD_DECLARATION"

    def __init__(self, method_text, class_body):
        self.method_text = method_text
        self.class_body = class_body
        self._name = None
        self._return_type = None
        self._parameters = []
        self._modifiers = []
        self._parse_method()

    def _parse_method(self):
        """Parse method signature"""
        import re

        # Extract method signature: @Annotations public ReturnType methodName(params) {
        method_pattern = r"((?:@\w+(?:\([^)]*\))?\s+)*)(public|private|protected)?\s*(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)"
        match = re.search(method_pattern, self.method_text)

        if match:
            annotations_text = match.group(1) or ""
            self._return_type = match.group(3)
            self._name = match.group(4)
            params_text = match.group(5)

            # Parse annotations
            annotation_pattern = r"@(\w+)(?:\(([^)]*)\))?"
            annotation_matches = re.findall(annotation_pattern, annotations_text)

            for annotation_name, params in annotation_matches:
                if annotation_name in (
                    "GetMapping",
                    "PostMapping",
                    "PutMapping",
                    "DeleteMapping",
                    "PatchMapping",
                    "RequestMapping",
                ):
                    self._modifiers.append(
                        MockRequestMappingAnnotation(annotation_name, params)
                    )
                elif annotation_name == "Bean":
                    self._modifiers.append(MockAnnotation("@Bean"))
                else:
                    self._modifiers.append(MockAnnotation(f"@{annotation_name}"))

            # Parse parameters
            if params_text.strip():
                param_pattern = r"(@\w+(?:\([^)]*\))?\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)"
                param_matches = re.findall(param_pattern, params_text)
                self._parameters = [
                    MockParameter(param_type, param_name, annotations)
                    for annotations, param_type, param_name in param_matches
                ]

    def getNodeType(self):
        return self.METHOD_DECLARATION

    def getName(self):
        return MockSimpleName(self._name or "unknown")

    def getReturnType2(self):
        return MockSimpleType(self._return_type or "void")

    def parameters(self):
        return self._parameters

    def modifiers(self):
        return self._modifiers


class MockInterfaceMethodDeclaration:
    """Mock method declaration for interface methods (no body)"""

    METHOD_DECLARATION = "METHOD_DECLARATION"

    def __init__(self, method_text, interface_body):
        self.method_text = method_text
        self.interface_body = interface_body
        self._name = None
        self._return_type = None
        self._parameters = []
        self._modifiers = []
        self._parse_interface_method()

    def _parse_interface_method(self):
        """Parse interface method signature"""
        import re

        # Extract method signature: @Annotations Type methodName(params);
        method_pattern = (
            r"((?:@\w+(?:\([^)]*\))?\s*)*)(\w+(?:<[^>]+>)?)\s+(\w+)\s*\((.*?)\)\s*;"
        )
        match = re.search(method_pattern, self.method_text)

        if match:
            annotations_text = match.group(1) or ""
            self._return_type = match.group(2)
            self._name = match.group(3)
            params_text = match.group(4)

            # Parse annotations
            annotation_pattern = r"@(\w+)(?:\(([^)]*)\))?"
            annotation_matches = re.findall(annotation_pattern, annotations_text)

            for annotation_name, params in annotation_matches:
                if annotation_name == "Query":
                    self._modifiers.append(MockAnnotation("@Query"))
                else:
                    self._modifiers.append(MockAnnotation(f"@{annotation_name}"))

            # Parse parameters
            if params_text.strip():
                param_pattern = r"(@\w+(?:\([^)]*\))?\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)"
                param_matches = re.findall(param_pattern, params_text)
                self._parameters = [
                    MockParameter(param_type, param_name, annotations)
                    for annotations, param_type, param_name in param_matches
                ]

    def getNodeType(self):
        return self.METHOD_DECLARATION

    def getName(self):
        return MockSimpleName(self._name or "unknown")

    def getReturnType2(self):
        return MockSimpleType(self._return_type or "void")

    def parameters(self):
        return self._parameters

    def modifiers(self):
        return self._modifiers


class MockParameter:
    """Mock method parameter"""

    def __init__(self, param_type, param_name, annotations=""):
        self.param_type = param_type
        self.param_name = param_name
        self.annotations = annotations

    def getName(self):
        return MockSimpleName(self.param_name)

    def getType(self):
        return MockSimpleType(self.param_type)

    def modifiers(self):
        """Return any parameter annotations like @PathVariable, @RequestBody"""
        modifiers = []
        if "@" in self.annotations:
            import re

            annotation_pattern = r"@(\w+)(?:\(([^)]*)\))?"
            matches = re.findall(annotation_pattern, self.annotations)
            for annotation_name, params in matches:
                modifiers.append(MockAnnotation(f"@{annotation_name}"))
        return modifiers


class MockVariableDeclarationFragment:
    """Mock variable declaration fragment"""

    def __init__(self, name):
        self.name = name

    def getName(self):
        return MockSimpleName(self.name)


# Singleton instance
_jdt_bridge: Optional[JDTBridge] = None


def get_jdt_bridge() -> JDTBridge:
    """Get singleton JDT bridge instance"""
    global _jdt_bridge
    if _jdt_bridge is None:
        _jdt_bridge = JDTBridge()
    return _jdt_bridge
