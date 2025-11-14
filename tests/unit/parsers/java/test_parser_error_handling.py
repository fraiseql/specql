"""Tests for spring_boot_parser.py error handling"""

import pytest
from src.parsers.java.spring_boot_parser import SpringBootParser


class TestParserErrorHandling:
    """Test error handling in Spring Boot parser"""

    @pytest.fixture
    def parser(self):
        return SpringBootParser()

    def test_parse_file_not_found(self, parser):
        """Test parsing non-existent file"""
        with pytest.raises(FileNotFoundError):
            parser.parse_entity_file("/nonexistent/path/Entity.java")

    def test_parse_empty_file(self, parser):
        """Test parsing empty Java file"""
        import tempfile
        import os

        # Create empty file
        fd, path = tempfile.mkstemp(suffix=".java")
        os.close(fd)

        try:
            # Should raise exception for empty file
            with pytest.raises(Exception):
                parser.parse_entity_file(path)
        finally:
            os.unlink(path)

    def test_parse_non_entity_class(self, parser):
        """Test parsing class without @Entity"""
        import tempfile
        import os

        java_code = """
        package com.example;

        public class NotAnEntity {
            private String field;
        }
        """

        # Create temp file
        fd, path = tempfile.mkstemp(suffix=".java")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(java_code)

            # Parser parses any public class, not just entities
            result = parser.parse_entity_file(path)
            assert result.name == "NotAnEntity"
            assert result.schema == "example"
        finally:
            os.unlink(path)

    def test_parse_class_with_syntax_error(self, parser):
        """Test parsing Java with syntax errors"""
        import tempfile
        import os

        java_code = """
        package com.example;

        @Entity
        public class Broken {
            private String name
            // Missing semicolon
        }
        """

        # Create temp file
        fd, path = tempfile.mkstemp(suffix=".java")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(java_code)

            # Should handle gracefully or raise clear error
            try:
                result = parser.parse_entity_file(path)
                # If it succeeds, should have correct name
                assert result.name == "Broken"
            except Exception as e:
                # Should be a clear parse error, not generic exception
                assert "parse" in str(e).lower() or "syntax" in str(e).lower()
        finally:
            os.unlink(path)

    def test_parse_entity_with_missing_package(self, parser):
        """Test entity without package declaration"""
        import tempfile
        import os

        java_code = """
        import javax.persistence.*;

        @Entity
        public class NoPackage {
            @Id
            private Long id;
        }
        """

        # Create temp file
        fd, path = tempfile.mkstemp(suffix=".java")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(java_code)

            result = parser.parse_entity_file(path)
            # Should handle gracefully
            assert result.schema == "default" or result.schema == ""
        finally:
            os.unlink(path)

    def test_parse_project_empty_directory(self, parser):
        """Test parsing empty directory"""
        import tempfile
        import os

        temp_dir = tempfile.mkdtemp()
        try:
            entities = parser.parse_project(temp_dir)
            # Should return empty list
            assert entities == [] or len(entities) == 0
        finally:
            os.rmdir(temp_dir)

    def test_parse_project_with_no_entities(self, parser):
        """Test parsing directory with no entity files"""
        import tempfile
        import os

        temp_dir = tempfile.mkdtemp()
        non_entity = None
        try:
            # Create non-entity Java file
            non_entity = os.path.join(temp_dir, "Utils.java")
            with open(non_entity, "w") as f:
                f.write("""
                package com.example;
                public class Utils {
                    public static void helper() {}
                }
                """)

            entities = parser.parse_project(temp_dir)
            # Should return empty list (no entities found)
            assert len(entities) == 0
        finally:
            if non_entity and os.path.exists(non_entity):
                os.unlink(non_entity)
            os.rmdir(temp_dir)
