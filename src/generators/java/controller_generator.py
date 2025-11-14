"""Generate Spring @RestController classes"""

from typing import List
from src.core.universal_ast import UniversalEntity


class JavaControllerGenerator:
    """Generates Spring @RestController classes"""

    def generate(self, entity: UniversalEntity) -> str:
        """Generate complete REST controller"""
        lines = []

        # Package
        lines.append(f"package {entity.schema}.controller;")
        lines.append("")

        # Imports
        lines.extend(self._generate_imports(entity))
        lines.append("")

        # Class declaration
        lines.append("@RestController")
        lines.append(f'@RequestMapping("/api/{entity.name.lower()}s")')
        lines.append(f"public class {entity.name}Controller {{")
        lines.append("")

        # Service injection
        lines.extend(self._generate_dependencies(entity))
        lines.append("")

        # Constructor
        lines.extend(self._generate_constructor(entity))
        lines.append("")

        # REST endpoints
        lines.extend(self._generate_rest_endpoints(entity))

        lines.append("}")

        return "\n".join(lines)

    def _generate_imports(self, entity: UniversalEntity) -> List[str]:
        """Generate import statements"""
        return [
            "import org.springframework.http.HttpStatus;",
            "import org.springframework.http.ResponseEntity;",
            "import org.springframework.web.bind.annotation.*;",
            "import org.springframework.web.bind.annotation.RestController;",
            "import javax.validation.Valid;",
            f"import {entity.schema}.{entity.name};",
            f"import {entity.schema}.service.{entity.name}Service;",
            "import java.util.List;",
        ]

    def _generate_dependencies(self, entity: UniversalEntity) -> List[str]:
        """Generate service field"""
        service_field = f"{entity.name.lower()}Service"
        return [
            f"    private final {entity.name}Service {service_field};",
        ]

    def _generate_constructor(self, entity: UniversalEntity) -> List[str]:
        """Generate constructor with dependency injection"""
        service_field = f"{entity.name.lower()}Service"
        return [
            f"    public {entity.name}Controller({entity.name}Service {service_field}) {{",
            f"        this.{service_field} = {service_field};",
            "    }",
        ]

    def _generate_rest_endpoints(self, entity: UniversalEntity) -> List[str]:
        """Generate CRUD REST endpoints"""
        lines = []
        service = f"{entity.name.lower()}Service"

        # POST - Create
        lines.append("    @PostMapping")
        lines.append(
            f"    public ResponseEntity<{entity.name}> create(@Valid @RequestBody {entity.name} {entity.name.lower()}) {{"
        )
        lines.append(
            f"        {entity.name} created = {service}.create({entity.name.lower()});"
        )
        lines.append(
            "        return ResponseEntity.status(HttpStatus.CREATED).body(created);"
        )
        lines.append("    }")
        lines.append("")

        # GET - Read by ID
        lines.append('    @GetMapping("/{id}")')
        lines.append(
            f"    public ResponseEntity<{entity.name}> getById(@PathVariable Long id) {{"
        )
        lines.append(f"        return {service}.findById(id)")
        lines.append("            .map(ResponseEntity::ok)")
        lines.append("            .orElse(ResponseEntity.notFound().build());")
        lines.append("    }")
        lines.append("")

        # GET - List all
        lines.append("    @GetMapping")
        lines.append(f"    public List<{entity.name}> getAll() {{")
        lines.append(f"        return {service}.findAll();")
        lines.append("    }")
        lines.append("")

        # PUT - Update
        lines.append('    @PutMapping("/{id}")')
        lines.append(
            f"    public ResponseEntity<{entity.name}> update(@PathVariable Long id, @Valid @RequestBody {entity.name} {entity.name.lower()}) {{"
        )
        lines.append(
            f"        {entity.name} updated = {service}.update(id, {entity.name.lower()});"
        )
        lines.append("        return ResponseEntity.ok(updated);")
        lines.append("    }")
        lines.append("")

        # DELETE
        lines.append('    @DeleteMapping("/{id}")')
        lines.append("    public ResponseEntity<Void> delete(@PathVariable Long id) {")
        lines.append(f"        {service}.delete(id);")
        lines.append("        return ResponseEntity.noContent().build();")
        lines.append("    }")

        return lines
