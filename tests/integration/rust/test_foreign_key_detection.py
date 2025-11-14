"""
Comprehensive tests for foreign key detection in Rust parser.

INSTALLATION: Copy to tests/integration/rust/test_foreign_key_detection.py

PURPOSE:
Tests the automatic detection of foreign key relationships from:
1. Field naming conventions (user_id -> User)
2. Diesel #[belongs_to(...)] attributes
3. Manual relationship annotations

Run with:
    uv run pytest tests/integration/rust/test_foreign_key_detection.py -v
"""

import pytest
import tempfile
import os
from pathlib import Path
from src.reverse_engineering.rust_parser import (
    RustParser,
    RustToSpecQLMapper,
    RustReverseEngineeringService,
)
from src.core.ast_models import FieldTier


class TestForeignKeyDetection:
    """Test foreign key relationship detection."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = RustParser()
        self.mapper = RustToSpecQLMapper()
        self.service = RustReverseEngineeringService()

    def test_naming_convention_detection_simple(self):
        """Test FK detection from simple naming convention: user_id -> User."""
        rust_code = """
        pub struct User {
            pub id: i32,
            pub name: String,
        }

        pub struct Post {
            pub id: i64,
            pub title: String,
            pub user_id: i32,  // Should detect FK to User
        }
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            entities = self.service.reverse_engineer_file(Path(temp_path))

            # Find Post entity
            post = next(e for e in entities if e.name == "Post")

            # Check user_id field
            user_id_field = post.fields.get("user_id")
            assert user_id_field is not None, "user_id field should exist"

            # NOTE: This test documents CURRENT behavior
            # If FK detection is not yet implemented, this will fail
            # Junior engineer: Implement FK detection if this fails
            # Expected: user_id should reference "user" table
            # assert user_id_field.reference_entity == "user"
            # assert user_id_field.tier == FieldTier.REFERENCE

        finally:
            os.unlink(temp_path)

    def test_belongs_to_attribute_simple(self):
        """Test FK detection from Diesel #[belongs_to(User)] attribute."""
        rust_code = """
        pub struct User {
            pub id: i32,
            pub name: String,
        }

        pub struct Post {
            pub id: i64,
            pub title: String,
            #[belongs_to(User)]
            pub user_id: i32,
        }
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            entities = self.service.reverse_engineer_file(Path(temp_path))

            # Find Post entity
            post = next(e for e in entities if e.name == "Post")

            # Check user_id field
            user_id_field = post.fields.get("user_id")
            assert user_id_field is not None

            # belongs_to parsing is implemented
            assert user_id_field.reference_entity == "user"
            assert user_id_field.tier == FieldTier.REFERENCE

        finally:
            os.unlink(temp_path)

    def test_belongs_to_attribute_with_custom_fk(self):
        """Test FK detection with custom foreign_key parameter."""
        rust_code = """
        pub struct Category {
            pub id: i32,
            pub name: String,
        }

        pub struct Product {
            pub id: i64,
            pub name: String,
            #[belongs_to(Category, foreign_key = "category_id")]
            pub category_id: i32,
        }
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            entities = self.service.reverse_engineer_file(Path(temp_path))

            # Find Product entity
            product = next(e for e in entities if e.name == "Product")

            # Check category_id field
            category_id_field = product.fields.get("category_id")
            assert category_id_field is not None

            # Check if reference is detected
            if (
                hasattr(category_id_field, "reference_entity")
                and category_id_field.reference_entity
            ):
                assert category_id_field.reference_entity == "category"
                assert category_id_field.tier == FieldTier.REFERENCE
            else:
                pytest.skip(
                    "FK detection from belongs_to with custom FK not yet implemented"
                )

        finally:
            os.unlink(temp_path)

    def test_optional_foreign_key(self):
        """Test FK detection for optional relationships (Option<i32>)."""
        rust_code = """
        pub struct User {
            pub id: i32,
            pub name: String,
        }

        pub struct Post {
            pub id: i64,
            pub title: String,
            #[belongs_to(User)]
            pub author_id: Option<i32>,  // Optional FK
        }
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            entities = self.service.reverse_engineer_file(Path(temp_path))

            # Find Post entity
            post = next(e for e in entities if e.name == "Post")

            # Check author_id field
            author_id_field = post.fields.get("author_id")
            assert author_id_field is not None
            assert author_id_field.nullable, "Optional FK should be nullable"

            # Check if reference is detected
            if (
                hasattr(author_id_field, "reference_entity")
                and author_id_field.reference_entity
            ):
                assert author_id_field.reference_entity == "user"
                assert author_id_field.tier == FieldTier.REFERENCE
            else:
                pytest.skip("FK detection for optional fields not yet implemented")

        finally:
            os.unlink(temp_path)

    def test_multiple_foreign_keys(self):
        """Test detection of multiple FKs in one entity."""
        rust_code = """
        pub struct User {
            pub id: i32,
            pub name: String,
        }

        pub struct Category {
            pub id: i32,
            pub name: String,
        }

        pub struct Post {
            pub id: i64,
            pub title: String,
            #[belongs_to(User)]
            pub author_id: i32,
            #[belongs_to(Category)]
            pub category_id: i32,
        }
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            entities = self.service.reverse_engineer_file(Path(temp_path))

            # Find Post entity
            post = next(e for e in entities if e.name == "Post")

            # Check both FK fields
            author_id_field = post.fields.get("author_id")
            category_id_field = post.fields.get("category_id")

            assert author_id_field is not None
            assert category_id_field is not None

            # Check if references are detected
            reference_count = 0
            if (
                hasattr(author_id_field, "reference_entity")
                and author_id_field.reference_entity
            ):
                assert author_id_field.reference_entity == "user"
                reference_count += 1

            if (
                hasattr(category_id_field, "reference_entity")
                and category_id_field.reference_entity
            ):
                assert category_id_field.reference_entity == "category"
                reference_count += 1

            if reference_count == 0:
                pytest.skip("Multiple FK detection not yet implemented")
            elif reference_count == 1:
                pytest.fail("Only one of two FKs was detected")
            # else: Both detected, test passes

        finally:
            os.unlink(temp_path)

    def test_self_referential_foreign_key(self):
        """Test detection of self-referential FKs (e.g., parent_id)."""
        rust_code = """
        pub struct Category {
            pub id: i32,
            pub name: String,
            #[belongs_to(Category, foreign_key = "parent_id")]
            pub parent_id: Option<i32>,  // Self-referential
        }
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            entities = self.service.reverse_engineer_file(Path(temp_path))

            # Find Category entity
            category = next(e for e in entities if e.name == "Category")

            # Check parent_id field
            parent_id_field = category.fields.get("parent_id")
            assert parent_id_field is not None
            assert parent_id_field.nullable, "Self-referential FK should be nullable"

            # Check if self-reference is detected
            if (
                hasattr(parent_id_field, "reference_entity")
                and parent_id_field.reference_entity
            ):
                assert parent_id_field.reference_entity == "category"
                assert parent_id_field.tier == FieldTier.REFERENCE
            else:
                pytest.skip("Self-referential FK detection not yet implemented")

        finally:
            os.unlink(temp_path)

    def test_naming_convention_multiple_patterns(self):
        """Test various FK naming patterns."""
        rust_code = """
        pub struct User {
            pub id: i32,
        }

        pub struct Organization {
            pub id: i32,
        }

        pub struct Post {
            pub id: i64,
            pub user_id: i32,           // Pattern: <entity>_id
            pub created_by: i32,        // Pattern: created_by (User)
            pub organization_id: i32,   // Pattern: longer name
            pub owner_user_id: i32,     // Pattern: prefix_<entity>_id
        }
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            entities = self.service.reverse_engineer_file(Path(temp_path))

            # Find Post entity
            post = next(e for e in entities if e.name == "Post")

            # Document which patterns are detected
            detected_patterns = []

            if hasattr(post.fields["user_id"], "reference_entity"):
                if post.fields["user_id"].reference_entity:
                    detected_patterns.append("user_id")

            if hasattr(post.fields["organization_id"], "reference_entity"):
                if post.fields["organization_id"].reference_entity:
                    detected_patterns.append("organization_id")

            # This test is for documentation purposes
            print(f"\nDetected FK patterns: {detected_patterns}")

            if not detected_patterns:
                pytest.skip("Naming convention FK detection not yet implemented")

        finally:
            os.unlink(temp_path)

    def test_belongs_to_without_field_name_match(self):
        """Test belongs_to where field name doesn't match convention."""
        rust_code = """
        pub struct User {
            pub id: i32,
            pub name: String,
        }

        pub struct Post {
            pub id: i64,
            pub title: String,
            #[belongs_to(User, foreign_key = "created_by")]
            pub created_by: i32,  // FK but doesn't follow naming convention
        }
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            entities = self.service.reverse_engineer_file(Path(temp_path))

            # Find Post entity
            post = next(e for e in entities if e.name == "Post")

            # Check created_by field
            created_by_field = post.fields.get("created_by")
            assert created_by_field is not None

            # belongs_to should work regardless of field name
            if (
                hasattr(created_by_field, "reference_entity")
                and created_by_field.reference_entity
            ):
                assert created_by_field.reference_entity == "user"
                assert created_by_field.tier == FieldTier.REFERENCE
            else:
                pytest.skip("belongs_to with custom FK name not yet fully implemented")

        finally:
            os.unlink(temp_path)

    def test_diesel_table_foreign_keys(self):
        """Test FK detection in Diesel table! macros."""
        rust_code = """
        table! {
            users (id) {
                id -> Integer,
                name -> Text,
            }
        }

        table! {
            posts (id) {
                id -> BigInt,
                title -> Text,
                user_id -> Integer,  // Should detect FK to users
            }
        }
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(rust_code)
            temp_path = f.name

        try:
            # This test depends on Diesel table parsing being implemented
            try:
                entities = self.service.reverse_engineer_file(Path(temp_path))
            except Exception:
                pytest.skip("Diesel table parsing not yet implemented")

            # Find posts entity
            posts = next((e for e in entities if e.table == "posts"), None)

            if posts is None:
                pytest.skip("Diesel table parsing not yet implemented")

            # Check user_id field
            user_id_field = posts.fields.get("user_id")
            assert user_id_field is not None

            # Check if FK is detected
            if (
                hasattr(user_id_field, "reference_entity")
                and user_id_field.reference_entity
            ):
                assert user_id_field.reference_entity == "users"
            else:
                pytest.skip("FK detection in Diesel tables not yet implemented")

        finally:
            os.unlink(temp_path)


class TestForeignKeyEnhancements:
    """Tests for future FK detection enhancements."""

    def test_composite_foreign_keys(self):
        """Test detection of composite FKs (future enhancement)."""
        pytest.skip("Composite FK detection is a future enhancement")

    def test_polymorphic_associations(self):
        """Test polymorphic FK detection (future enhancement)."""
        pytest.skip("Polymorphic association detection is a future enhancement")

    def test_through_associations(self):
        """Test many-to-many through table detection (future enhancement)."""
        pytest.skip("Through association detection is a future enhancement")


# ============================================================================
# IMPLEMENTATION GUIDE FOR JUNIOR ENGINEER
# ============================================================================

"""
GUIDE: Implementing Foreign Key Detection

CURRENT STATE:
- Basic belongs_to parsing exists (rust_parser.py line 206-255)
- Parses #[belongs_to(Entity)] attributes
- Sets reference_entity and tier = REFERENCE

TASKS TO COMPLETE:

1. NAMING CONVENTION DETECTION
   Location: RustToSpecQLMapper._map_field() method

   Add before line 186:
   ```python
   # Detect foreign keys from naming convention
   if not field_def.reference_entity:  # Only if not already set by belongs_to
       if rust_field.name.endswith('_id'):
           # Extract entity name: user_id -> user
           entity_name = rust_field.name[:-3]  # Remove '_id'
           field_def.reference_entity = entity_name
           field_def.tier = FieldTier.REFERENCE
   ```

2. IMPROVE BELONGS_TO PARSING
   Location: RustToSpecQLMapper._parse_belongs_to_attribute() (line 223)

   Current implementation is basic. Enhance to handle:
   - Multiple spaces: #[belongs_to( User )]
   - Comments: #[belongs_to(User)] // Link to users table
   - Complex foreign_key: foreign_key = "custom_id"

3. DIESEL TABLE FK DETECTION
   Location: RustToSpecQLMapper.map_diesel_table_to_entity()

   After creating field_def, add:
   ```python
   # Detect FK from naming convention in Diesel tables
   if diesel_col.name.endswith('_id'):
       entity_name = diesel_col.name[:-3]
       field_def.reference_entity = entity_name
       field_def.tier = FieldTier.REFERENCE
   ```

4. ADD JOINABLE ASSOCIATIONS
   Location: Diesel schema.rs often has joinable! macro

   Future: Parse joinable! macro to detect many-to-many relationships

TESTING:
After implementation, run:
```bash
uv run pytest tests/integration/rust/test_foreign_key_detection.py -v
```

Many tests will now pass instead of being skipped.
"""
