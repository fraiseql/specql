"""Tests for versioning pattern detection"""

import pytest
from src.reverse_engineering.universal_pattern_detector import (
    UniversalPatternDetector,
    VersioningPattern,
)


class TestVersioningPatternSQL:
    """Test SQL versioning pattern detection"""

    def setup_method(self):
        self.detector = VersioningPattern()

    def test_sql_version_column(self):
        """Detect version column for optimistic locking"""
        sql = """
        CREATE TABLE documents (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255),
            version INT NOT NULL DEFAULT 1
        );
        """

        assert self.detector.matches(sql, "sql") == True
        assert self.detector.confidence >= 0.40

    def test_sql_history_table(self):
        """Detect history table pattern"""
        sql = """
        CREATE TABLE documents (
            id INT PRIMARY KEY,
            title VARCHAR(255)
        );

        CREATE TABLE documents_history (
            id INT PRIMARY KEY,
            document_id INT,
            version INT,
            title VARCHAR(255),
            changed_at TIMESTAMP
        );
        """

        assert self.detector.matches(sql, "sql") == True
        assert self.detector.confidence >= 0.30

    def test_sql_temporal_columns(self):
        """Detect temporal table with system_time columns"""
        sql = """
        CREATE TABLE documents (
            id INT PRIMARY KEY,
            title VARCHAR(255),
            system_time_start TIMESTAMP,
            system_time_end TIMESTAMP
        ) WITH SYSTEM VERSIONING;
        """

        assert self.detector.matches(sql, "sql") == True
        assert self.detector.confidence >= 0.30


class TestVersioningPatternPython:
    """Test Python versioning pattern detection"""

    def setup_method(self):
        self.detector = VersioningPattern()

    def test_python_version_field(self):
        """Detect version field in Python model"""
        code = """
        class Document(Base):
            id: int
            title: str
            version: int = Column(Integer, default=1, nullable=False)
        """

        assert self.detector.matches(code, "python") == True
        assert self.detector.confidence >= 0.40

    def test_python_history_mixin(self):
        """Detect history mixin pattern"""
        code = """
        class HistoryMixin:
            version: int = Column(Integer, default=1)

        class Document(HistoryMixin, Base):
            id: int
            title: str
        """

        assert self.detector.matches(code, "python") == True  # Has version field in mixin


class TestVersioningPatternJava:
    """Test Java versioning pattern detection"""

    def setup_method(self):
        self.detector = VersioningPattern()

    def test_java_version_annotation(self):
        """Detect @Version annotation for optimistic locking"""
        code = """
        @Entity
        public class Document {
            @Id
            private Long id;

            private String title;

            @Version
            private int version;
        }
        """

        assert self.detector.matches(code, "java") == True
        assert self.detector.confidence >= 0.50


class TestVersioningPatternIntegration:
    """Integration tests with UniversalPatternDetector"""

    @pytest.fixture
    def detector(self):
        return UniversalPatternDetector()

    def test_integration_sql_full_versioning(self, detector):
        """Test full SQL versioning setup through UniversalPatternDetector"""
        sql_code = """
        CREATE TABLE documents (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255),
            version INT NOT NULL DEFAULT 1
        );

        CREATE TABLE documents_history (
            id SERIAL PRIMARY KEY,
            document_id INT REFERENCES documents(id),
            version INT NOT NULL,
            title VARCHAR(255),
            changed_at TIMESTAMP DEFAULT NOW()
        );

        UPDATE documents
        SET title = 'New Title', version = version + 1
        WHERE id = 1 AND version = 2;
        """

        patterns = detector.detect(sql_code, language="sql")

        assert any(p.name == "versioning" for p in patterns)
        ver = next(p for p in patterns if p.name == "versioning")

        assert ver.confidence >= 0.70
        assert "Has version column for optimistic locking" in ver.evidence
        assert "Has history table for version tracking" in ver.evidence
        assert ver.suggested_stdlib == "versioning/optimistic_lock"

    def test_integration_java_version_annotation(self, detector):
        """Test Java @Version annotation through UniversalPatternDetector"""
        java_code = """
        import javax.persistence.Entity;
        import javax.persistence.Version;

        @Entity
        public class Document {
            @Id
            private Long id;

            private String title;

            @Version
            private int version;

            public void updateTitle(String newTitle) {
                this.title = newTitle;
                // Version automatically incremented by JPA
            }
        }
        """

        patterns = detector.detect(java_code, language="java")

        assert any(p.name == "versioning" for p in patterns)
        ver = next(p for p in patterns if p.name == "versioning")

        assert ver.confidence >= 0.50
        assert "Uses @Version annotation for optimistic locking" in ver.evidence
