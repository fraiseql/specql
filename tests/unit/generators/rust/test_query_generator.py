"""
Tests for Diesel query builder generation
"""

import pytest
from src.generators.rust.query_generator import RustQueryGenerator
from src.core.ast_models import Entity, FieldDefinition


class TestBasicCrudQueries:
    """Test generation of basic CRUD query methods"""

    @pytest.fixture
    def generator(self):
        return RustQueryGenerator()

    @pytest.fixture
    def simple_entity(self):
        return Entity(
            name="Contact",
            schema="crm",
            fields={
                "email": FieldDefinition(
                    name="email", type_name="text", nullable=False
                ),
                "phone": FieldDefinition(name="phone", type_name="text", nullable=True),
                "active": FieldDefinition(
                    name="active", type_name="boolean", nullable=False
                ),
            },
        )

    def test_generate_find_by_id(self, generator, simple_entity):
        """Test find_by_id query generation"""
        result = generator.generate_find_by_id(simple_entity)

        # Method signature
        assert "pub fn find_by_id(" in result
        assert "conn: &mut PgConnection" in result
        assert "contact_id: Uuid" in result
        assert ") -> QueryResult<Contact>" in result

        # Query structure
        assert "tb_contact::table" in result
        assert "filter(tb_contact::id.eq(contact_id))" in result
        assert "filter(tb_contact::deleted_at.is_null())" in result
        assert "first::<Contact>(conn)" in result

    def test_generate_list_active(self, generator, simple_entity):
        """Test list_active query generation"""
        result = generator.generate_list_active(simple_entity)

        # Method signature
        assert "pub fn list_active(" in result
        assert "conn: &mut PgConnection" in result
        assert ") -> QueryResult<Vec<Contact>>" in result

        # Query structure
        assert "tb_contact::table" in result
        assert "filter(tb_contact::deleted_at.is_null())" in result
        assert "order(tb_contact::created_at.desc())" in result
        assert "load::<Contact>(conn)" in result

    def test_generate_create(self, generator, simple_entity):
        """Test create query generation"""
        result = generator.generate_create(simple_entity)

        # Method signature
        assert "pub fn create(" in result
        assert "conn: &mut PgConnection" in result
        assert "new_contact: NewContact" in result
        assert ") -> QueryResult<Contact>" in result

        # Query structure
        assert "diesel::insert_into(tb_contact::table)" in result
        assert "values(&new_contact)" in result
        assert "get_result::<Contact>(conn)" in result

    def test_generate_update(self, generator, simple_entity):
        """Test update query generation"""
        result = generator.generate_update(simple_entity)

        # Method signature
        assert "pub fn update(" in result
        assert "conn: &mut PgConnection" in result
        assert "contact_id: Uuid" in result
        assert "changeset: UpdateContact" in result
        assert ") -> QueryResult<Contact>" in result

        # Query structure
        assert "diesel::update(tb_contact::table)" in result
        assert "filter(tb_contact::id.eq(contact_id))" in result
        assert "set(&changeset)" in result
        assert "get_result::<Contact>(conn)" in result

    def test_generate_soft_delete(self, generator, simple_entity):
        """Test soft delete query generation"""
        result = generator.generate_soft_delete(simple_entity)

        # Method signature
        assert "pub fn soft_delete(" in result
        assert "conn: &mut PgConnection" in result
        assert "contact_id: Uuid" in result
        assert ") -> QueryResult<Contact>" in result

        # Query structure
        assert "diesel::update(tb_contact::table)" in result
        assert "filter(tb_contact::id.eq(contact_id))" in result
        assert "set(tb_contact::deleted_at.eq(Utc::now().naive_utc()))" in result
        assert "get_result::<Contact>(conn)" in result

    def test_generate_hard_delete(self, generator, simple_entity):
        """Test hard delete query generation"""
        result = generator.generate_hard_delete(simple_entity)

        # Method signature
        assert "pub fn hard_delete(" in result
        assert "conn: &mut PgConnection" in result
        assert "contact_id: Uuid" in result
        assert ") -> QueryResult<usize>" in result

        # Query structure
        assert "diesel::delete(tb_contact::table)" in result
        assert "filter(tb_contact::id.eq(contact_id))" in result
        assert "execute(conn)" in result

    def test_generate_query_struct(self, generator, simple_entity):
        """Test complete query struct generation"""
        result = generator.generate_query_struct(simple_entity)

        # Struct declaration
        assert "pub struct ContactQueries;" in result
        assert "impl ContactQueries {" in result

        # All methods included
        assert "find_by_id" in result
        assert "list_active" in result
        assert "create" in result
        assert "update" in result
        assert "soft_delete" in result
        assert "hard_delete" in result

    def test_generate_imports(self, generator, simple_entity):
        """Test required imports are generated"""
        result = generator.generate_imports(simple_entity)

        assert "use diesel::prelude::*;" in result
        assert "use diesel::result::QueryResult;" in result
        assert "use uuid::Uuid;" in result
        assert "use super::models::{Contact, NewContact, UpdateContact};" in result
        assert "use super::schema::crm::tb_contact;" in result


class TestRelationshipQueries:
    """Test generation of relationship-based query methods"""

    @pytest.fixture
    def generator(self):
        return RustQueryGenerator()

    @pytest.fixture
    def contact_entity(self):
        return Entity(
            name="Contact",
            schema="crm",
            fields={
                "email": FieldDefinition(
                    name="email", type_name="text", nullable=False
                ),
                "company": FieldDefinition(
                    name="company",
                    type_name="ref",
                    reference_entity="Company",
                    nullable=True,
                ),
            },
        )

    @pytest.fixture
    def company_entity(self):
        return Entity(
            name="Company",
            schema="crm",
            fields={
                "name": FieldDefinition(name="name", type_name="text", nullable=False),
            },
        )

    def test_generate_find_by_foreign_key(self, generator, contact_entity):
        """Test find by foreign key query generation"""
        result = generator.generate_find_by_foreign_key(
            contact_entity, "company", "Company"
        )

        # Method signature
        assert "pub fn find_by_company(" in result
        assert "conn: &mut PgConnection" in result
        assert "company_id: Uuid" in result
        assert ") -> QueryResult<Vec<Contact>>" in result

        # Query structure
        assert (
            "inner_join(tb_company::table.on(tb_contact::fk_company.eq(tb_company::pk_company)))"
            in result
        )
        assert "filter(tb_company::id.eq(company_id))" in result
        assert "filter(tb_contact::deleted_at.is_null())" in result
        assert "select(Contact::as_select())" in result
        assert "load::<Contact>(conn)" in result

    def test_generate_find_children(self, generator, company_entity):
        """Test find children query generation"""
        result = generator.generate_find_children(company_entity, "contacts", "Contact")

        # Method signature
        assert "pub fn find_contacts(" in result
        assert "conn: &mut PgConnection" in result
        assert "company_id: Uuid" in result
        assert ") -> QueryResult<Vec<Contact>>" in result

        # Query structure
        assert (
            "inner_join(tb_contact::table.on(tb_company::pk_company.eq(tb_contact::fk_company)))"
            in result
        )
        assert "filter(tb_company::id.eq(company_id))" in result
        assert "filter(tb_contact::deleted_at.is_null())" in result
        assert "select(Contact::as_select())" in result

    def test_generate_relationship_imports(self, generator, contact_entity):
        """Test imports include related entities"""
        result = generator.generate_relationship_imports(contact_entity, ["Company"])

        assert "use super::models::Contact;" in result
        assert "use super::schema::crm::{tb_contact, tb_company};" in result

    def test_generate_relationship_queries(self, generator, contact_entity):
        """Test complete relationship queries generation"""
        result = generator.generate_relationship_queries(contact_entity)

        # Should include find_by_company method
        assert "find_by_company" in result
        assert "inner_join" in result
        assert "tb_company::table" in result
