"""Comprehensive tests for Lombok annotation handler"""

import pytest
from src.parsers.java.lombok_handler import LombokAnnotationHandler, LombokMetadata


class TestLombokMetadata:
    """Test LombokMetadata dataclass"""

    def test_metadata_defaults(self):
        """Test default metadata initialization"""
        metadata = LombokMetadata()

        assert metadata.has_data is False
        assert metadata.has_getter is False
        assert metadata.has_setter is False
        assert metadata.has_builder is False
        assert metadata.non_null_fields == set()
        assert metadata.builder_defaults == {}

    def test_metadata_with_values(self):
        """Test metadata with custom values"""
        metadata = LombokMetadata(
            has_data=True,
            has_getter=True,
            non_null_fields={"name", "email"},
            builder_defaults={"active": "true"},
        )

        assert metadata.has_data is True
        assert metadata.has_getter is True
        assert "name" in metadata.non_null_fields
        assert metadata.builder_defaults["active"] == "true"


class TestLombokAnnotationHandler:
    """Test Lombok annotation handler"""

    @pytest.fixture
    def handler(self):
        return LombokAnnotationHandler()

    def test_detect_data_annotation(self, handler):
        """Test @Data annotation detection"""
        java_code = """
        import lombok.Data;

        @Data
        public class User {
            private String name;
        }
        """

        metadata = handler.extract_lombok_metadata(java_code)

        assert metadata.has_data is True
        assert metadata.has_getter is True  # @Data implies @Getter
        assert metadata.has_setter is True  # @Data implies @Setter

    def test_detect_getter_annotation(self, handler):
        """Test @Getter annotation detection"""
        java_code = """
        import lombok.Getter;

        @Getter
        public class User {
            private String name;
        }
        """

        metadata = handler.extract_lombok_metadata(java_code)

        assert metadata.has_getter is True
        assert metadata.has_data is False
        assert metadata.has_setter is False

    def test_detect_setter_annotation(self, handler):
        """Test @Setter annotation detection"""
        java_code = """
        import lombok.Setter;

        @Setter
        public class User {
            private String name;
        }
        """

        metadata = handler.extract_lombok_metadata(java_code)

        assert metadata.has_setter is True
        assert metadata.has_getter is False

    def test_detect_builder_annotation(self, handler):
        """Test @Builder annotation detection"""
        java_code = """
        import lombok.Builder;

        @Builder
        public class User {
            private String name;
        }
        """

        metadata = handler.extract_lombok_metadata(java_code)

        assert metadata.has_builder is True

    def test_detect_noargsconstructor(self, handler):
        """Test @NoArgsConstructor annotation detection"""
        java_code = """
        import lombok.NoArgsConstructor;

        @NoArgsConstructor
        public class User {
            private String name;
        }
        """

        metadata = handler.extract_lombok_metadata(java_code)

        assert metadata.has_no_args_constructor is True

    def test_detect_allargsconstructor(self, handler):
        """Test @AllArgsConstructor annotation detection"""
        java_code = """
        import lombok.AllArgsConstructor;

        @AllArgsConstructor
        public class User {
            private String name;
        }
        """

        metadata = handler.extract_lombok_metadata(java_code)

        assert metadata.has_all_args_constructor is True

    def test_detect_requiredargsconstructor(self, handler):
        """Test @RequiredArgsConstructor annotation detection"""
        java_code = """
        import lombok.RequiredArgsConstructor;

        @RequiredArgsConstructor
        public class User {
            private String name;
        }
        """

        metadata = handler.extract_lombok_metadata(java_code)

        assert metadata.has_required_args_constructor is True

    def test_find_nonnull_fields(self, handler):
        """Test @NonNull field detection"""
        java_code = """
        import lombok.NonNull;

        public class User {
            @NonNull
            private String name;

            @NonNull
            private String email;

            private String phone;
        }
        """

        metadata = handler.extract_lombok_metadata(java_code)

        assert "name" in metadata.non_null_fields
        assert "email" in metadata.non_null_fields
        assert "phone" not in metadata.non_null_fields
        assert len(metadata.non_null_fields) == 2

    def test_find_builder_defaults(self, handler):
        """Test @Builder.Default detection"""
        java_code = """
        import lombok.Builder;

        @Builder
        public class User {
            @Builder.Default
            private Boolean active = true;

            @Builder.Default
            private Integer loginCount = 0;

            private String name;
        }
        """

        metadata = handler.extract_lombok_metadata(java_code)

        assert "active" in metadata.builder_defaults
        assert metadata.builder_defaults["active"] == "true"
        assert "loginCount" in metadata.builder_defaults
        assert metadata.builder_defaults["loginCount"] == "0"
        assert "name" not in metadata.builder_defaults

    def test_should_infer_accessors_with_data(self, handler):
        """Test accessor inference with @Data"""
        metadata = LombokMetadata(has_data=True)
        assert handler.should_infer_accessors(metadata) is True

    def test_should_infer_accessors_with_getter(self, handler):
        """Test accessor inference with @Getter"""
        metadata = LombokMetadata(has_getter=True)
        assert handler.should_infer_accessors(metadata) is True

    def test_should_infer_accessors_with_setter(self, handler):
        """Test accessor inference with @Setter"""
        metadata = LombokMetadata(has_setter=True)
        assert handler.should_infer_accessors(metadata) is True

    def test_should_not_infer_accessors_without_annotations(self, handler):
        """Test no accessor inference without Lombok"""
        metadata = LombokMetadata()
        assert handler.should_infer_accessors(metadata) is False

    def test_is_field_required_with_nonnull(self, handler):
        """Test required field detection with @NonNull"""
        metadata = LombokMetadata(non_null_fields={"email", "password"})

        assert handler.is_field_required("email", metadata) is True
        assert handler.is_field_required("password", metadata) is True
        assert handler.is_field_required("phone", metadata) is False

    def test_multiple_annotations_combined(self, handler):
        """Test multiple Lombok annotations together"""
        java_code = """
        import lombok.*;

        @Data
        @Builder
        @NoArgsConstructor
        @AllArgsConstructor
        public class User {
            @NonNull
            private String name;

            @Builder.Default
            private Boolean active = true;

            private String email;
        }
        """

        metadata = handler.extract_lombok_metadata(java_code)

        # Check all annotations detected
        assert metadata.has_data is True
        assert metadata.has_builder is True
        assert metadata.has_no_args_constructor is True
        assert metadata.has_all_args_constructor is True

        # Check field metadata
        assert "name" in metadata.non_null_fields
        assert "active" in metadata.builder_defaults

        # Check inferred behavior
        assert handler.should_infer_accessors(metadata) is True
        assert handler.is_field_required("name", metadata) is True

    def test_complex_builder_default_values(self, handler):
        """Test complex @Builder.Default expressions"""
        java_code = """
        import lombok.Builder;

        @Builder
        public class Config {
            @Builder.Default
            private List<String> tags = new ArrayList<>();

            @Builder.Default
            private Map<String, String> settings = new HashMap<>();

            @Builder.Default
            private String status = "ACTIVE";
        }
        """

        metadata = handler.extract_lombok_metadata(java_code)

        assert "tags" in metadata.builder_defaults
        assert "new ArrayList<>()" in metadata.builder_defaults["tags"]
        assert "settings" in metadata.builder_defaults
        assert "status" in metadata.builder_defaults

    def test_nonnull_with_different_access_modifiers(self, handler):
        """Test @NonNull with public/protected/private fields"""
        java_code = """
        import lombok.NonNull;

        public class User {
            @NonNull
            private String privateName;

            @NonNull
            protected String protectedName;

            @NonNull
            public String publicName;
        }
        """

        metadata = handler.extract_lombok_metadata(java_code)

        assert "privateName" in metadata.non_null_fields
        assert "protectedName" in metadata.non_null_fields
        assert "publicName" in metadata.non_null_fields
