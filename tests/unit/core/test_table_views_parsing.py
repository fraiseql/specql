"""Tests for table_views configuration parsing."""

import pytest

from src.core.ast_models import TableViewMode
from src.core.exceptions import SpecQLValidationError
from src.core.specql_parser import SpecQLParser


class TestTableViewsParsing:
    """Test parsing table_views configuration."""

    def setup_method(self):
        self.parser = SpecQLParser()

    def test_parse_minimal_table_views(self):
        """Test parsing minimal table_views config."""
        yaml_content = """
entity: Review
schema: library
fields:
  rating: integer
  author: ref(User)

table_views:
  mode: auto
"""

        entity = self.parser.parse(yaml_content)
        assert entity.table_views is not None
        assert entity.table_views.mode == TableViewMode.AUTO

    def test_parse_include_relations(self):
        """Test parsing include_relations."""
        yaml_content = """
entity: Review
schema: library
fields:
  author: ref(User)
  book: ref(Book)

table_views:
  include_relations:
    - author:
        fields: [name, email]
    - book:
        fields: [title, isbn]
"""

        entity = self.parser.parse(yaml_content)
        assert len(entity.table_views.include_relations) == 2

        author_rel = entity.table_views.include_relations[0]
        assert author_rel.entity_name == "author"
        assert author_rel.fields == ["name", "email"]

        book_rel = entity.table_views.include_relations[1]
        assert book_rel.entity_name == "book"
        assert book_rel.fields == ["title", "isbn"]

    def test_parse_nested_include_relations(self):
        """Test parsing nested include_relations."""
        yaml_content = """
entity: Review
fields:
  book: ref(Book)

table_views:
  include_relations:
    - book:
        fields: [title, isbn]
        include_relations:
          - publisher:
              fields: [name, country]
"""

        entity = self.parser.parse(yaml_content)
        book_rel = entity.table_views.include_relations[0]
        assert len(book_rel.include_relations) == 1

        publisher_rel = book_rel.include_relations[0]
        assert publisher_rel.entity_name == "publisher"
        assert publisher_rel.fields == ["name", "country"]

    def test_parse_extra_filter_columns_simple(self):
        """Test parsing simple extra_filter_columns."""
        yaml_content = """
entity: Review
fields:
  rating: integer
  review_date: timestamp

table_views:
  extra_filter_columns:
    - rating
    - review_date
"""

        entity = self.parser.parse(yaml_content)
        assert len(entity.table_views.extra_filter_columns) == 2
        assert entity.table_views.extra_filter_columns[0].name == "rating"
        assert entity.table_views.extra_filter_columns[1].name == "review_date"

    def test_parse_extra_filter_columns_advanced(self):
        """Test parsing advanced extra_filter_columns."""
        yaml_content = """
entity: Review
fields:
  author: ref(User)

table_views:
  extra_filter_columns:
    - rating
    - author_name:
        source: author.name
        type: text
        index: gin_trgm
"""

        entity = self.parser.parse(yaml_content)
        assert len(entity.table_views.extra_filter_columns) == 2

        # Simple column
        assert entity.table_views.extra_filter_columns[0].name == "rating"

        # Advanced column
        col = entity.table_views.extra_filter_columns[1]
        assert col.name == "author_name"
        assert col.source == "author.name"
        assert col.type == "text"
        assert col.index_type == "gin_trgm"

    def test_parse_force_mode(self):
        """Test parsing force mode."""
        yaml_content = """
entity: AuditLog
fields:
  message: text

table_views:
  mode: force
"""

        entity = self.parser.parse(yaml_content)
        assert entity.table_views.mode == TableViewMode.FORCE
        assert entity.should_generate_table_view is True

    def test_parse_disable_mode(self):
        """Test parsing disable mode."""
        yaml_content = """
entity: SessionToken
fields:
  user: ref(User)

table_views:
  mode: disable
"""

        entity = self.parser.parse(yaml_content)
        assert entity.table_views.mode == TableViewMode.DISABLE
        assert entity.should_generate_table_view is False

    def test_invalid_mode(self):
        """Test invalid mode raises error."""
        yaml_content = """
entity: Review
table_views:
  mode: invalid_mode
"""

        with pytest.raises(SpecQLValidationError) as exc_info:
            self.parser.parse(yaml_content)

        assert "Invalid table_views.mode" in str(exc_info.value)

    def test_include_relations_requires_fields(self):
        """Test include_relations requires fields."""
        yaml_content = """
entity: Review
fields:
  author: ref(User)

table_views:
  include_relations:
    - author: {}
"""

        with pytest.raises(SpecQLValidationError) as exc_info:
            self.parser.parse(yaml_content)

        assert "must specify 'fields'" in str(exc_info.value)

    def test_entity_without_table_views_block(self):
        """Test entity without table_views block (defaults)."""
        yaml_content = """
entity: Review
fields:
  author: ref(User)
"""

        entity = self.parser.parse(yaml_content)
        assert entity.table_views is None
        assert entity.should_generate_table_view is True  # Auto mode default

    def test_complete_table_views_example(self):
        """Test complete table_views configuration."""
        yaml_content = """
entity: Review
schema: library

fields:
  rating: integer
  comment: text
  author: ref(User)
  book: ref(Book)
  review_date: timestamp

table_views:
  mode: auto
  include_relations:
    - author:
        fields: [name, email, avatarUrl]
    - book:
        fields: [title, isbn, publishedYear]
        include_relations:
          - publisher:
              fields: [name, country]

  extra_filter_columns:
    - rating
    - review_date
"""

        entity = self.parser.parse(yaml_content)

        # Verify entity structure
        assert entity.name == "Review"
        assert entity.schema == "library"
        assert entity.should_generate_table_view is True

        # Verify table_views config
        tv = entity.table_views
        assert tv.mode == TableViewMode.AUTO
        assert len(tv.include_relations) == 2
        assert len(tv.extra_filter_columns) == 2

        # Verify author relation
        author = tv.include_relations[0]
        assert author.entity_name == "author"
        assert set(author.fields) == {"name", "email", "avatarUrl"}

        # Verify book relation (with nested publisher)
        book = tv.include_relations[1]
        assert book.entity_name == "book"
        assert set(book.fields) == {"title", "isbn", "publishedYear"}
        assert len(book.include_relations) == 1

        publisher = book.include_relations[0]
        assert publisher.entity_name == "publisher"
        assert set(publisher.fields) == {"name", "country"}

        # Verify filter columns
        assert tv.extra_filter_columns[0].name == "rating"
        assert tv.extra_filter_columns[1].name == "review_date"
