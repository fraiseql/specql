"""
Integration tests for TypeScript parser.
"""

from src.parsers.typescript.typescript_parser import TypeScriptParser


class TestTypeScriptParser:
    """Test TypeScript parser functionality."""

    def test_parse_basic_interface(self):
        """Test parsing a basic TypeScript interface."""
        ts_code = """
        interface User {
          id: number;
          name: string;
          email: string;
        }
        """

        parser = TypeScriptParser()
        entities = parser.parse_content(ts_code)

        assert len(entities) == 1
        entity = entities[0]
        assert entity.name == "User"
        assert len(entity.fields) == 3

        # Check fields
        id_field = next(f for f in entity.fields if f.name == "id")
        assert id_field.type.value == "integer"
        assert id_field.required  is True

        name_field = next(f for f in entity.fields if f.name == "name")
        assert name_field.type.value == "text"
        assert name_field.required  is True

    def test_parse_optional_fields(self):
        """Test parsing optional fields."""
        ts_code = """
        interface Product {
          id: number;
          name: string;
          description?: string;
          price?: number;
        }
        """

        parser = TypeScriptParser()
        entities = parser.parse_content(ts_code)

        assert len(entities) == 1
        entity = entities[0]
        assert len(entity.fields) == 4

        # Required fields
        id_field = next(f for f in entity.fields if f.name == "id")
        assert id_field.required  is True

        name_field = next(f for f in entity.fields if f.name == "name")
        assert name_field.required  is True

        # Optional fields
        desc_field = next(f for f in entity.fields if f.name == "description")
        assert not desc_field.required

        price_field = next(f for f in entity.fields if f.name == "price")
        assert not price_field.required

    def test_parse_array_types(self):
        """Test parsing array types."""
        ts_code = """
        interface BlogPost {
          id: number;
          title: string;
          tags: string[];
          comments: Comment[];
        }
        """

        parser = TypeScriptParser()
        entities = parser.parse_content(ts_code)

        assert len(entities) == 1
        entity = entities[0]
        assert len(entity.fields) == 4

        tags_field = next(f for f in entity.fields if f.name == "tags")
        assert tags_field.type.value == "list"

        comments_field = next(f for f in entity.fields if f.name == "comments")
        assert comments_field.type.value == "list"

    def test_parse_union_types(self):
        """Test parsing union types (basic support)."""
        ts_code = """
        interface Settings {
          theme: 'light' | 'dark';
          status: 'active' | 'inactive' | 'pending';
          value: string | number;
        }
        """

        parser = TypeScriptParser()
        entities = parser.parse_content(ts_code)

        assert len(entities) == 1
        entity = entities[0]
        assert len(entity.fields) == 3

        # Union types should map to the first type (rich for complex unions)
        theme_field = next(f for f in entity.fields if f.name == "theme")
        assert theme_field.type.value == "rich"  # Union type falls back to rich

    def test_parse_type_aliases(self):
        """Test parsing type aliases."""
        ts_code = """
        type UserId = number;

        type UserProfile = {
          id: number;
          bio?: string;
          avatar?: string;
        };

        type ApiResponse<T> = {
          success: boolean;
          data?: T;
          error?: string;
        };
        """

        parser = TypeScriptParser()
        entities = parser.parse_content(ts_code)

        # Should parse the object type alias
        assert len(entities) == 1  # Only UserProfile (object type)
        entity = entities[0]
        assert entity.name == "UserProfile"
        assert len(entity.fields) == 3

    def test_parse_interface_with_extends(self):
        """Test parsing interfaces with extends clause."""
        ts_code = """
        interface BaseEntity {
          id: number;
          createdAt: Date;
          updatedAt: Date;
        }

        interface User extends BaseEntity {
          name: string;
          email: string;
        }
        """

        parser = TypeScriptParser()
        entities = parser.parse_content(ts_code)

        # Should parse both interfaces
        assert len(entities) == 2

        base_entity = next(e for e in entities if e.name == "BaseEntity")
        assert len(base_entity.fields) == 3

        user_entity = next(e for e in entities if e.name == "User")
        assert len(user_entity.fields) == 2  # Only own fields

    def test_parse_complex_types(self):
        """Test parsing complex TypeScript types."""
        ts_code = """
        interface ComplexEntity {
          id: number;
          metadata: Record<string, any>;
          settings: { theme: string; lang: string };
          callback: (data: any) => void;  // Should be ignored (method)
          tags: string[];
          optionalField?: boolean;
        }
        """

        parser = TypeScriptParser()
        entities = parser.parse_content(ts_code)

        assert len(entities) == 1
        entity = entities[0]
        assert len(entity.fields) == 5  # Should ignore method

        # Check field types
        metadata_field = next(f for f in entity.fields if f.name == "metadata")
        assert metadata_field.type.value == "rich"  # Record type

        settings_field = next(f for f in entity.fields if f.name == "settings")
        assert settings_field.type.value == "rich"  # Object type

        tags_field = next(f for f in entity.fields if f.name == "tags")
        assert tags_field.type.value == "list"  # Array type

    def test_ignore_methods_and_comments(self):
        """Test that methods and comments are properly ignored."""
        ts_code = """
        // This is a comment
        interface Service {
          id: number;
          name: string;

          // Method - should be ignored
          getData(): Promise<any>;

          /* Multi-line
             comment */
          processData(data: any): void;

          // Valid field
          status: string;
        }
        """

        parser = TypeScriptParser()
        entities = parser.parse_content(ts_code)

        assert len(entities) == 1
        entity = entities[0]
        assert len(entity.fields) == 3  # Only fields, no methods

        field_names = {f.name for f in entity.fields}
        assert field_names == {"id", "name", "status"}

    def test_parse_file_integration(self, tmp_path):
        """Test parsing from actual file."""
        ts_content = """
        interface TestEntity {
          id: number;
          title: string;
          active: boolean;
        }
        """

        ts_file = tmp_path / "test.ts"
        ts_file.write_text(ts_content)

        parser = TypeScriptParser()
        entities = parser.parse_file(str(ts_file))

        assert len(entities) == 1
        assert entities[0].name == "TestEntity"
        assert len(entities[0].fields) == 3

    def test_parse_enums(self):
        """Test parsing TypeScript enums."""
        ts_code = """
        enum Status {
          ACTIVE,
          INACTIVE,
          PENDING = 'pending',
          APPROVED = 1,
          REJECTED = 'rejected'
        }

        enum Priority {
          LOW = 1,
          MEDIUM,
          HIGH
        }
        """

        parser = TypeScriptParser()
        entities = parser.parse_content(ts_code)

        # Should parse 2 enums
        assert len(entities) == 2

        status_enum = next(e for e in entities if e.name == "Status")
        assert len(status_enum.fields) == 0  # Enums have no fields
        assert "ACTIVE" in status_enum.description
        assert "PENDING='pending'" in status_enum.description

        priority_enum = next(e for e in entities if e.name == "Priority")
        assert "LOW=1" in priority_enum.description

    def test_parse_intersection_types(self):
        """Test parsing intersection types."""
        ts_code = """
        interface BaseEntity {
          id: number;
          createdAt: Date;
        }

        interface WithName {
          name: string;
        }

        interface Combined extends BaseEntity {
          data: BaseEntity & WithName;  // Intersection type
          settings: { theme: string } & { lang: string };  // Complex intersection
        }
        """

        parser = TypeScriptParser()
        entities = parser.parse_content(ts_code)

        assert len(entities) == 3

        combined_entity = next(e for e in entities if e.name == "Combined")
        assert len(combined_entity.fields) == 2

        data_field = next(f for f in combined_entity.fields if f.name == "data")
        assert data_field.type.value == "rich"  # Intersection type falls back to rich
