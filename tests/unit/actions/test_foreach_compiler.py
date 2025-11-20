"""
Unit tests for ForEachStepCompiler
"""

import pytest

from core.ast_models import ActionStep, EntityDefinition, FieldDefinition
from generators.actions.step_compilers.foreach_compiler import ForEachStepCompiler


class TestForEachStepCompiler:
    """Test ForEachStepCompiler functionality"""

    def setup_method(self):
        """Set up test fixtures"""

        # Mock step compiler class
        class MockUpdateCompiler:
            def compile(self, step, entity, context):
                return f"-- Mock update: {getattr(step, 'fields', {})}"

        # Mock step compiler registry
        self.mock_registry = {"update": MockUpdateCompiler()}
        self.compiler = ForEachStepCompiler(step_compiler_registry=self.mock_registry)

        # Mock entity for testing
        self.mock_entity = EntityDefinition(
            name="Contact",
            schema="crm",
            fields={
                "email": FieldDefinition(name="email", type_name="text"),
                "first_name": FieldDefinition(name="first_name", type_name="text"),
            },
        )

    def test_compile_foreach_with_related_entities(self):
        """Test foreach compilation with related entities"""
        step = ActionStep(
            type="foreach",
            foreach_expr="item in related_orders",
            then_steps=[
                ActionStep(
                    type="update",
                    entity="Order",
                    fields={"status": "processed"},
                    where_clause="id = item.id",
                )
            ],
        )

        context = {}
        result = self.compiler.compile(step, self.mock_entity, context)

        # Should generate a FOR loop over related orders
        assert "FOR item IN" in result
        assert "related_orders" in result
        assert "END LOOP;" in result

    def test_parse_foreach_expression(self):
        """Test parsing of foreach expressions"""
        # Test valid expression
        iterator_var, collection_expr = self.compiler._parse_foreach_expression(
            "item in related_orders"
        )
        assert iterator_var == "item"
        assert collection_expr == "related_orders"

        # Test invalid expression
        with pytest.raises(ValueError, match="Invalid foreach expression"):
            self.compiler._parse_foreach_expression("invalid_expression")

    def test_invalid_step_type(self):
        """Test error handling for wrong step type"""
        step = ActionStep(type="invalid", foreach_expr="item in collection")

        with pytest.raises(ValueError, match="Expected foreach step"):
            self.compiler.compile(step, self.mock_entity, {})

    def test_missing_foreach_attributes(self):
        """Test error handling for missing foreach attributes"""
        step = ActionStep(type="foreach")  # No foreach_expr, iterator_var, or collection

        with pytest.raises(ValueError, match="Foreach step must have either"):
            self.compiler.compile(step, self.mock_entity, {})

    def test_generate_iteration_query_related_entities(self):
        """Test query generation for related entities"""
        query = self.compiler._generate_iteration_query("related_orders", self.mock_entity, {})
        expected = "        SELECT * FROM crm.tb_order\n        WHERE fk_contact = v_pk"
        assert expected in query

    def test_unsupported_collection_expression(self):
        """Test error handling for unsupported collection expressions"""
        # Input field references are not yet supported
        with pytest.raises(NotImplementedError):
            self.compiler._generate_iteration_query("input.related_items", self.mock_entity, {})

    def test_generate_iteration_query_complex_table_reference(self):
        """Test query generation for complex table references like schema.table"""
        query = self.compiler._generate_iteration_query("complex.expression", self.mock_entity, {})
        assert "SELECT * FROM complex.expression" in query

    def test_compile_foreach_with_subquery(self):
        """Test foreach compilation with subquery collections"""
        step = ActionStep(
            type="foreach",
            foreach_expr="order_item in (SELECT * FROM crm.tb_order WHERE total > 1000)",
            then_steps=[
                ActionStep(
                    type="update",
                    entity="Order",
                    fields={"status": "high_value"},
                    where_clause="id = order_item.id",
                )
            ],
        )

        context = {}
        result = self.compiler.compile(step, self.mock_entity, context)

        # Should generate a FOR loop using the subquery
        assert "FOR order_item IN" in result
        assert "SELECT * FROM crm.tb_order WHERE total > 1000" in result
        assert "END LOOP;" in result

    def test_generate_iteration_query_subquery(self):
        """Test query generation for subquery collections"""
        subquery = "(SELECT * FROM crm.tb_order WHERE total > 1000)"
        query = self.compiler._generate_iteration_query(subquery, self.mock_entity, {})
        assert subquery in query

    def test_generate_iteration_query_select_only(self):
        """Test query generation for SELECT statements without parentheses"""
        select_query = "SELECT * FROM crm.tb_order WHERE status = 'pending'"
        query = self.compiler._generate_iteration_query(select_query, self.mock_entity, {})
        assert select_query in query

    def test_generate_iteration_query_table_reference(self):
        """Test query generation for direct table references"""
        query = self.compiler._generate_iteration_query("crm.tb_orders", self.mock_entity, {})
        assert "SELECT * FROM crm.tb_orders" in query

    def test_generate_iteration_query_simple_table(self):
        """Test query generation for simple table names (fallback)"""
        query = self.compiler._generate_iteration_query("orders", self.mock_entity, {})
        assert "SELECT * FROM crm.orders" in query
