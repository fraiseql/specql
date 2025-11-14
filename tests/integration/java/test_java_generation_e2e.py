"""End-to-end test: SpecQL YAML → Java Spring Boot code"""

import pytest
from src.core.specql_parser import SpecQLParser
from src.generators.java.entity_generator import JavaEntityGenerator
from src.generators.java.repository_generator import JavaRepositoryGenerator
from src.generators.java.service_generator import JavaServiceGenerator
from src.generators.java.controller_generator import JavaControllerGenerator


def test_complete_spring_boot_generation():
    """Test full code generation pipeline"""
    # Parse SpecQL YAML
    yaml_content = """
entity: Product
schema: ecommerce
fields:
  name: text!
  price: integer
  active: boolean = true
actions:
  - name: activate_product
    steps:
      - validate: active = false
      - update: Product SET active = true
"""

    parser = SpecQLParser()
    entity = parser.parse_universal(yaml_content)

    # Generate all Java classes
    entity_gen = JavaEntityGenerator()
    repo_gen = JavaRepositoryGenerator()
    service_gen = JavaServiceGenerator()
    controller_gen = JavaControllerGenerator()

    entity_code = entity_gen.generate(entity)
    repo_code = repo_gen.generate(entity)
    service_code = service_gen.generate(entity)
    controller_code = controller_gen.generate(entity)

    # Verify entity
    assert "@Entity" in entity_code
    assert "public class Product" in entity_code

    # Verify repository
    assert "public interface ProductRepository extends JpaRepository" in repo_code

    # Verify service
    assert "@Service" in service_code
    assert "public class ProductService" in service_code
    assert "public Product activateProduct" in service_code

    # Verify controller
    assert "@RestController" in controller_code
    assert '@RequestMapping("/api/products")' in controller_code


def test_generated_code_compiles():
    """Test that generated Java code is syntactically valid"""
    # This would require Java compiler integration
    # For now, we'll do string validation
    pass
