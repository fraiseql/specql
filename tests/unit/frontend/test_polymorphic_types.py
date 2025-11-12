"""
Tests for TypeScript type generation from polymorphic patterns.
"""


from src.generators.frontend.polymorphic_types_generator import generate_polymorphic_types


class TestPolymorphicTypesGenerator:
    """Test TypeScript type generation for polymorphic patterns."""

    def test_generate_basic_polymorphic_types(self):
        """Test generating TypeScript types for a basic polymorphic pattern."""
        pattern_config = {
            "name": "pk_class_resolver",
            "config": {
                "discriminator_field": "class",
                "variants": [
                    {
                        "entity": {"schema": "tenant", "table": "tb_product"},
                        "key_field": "pk_product",
                        "class_value": "product",
                    },
                    {
                        "entity": {"schema": "tenant", "table": "tb_contract_item"},
                        "key_field": "pk_contract_item",
                        "class_value": "contract_item",
                    },
                ],
                "output_key": "pk_value",
            },
        }

        result = generate_polymorphic_types(pattern_config)

        # Check that the result contains expected TypeScript code
        assert "export interface PkClassResolverTypeResolver" in result
        assert "pk_value: string;" in result
        assert "class: 'product' | 'contract_item';" in result
        assert "export type PkClassResolverType =" in result
        assert "{ class: 'product'; data: Product }" in result
        assert "{ class: 'contract_item'; data: ContractItem }" in result
        assert "export function isPkClassResolverProduct" in result
        assert "export function isPkClassResolverContractItem" in result

    def test_generate_types_with_custom_output_key(self):
        """Test generating types with a custom output key."""
        pattern_config = {
            "name": "entity_resolver",
            "config": {
                "discriminator_field": "type",
                "variants": [
                    {
                        "entity": {"schema": "tenant", "table": "tb_user"},
                        "key_field": "id",
                        "class_value": "user",
                    }
                ],
                "output_key": "entity_id",
            },
        }

        result = generate_polymorphic_types(pattern_config)

        assert "entity_id: string;" in result
        assert "type: 'user';" in result

    def test_generate_types_with_multiple_variants(self):
        """Test generating types with multiple entity variants."""
        pattern_config = {
            "name": "multi_entity_resolver",
            "config": {
                "discriminator_field": "entity_type",
                "variants": [
                    {
                        "entity": {"schema": "tenant", "table": "tb_customer"},
                        "key_field": "customer_id",
                        "class_value": "customer",
                    },
                    {
                        "entity": {"schema": "tenant", "table": "tb_supplier"},
                        "key_field": "supplier_id",
                        "class_value": "supplier",
                    },
                    {
                        "entity": {"schema": "tenant", "table": "tb_partner"},
                        "key_field": "partner_id",
                        "class_value": "partner",
                    },
                ],
                "output_key": "entity_id",
            },
        }

        result = generate_polymorphic_types(pattern_config)

        # Check discriminator union
        assert "entity_type: 'customer' | 'supplier' | 'partner';" in result

        # Check union type cases
        assert "{ entity_type: 'customer'; data: Customer }" in result
        assert "{ entity_type: 'supplier'; data: Supplier }" in result
        assert "{ entity_type: 'partner'; data: Partner }" in result

        # Check type guards
        assert "isMultiEntityResolverCustomer" in result
        assert "isMultiEntityResolverSupplier" in result
        assert "isMultiEntityResolverPartner" in result

    def test_pascal_case_conversion(self):
        """Test that snake_case pattern names are converted to PascalCase."""
        pattern_config = {
            "name": "my_complex_pattern_name",
            "config": {
                "discriminator_field": "type",
                "variants": [
                    {
                        "entity": {"schema": "tenant", "table": "tb_test"},
                        "key_field": "id",
                        "class_value": "test",
                    }
                ],
            },
        }

        result = generate_polymorphic_types(pattern_config)

        assert "MyComplexPatternNameTypeResolver" in result
        assert "MyComplexPatternNameType" in result
        assert "isMyComplexPatternNameTest" in result
