import pytest
from src.reverse_engineering.seaorm_parser import SeaORMParser


class TestSeaORMParser:
    """Test SeaORM entity and query detection"""

    def test_detect_seaorm_entity(self):
        """Test detecting SeaORM entity model"""
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

        parser = SeaORMParser()
        entities = parser.extract_entities(code)

        assert len(entities) == 1
        entity = entities[0]
        assert entity.name == "Contact"  # Inferred from table_name
        assert entity.table_name == "contacts"
        assert len(entity.fields) == 5
        assert entity.primary_key == "id"
        assert "email" in [f.name for f in entity.fields]
        assert entity.has_relations == True

    def test_detect_seaorm_fields_with_attributes(self):
        """Test extracting field attributes"""
        code = """
        #[derive(Clone, Debug, PartialEq, DeriveEntityModel)]
        #[sea_orm(table_name = "contacts")]
        pub struct Model {
            #[sea_orm(primary_key, auto_increment = true)]
            pub id: i32,

            #[sea_orm(unique, indexed)]
            pub email: String,

            #[sea_orm(default_value = "lead")]
            pub status: String,

            #[sea_orm(nullable)]
            pub deleted_at: Option<DateTime>,
        }
        """

        parser = SeaORMParser()
        entities = parser.extract_entities(code)

        assert len(entities) == 1
        fields = entities[0].fields

        # Check field attributes
        id_field = next(f for f in fields if f.name == "id")
        assert id_field.is_primary_key == True
        assert id_field.auto_increment == True

        email_field = next(f for f in fields if f.name == "email")
        assert email_field.is_unique == True
        assert email_field.is_indexed == True

        status_field = next(f for f in fields if f.name == "status")
        assert status_field.default_value == "lead"

        deleted_field = next(f for f in fields if f.name == "deleted_at")
        assert deleted_field.is_nullable == True


class TestSeaORMQueries:
    """Test SeaORM query detection"""

    def test_detect_find_queries(self):
        """Test detecting find operations"""
        code = """
        use sea_orm::*;

        pub async fn get_contact(db: &DatabaseConnection, id: i32) -> Result<Option<Model>, DbErr> {
            Contact::find_by_id(id)
                .one(db)
                .await
        }

        pub async fn list_contacts(db: &DatabaseConnection) -> Result<Vec<Model>, DbErr> {
            Contact::find()
                .filter(Column::Status.eq("active"))
                .order_by_asc(Column::CreatedAt)
                .all(db)
                .await
        }
        """

        parser = SeaORMParser()
        queries = parser.extract_queries(code)

        assert len(queries) == 2
        assert queries[0].operation == "find_by_id"
        assert queries[0].entity == "Contact"
        assert queries[1].operation == "find"
        assert queries[1].has_filter == True

    def test_detect_insert_queries(self):
        """Test detecting insert operations"""
        code = """
        pub async fn create_contact(db: &DatabaseConnection, data: ContactDTO) -> Result<Model, DbErr> {
            let contact = ActiveModel {
                email: Set(data.email),
                status: Set("lead".to_string()),
                ..Default::default()
            };

            Contact::insert(contact)
                .exec_with_returning(db)
                .await
        }
        """

        parser = SeaORMParser()
        queries = parser.extract_queries(code)

        assert len(queries) == 1
        assert queries[0].operation == "insert"
        assert queries[0].entity == "Contact"

    def test_detect_update_queries(self):
        """Test detecting update operations"""
        code = """
        pub async fn update_contact(db: &DatabaseConnection, id: i32, status: String) -> Result<Model, DbErr> {
            let mut contact: ActiveModel = Contact::find_by_id(id)
                .one(db)
                .await?
                .unwrap()
                .into();

            contact.status = Set(status);

            contact.update(db).await
        }

        pub async fn bulk_update(db: &DatabaseConnection) -> Result<UpdateResult, DbErr> {
            Contact::update_many()
                .col_expr(Column::Status, Expr::value("qualified"))
                .filter(Column::Id.eq(1))
                .exec(db)
                .await
        }
        """

        parser = SeaORMParser()
        queries = parser.extract_queries(code)

        assert len(queries) >= 2
        update_queries = [q for q in queries if "update" in q.operation]
        assert len(update_queries) >= 1

    def test_detect_delete_queries(self):
        """Test detecting delete operations"""
        code = """
        pub async fn delete_contact(db: &DatabaseConnection, id: i32) -> Result<DeleteResult, DbErr> {
            Contact::delete_by_id(id)
                .exec(db)
                .await
        }

        pub async fn delete_many(db: &DatabaseConnection) -> Result<DeleteResult, DbErr> {
            Contact::delete_many()
                .filter(Column::DeletedAt.is_not_null())
                .exec(db)
                .await
        }
        """

        parser = SeaORMParser()
        queries = parser.extract_queries(code)

        assert len(queries) == 2
        assert all(q.operation.startswith("delete") for q in queries)
