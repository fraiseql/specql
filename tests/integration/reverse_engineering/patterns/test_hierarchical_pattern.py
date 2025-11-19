"""Tests for hierarchical data pattern detection"""

import pytest

from src.reverse_engineering.universal_pattern_detector import (
    HierarchicalPattern,
    UniversalPatternDetector,
)


class TestHierarchicalPatternSQL:
    """Test SQL hierarchical pattern detection"""

    def setup_method(self):
        self.detector = HierarchicalPattern()

    def test_sql_parent_id_self_reference(self):
        """Detect parent_id self-referencing foreign key"""
        sql = """
        CREATE TABLE categories (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255),
            parent_id INTEGER REFERENCES categories(id)
        );
        """

        assert self.detector.matches(sql, "sql")
        assert self.detector.confidence >= 0.30

    def test_sql_recursive_cte(self):
        """Detect recursive CTE for tree traversal"""
        sql = """
        WITH RECURSIVE category_tree AS (
            SELECT id, name, parent_id, 1 as depth
            FROM categories WHERE parent_id IS NULL
            UNION ALL
            SELECT c.id, c.name, c.parent_id, ct.depth + 1
            FROM categories c
            JOIN category_tree ct ON c.parent_id = ct.id
        )
        SELECT * FROM category_tree;
        """

        assert self.detector.matches(sql, "sql")
        assert self.detector.confidence >= 0.30

    def test_sql_path_field(self):
        """Detect path field for materialized paths"""
        sql = """
        CREATE TABLE categories (
            id INT PRIMARY KEY,
            name VARCHAR(255),
            path VARCHAR(1000)
        );
        """

        assert not self.detector.matches(sql, "sql")  # No parent_id or recursive CTE

    def test_sql_nested_set(self):
        """Detect nested set model with lft/rgt boundaries"""
        sql = """
        CREATE TABLE categories (
            id INT PRIMARY KEY,
            name VARCHAR(255),
            lft INT,
            rgt INT
        );
        """

        assert not self.detector.matches(sql, "sql")  # No parent_id or recursive CTE


class TestHierarchicalPatternPython:
    """Test Python hierarchical pattern detection"""

    def setup_method(self):
        self.detector = HierarchicalPattern()

    def test_python_parent_relationship(self):
        """Detect parent relationship in SQLAlchemy model"""
        code = """
        class Category(Base):
            id: int
            name: str
            parent_id: Optional[int]
            parent: Optional['Category'] = relationship('Category', remote_side=[id])
        """

        assert self.detector.matches(code, "python")
        assert self.detector.confidence >= 0.30

    def test_python_children_relationship(self):
        """Detect children relationship in SQLAlchemy model"""
        code = """
        class Category(Base):
            id: int
            name: str
            parent_id: Optional[int]
            children: List['Category'] = relationship('Category')
        """

        assert self.detector.matches(code, "python")
        assert self.detector.confidence >= 0.30


class TestHierarchicalPatternJava:
    """Test Java hierarchical pattern detection"""

    def setup_method(self):
        self.detector = HierarchicalPattern()

    def test_java_many_to_one_parent(self):
        """Detect @ManyToOne parent relationship"""
        code = """
        @Entity
        public class Category {
            @Id
            private Long id;

            private String name;

            @ManyToOne
            @JoinColumn(name = "parent_id")
            private Category parent;

            @OneToMany(mappedBy = "parent")
            private List<Category> children;
        }
        """

        assert self.detector.matches(code, "java")
        assert self.detector.confidence >= 0.60  # parent + children


class TestHierarchicalPatternRust:
    """Test Rust hierarchical pattern detection"""

    def setup_method(self):
        self.detector = HierarchicalPattern()

    def test_rust_parent_id_field(self):
        """Detect parent_id field in Rust struct"""
        code = """
        pub struct Category {
            pub id: i32,
            pub name: String,
            pub parent_id: Option<i32>,
        }
        """

        assert self.detector.matches(code, "rust")
        assert self.detector.confidence >= 0.30


class TestHierarchicalPatternIntegration:
    """Integration tests with UniversalPatternDetector"""

    @pytest.fixture
    def detector(self):
        return UniversalPatternDetector()

    def test_integration_sql_full_hierarchy(self, detector):
        """Test full SQL hierarchical setup through UniversalPatternDetector"""
        sql_code = """
        CREATE TABLE categories (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255),
            parent_id INTEGER REFERENCES categories(id)
        );

        WITH RECURSIVE category_tree AS (
            SELECT id, name, parent_id, 1 as depth
            FROM categories WHERE parent_id IS NULL
            UNION ALL
            SELECT c.id, c.name, c.parent_id, ct.depth + 1
            FROM categories c
            JOIN category_tree ct ON c.parent_id = ct.id
        )
        SELECT * FROM category_tree;
        """

        patterns = detector.detect(sql_code, language="sql")

        assert any(p.name == "hierarchical" for p in patterns)
        hier = next(p for p in patterns if p.name == "hierarchical")

        assert hier.confidence >= 0.60
        assert "Has parent_id self-referencing foreign key" in hier.evidence
        assert "Uses recursive CTE for tree traversal" in hier.evidence
        assert hier.suggested_stdlib == "hierarchy/recursive_tree"

    def test_integration_python_relationships(self, detector):
        """Test Python relationships through UniversalPatternDetector"""
        python_code = """
        from typing import Optional, List
        from sqlalchemy import Column, Integer, String, ForeignKey
        from sqlalchemy.orm import relationship

        class Category(Base):
            __tablename__ = 'categories'

            id = Column(Integer, primary_key=True)
            name = Column(String)
            parent_id = Column(Integer, ForeignKey('categories.id'))

            parent = relationship('Category', remote_side=[id])
            children = relationship('Category', backref='parent')
        """

        patterns = detector.detect(python_code, language="python")

        assert any(p.name == "hierarchical" for p in patterns)
        hier = next(p for p in patterns if p.name == "hierarchical")

        assert hier.confidence >= 0.50
        assert "Has parent_id field for self-reference" in hier.evidence
