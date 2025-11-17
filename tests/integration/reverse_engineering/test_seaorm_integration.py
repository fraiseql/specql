import pytest
from pathlib import Path
from src.reverse_engineering.rust_parser import RustReverseEngineeringService


class TestSeaORMIntegration:
    """Integration tests for SeaORM support in Rust reverse engineering"""

    def test_seaorm_entity_integration(self):
        """Test full SeaORM entity parsing and conversion to SpecQL"""
        code = """
        use sea_orm::entity::prelude::*;

        #[derive(Clone, Debug, PartialEq, DeriveEntityModel)]
        #[sea_orm(table_name = "contacts")]
        pub struct Model {
            #[sea_orm(primary_key)]
            pub id: i32,

            #[sea_orm(unique)]
            pub email: String,

            #[sea_orm(column_type = "String(Some(50))")]
            pub status: String,

            pub created_at: DateTime,
            pub updated_at: DateTime,
        }

        #[derive(Copy, Clone, Debug, EnumIter, DeriveRelation)]
        pub enum Relation {
            #[sea_orm(has_many = "super::companies::Entity")]
            Companies,
        }
        """

        # Create temporary file
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            service = RustReverseEngineeringService()
            entities = service.reverse_engineer_file(Path(temp_path))

            assert len(entities) == 1
            entity = entities[0]

            assert entity.name == "Contact"
            assert entity.table == "contacts"
            assert entity.schema == "crm"
            assert len(entity.fields) == 5

            # Check fields
            assert "id" in entity.fields
            assert "email" in entity.fields
            assert "status" in entity.fields
            assert "created_at" in entity.fields
            assert "updated_at" in entity.fields

            # Check field types
            assert entity.fields["id"].type_name == "integer"
            assert entity.fields["email"].type_name == "text"
            assert entity.fields["status"].type_name == "text"
            assert entity.fields["created_at"].type_name == "timestamp"
            assert entity.fields["updated_at"].type_name == "timestamp"

        finally:
            os.unlink(temp_path)

    def test_orm_detection_seaorm(self):
        """Test ORM type detection for SeaORM"""
        service = RustReverseEngineeringService()

        seaorm_code = """
        use sea_orm::entity::prelude::*;

        #[derive(DeriveEntityModel)]
        #[sea_orm(table_name = "test")]
        pub struct Model {
            pub id: i32,
        }
        """

        assert service._detect_orm_type(seaorm_code) == "seaorm"

    def test_orm_detection_diesel(self):
        """Test ORM type detection for Diesel"""
        service = RustReverseEngineeringService()

        diesel_code = """
        use diesel::prelude::*;

        table! {
            test (id) {
                id -> Integer,
                name -> Text,
            }
        }
        """

        assert service._detect_orm_type(diesel_code) == "diesel"

    def test_orm_detection_unknown(self):
        """Test ORM type detection for unknown ORM"""
        service = RustReverseEngineeringService()

        unknown_code = """
        pub struct Test {
            pub id: i32,
        }
        """

        assert service._detect_orm_type(unknown_code) == "unknown"
