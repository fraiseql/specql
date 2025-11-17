"""Tests for multi-tenant pattern detection"""

import pytest
from src.reverse_engineering.universal_pattern_detector import (
    UniversalPatternDetector,
    MultiTenantPattern,
)


class TestMultiTenantPatternSQL:
    """Test SQL multi-tenant pattern detection"""

    def setup_method(self):
        self.detector = MultiTenantPattern()

    def test_sql_tenant_id_column(self):
        """Detect tenant_id column in SQL table"""
        sql = """
        CREATE TABLE contacts (
            id SERIAL PRIMARY KEY,
            tenant_id UUID NOT NULL,
            email VARCHAR(255)
        );
        """

        assert self.detector.matches(sql, "sql") == True
        assert self.detector.confidence >= 0.70

    def test_sql_rls_policy(self):
        """Detect RLS policy with tenant isolation"""
        sql = """
        CREATE POLICY tenant_isolation ON contacts
            USING (tenant_id = current_setting('app.tenant_id')::UUID);
        """

        assert self.detector.matches(sql, "sql") == True
        assert self.detector.confidence >= 0.90

    def test_sql_full_multi_tenant(self):
        """Detect full multi-tenant setup (column + RLS + index)"""
        sql = """
        CREATE TABLE contacts (
            id SERIAL PRIMARY KEY,
            tenant_id UUID NOT NULL,
            email VARCHAR(255)
        );

        CREATE INDEX idx_contacts_tenant_id ON contacts(tenant_id);

        CREATE POLICY tenant_isolation ON contacts
            USING (tenant_id = current_setting('app.tenant_id')::UUID);
        """

        assert self.detector.matches(sql, "sql") == True
        assert self.detector.confidence >= 0.95
        assert "tenant_id column found" in self.detector.evidence
        assert "RLS policy with tenant_id filter" in self.detector.evidence


class TestMultiTenantPatternPython:
    """Test Python multi-tenant pattern detection"""

    def setup_method(self):
        self.detector = MultiTenantPattern()

    def test_python_tenant_field(self):
        """Detect tenant_id field in Python model"""
        code = """
        class Contact(Base):
            tenant_id: UUID
            email: str
        """

        assert self.detector.matches(code, "python") == True
        assert self.detector.confidence >= 0.70

    def test_python_tenant_mixin(self):
        """Detect TenantMixin pattern"""
        code = """
        class TenantMixin:
            tenant_id = Column(UUID, nullable=False)

        class Contact(TenantMixin, Base):
            email = Column(String)
        """

        assert self.detector.matches(code, "python") == True
        assert self.detector.confidence >= 0.80


class TestMultiTenantPatternJava:
    """Test Java multi-tenant pattern detection"""

    def setup_method(self):
        self.detector = MultiTenantPattern()

    def test_java_tenant_id_annotation(self):
        """Detect @TenantId annotation"""
        code = """
        @Entity
        public class Contact {
            @TenantId
            private UUID tenantId;
            private String email;
        }
        """

        assert self.detector.matches(code, "java") == True
        assert self.detector.confidence >= 0.85

    def test_java_hibernate_filter(self):
        """Detect Hibernate @Filter with tenant isolation"""
        code = """
        @Entity
        @FilterDef(name = "tenantFilter", parameters = @ParamDef(name = "tenantId", type = "uuid"))
        @Filter(name = "tenantFilter", condition = "tenant_id = :tenantId")
        public class Contact {
            @Column(name = "tenant_id", nullable = false)
            private UUID tenantId;
        }
        """

        assert self.detector.matches(code, "java") == True
        assert self.detector.confidence >= 0.85  # @Filter detection gives 0.85 confidence


class TestMultiTenantPatternRust:
    """Test Rust multi-tenant pattern detection"""

    def setup_method(self):
        self.detector = MultiTenantPattern()

    def test_rust_tenant_field(self):
        """Detect tenant_id field in Rust struct"""
        code = """
        pub struct Contact {
            pub id: i32,
            pub tenant_id: Uuid,
            pub email: String,
        }
        """

        assert self.detector.matches(code, "rust") == True
        assert self.detector.confidence >= 0.70


class TestMultiTenantPatternIntegration:
    """Integration tests with UniversalPatternDetector"""

    @pytest.fixture
    def detector(self):
        return UniversalPatternDetector()

    def test_integration_sql_full_setup(self, detector):
        """Test full SQL multi-tenant setup through UniversalPatternDetector"""
        sql_code = """
        CREATE TABLE contacts (
            id SERIAL PRIMARY KEY,
            tenant_id UUID NOT NULL,
            email VARCHAR(255)
        );

        CREATE INDEX idx_contacts_tenant_id ON contacts(tenant_id);

        ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;

        CREATE POLICY tenant_isolation ON contacts
            USING (tenant_id = current_setting('app.tenant_id')::UUID);
        """

        patterns = detector.detect(sql_code, language="sql")

        assert any(p.name == "multi_tenant" for p in patterns)
        mt = next(p for p in patterns if p.name == "multi_tenant")

        assert mt.confidence >= 0.95
        assert "tenant_id column found" in mt.evidence
        assert "RLS policy with tenant_id filter" in mt.evidence
        assert mt.suggested_stdlib == "stdlib/multi_tenant/enforce_tenant_isolation"

    def test_integration_python_tenant_mixin(self, detector):
        """Test Python TenantMixin through UniversalPatternDetector"""
        python_code = """
        from uuid import UUID
        from sqlalchemy import Column, String

        class TenantMixin:
            tenant_id = Column(UUID, nullable=False)

        class Contact(TenantMixin, Base):
            email = Column(String)

            @classmethod
            def for_tenant(cls, tenant_id: UUID):
                return cls.query.filter_by(tenant_id=tenant_id).all()
        """

        patterns = detector.detect(python_code, language="python")

        assert any(p.name == "multi_tenant" for p in patterns)
        mt = next(p for p in patterns if p.name == "multi_tenant")

        assert mt.confidence >= 0.80
        assert "TenantMixin base class" in mt.evidence
