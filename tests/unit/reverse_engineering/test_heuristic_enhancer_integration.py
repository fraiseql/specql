"""
Test HeuristicEnhancer integration with UniversalPatternDetector
"""

from core.ast_models import ActionStep
from reverse_engineering.ast_to_specql_mapper import ConversionResult
from reverse_engineering.heuristic_enhancer import HeuristicEnhancer


class TestHeuristicEnhancerIntegration:
    """Test integration of HeuristicEnhancer with UniversalPatternDetector"""

    def setup_method(self):
        self.enhancer = HeuristicEnhancer()

    def test_sql_state_machine_detection(self):
        """Test SQL state machine pattern detection via universal detector"""
        sql_code = """
        CREATE TABLE contacts (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255),
            status TEXT
        );

        CREATE OR REPLACE FUNCTION qualify_lead(p_contact_id INTEGER)
        RETURNS TABLE(success BOOLEAN, message TEXT) AS $$
        BEGIN
            UPDATE contacts SET status = 'qualified' WHERE id = p_contact_id AND status = 'lead';
            RETURN QUERY SELECT TRUE, 'Contact qualified';
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION close_contact(p_contact_id INTEGER)
        RETURNS TABLE(success BOOLEAN, message TEXT) AS $$
        BEGIN
            UPDATE contacts SET status = 'closed' WHERE id = p_contact_id AND status = 'qualified';
            RETURN QUERY SELECT TRUE, 'Contact closed';
        END;
        $$ LANGUAGE plpgsql;
        """

        # Create a minimal ConversionResult
        result = ConversionResult(
            function_name="update_contact_status",
            schema="public",
            parameters=[],
            return_type="TABLE(success BOOLEAN, message TEXT)",
            steps=[],
            confidence=0.85,
        )

        # Enhance with source code
        enhanced = self.enhancer.enhance(result, source_code=sql_code, language="sql")

        # Check that universal patterns were detected
        assert hasattr(enhanced, "metadata")
        assert "universal_patterns" in enhanced.metadata
        universal_patterns = enhanced.metadata["universal_patterns"]

        # Should detect state machine pattern
        pattern_names = [p["name"] for p in universal_patterns]
        assert "state_machine" in pattern_names

        # Find the state machine pattern
        state_machine = next(p for p in universal_patterns if p["name"] == "state_machine")
        assert state_machine["confidence"] >= 0.60
        assert any("status" in e.lower() for e in state_machine["evidence"])

    def test_python_soft_delete_detection(self):
        """Test Python soft delete pattern detection"""
        python_code = """
        class Contact(Base):
            id: int
            email: str
            deleted_at: Optional[datetime] = None

            def soft_delete(self):
                self.deleted_at = datetime.now()
        """

        result = ConversionResult(
            function_name="soft_delete_contact",
            schema="public",
            parameters=[],
            return_type="VOID",
            steps=[],
            confidence=0.85,
        )

        enhanced = self.enhancer.enhance(result, source_code=python_code, language="python")

        # Check for soft delete pattern
        assert "universal_patterns" in enhanced.metadata
        pattern_names = [p["name"] for p in enhanced.metadata["universal_patterns"]]
        assert "soft_delete" in pattern_names

    def test_rust_audit_trail_detection(self):
        """Test Rust audit trail pattern detection"""
        rust_code = """
        #[derive(Debug, Serialize)]
        pub struct Contact {
            pub id: i32,
            pub email: String,
            pub created_at: DateTime<Utc>,
            pub updated_at: DateTime<Utc>,
            pub created_by: i32,
            pub updated_by: i32,
        }

        impl Contact {
            pub fn update(&mut self, user_id: i32) {
                self.updated_at = Utc::now();
                self.updated_by = user_id;
            }
        }
        """

        result = ConversionResult(
            function_name="update_contact",
            schema="public",
            parameters=[],
            return_type="VOID",
            steps=[],
            confidence=0.85,
        )

        enhanced = self.enhancer.enhance(result, source_code=rust_code, language="rust")

        # Check for audit trail pattern
        assert "universal_patterns" in enhanced.metadata
        pattern_names = [p["name"] for p in enhanced.metadata["universal_patterns"]]
        assert "audit_trail" in pattern_names

        # Verify confidence boost
        assert enhanced.confidence > 0.85  # Should be boosted

    def test_java_multi_tenant_detection(self):
        """Test Java multi-tenant pattern detection"""
        java_code = """
        @Entity
        @Table(name = "contacts")
        @Filter(name = "tenantFilter", condition = "tenant_id = :tenantId")
        public class Contact {
            @Id
            private Long id;

            private String email;

            @Column(name = "tenant_id", nullable = false)
            private UUID tenant_id;

            public void setTenantId(UUID tenant_id) {
                this.tenant_id = tenant_id;
            }
        }
        """

        result = ConversionResult(
            function_name="create_contact",
            schema="public",
            parameters=[],
            return_type="VOID",
            steps=[],
            confidence=0.85,
        )

        enhanced = self.enhancer.enhance(result, source_code=java_code, language="java")

        # Check for multi-tenant pattern
        assert "universal_patterns" in enhanced.metadata
        pattern_names = [p["name"] for p in enhanced.metadata["universal_patterns"]]
        assert "multi_tenant" in pattern_names

    def test_backward_compatibility_without_source_code(self):
        """Test that enhance() still works without source_code (backward compatibility)"""
        result = ConversionResult(
            function_name="test_action",
            schema="public",
            parameters=[],
            return_type="VOID",
            steps=[
                ActionStep(
                    type="query",
                    expression="UPDATE contacts SET status = 'qualified' WHERE id = 1",
                )
            ],
            confidence=0.85,
        )

        # Call enhance without source_code
        enhanced = self.enhancer.enhance(result)

        # Should still work and return result
        assert enhanced.confidence >= 0.85
        assert hasattr(enhanced, "metadata")
        assert "detected_patterns" in enhanced.metadata

        # Should NOT have universal_patterns
        assert (
            "universal_patterns" not in enhanced.metadata
            or not enhanced.metadata["universal_patterns"]
        )

    def test_confidence_boost_from_universal_patterns(self):
        """Test that universal patterns boost confidence"""
        sql_code = """
        CREATE TABLE contacts (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255),
            status TEXT,
            deleted_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );

        UPDATE contacts
        SET status = 'qualified', deleted_at = NULL
        WHERE id = 1 AND status = 'lead';
        """

        result = ConversionResult(
            function_name="qualify_contact",
            schema="public",
            parameters=[],
            return_type="VOID",
            steps=[],
            confidence=0.85,
        )

        enhanced = self.enhancer.enhance(result, source_code=sql_code, language="sql")

        # Should detect multiple patterns (state_machine, soft_delete, audit_trail)
        assert "universal_patterns" in enhanced.metadata
        assert len(enhanced.metadata["universal_patterns"]) >= 2

        # Confidence should be boosted
        assert enhanced.confidence > 0.85

    def test_pattern_merging_with_sql_patterns(self):
        """Test that universal patterns merge with SQL-specific patterns"""
        sql_code = """
        CREATE TABLE contacts (
            id SERIAL PRIMARY KEY,
            status TEXT
        );

        CREATE OR REPLACE FUNCTION qualify_contact(p_id INT)
        RETURNS VOID AS $$
        BEGIN
            UPDATE contacts SET status = 'qualified' WHERE id = p_id AND status = 'lead';
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION close_contact(p_id INT)
        RETURNS VOID AS $$
        BEGIN
            UPDATE contacts SET status = 'closed' WHERE id = p_id AND status = 'qualified';
        END;
        $$ LANGUAGE plpgsql;
        """

        result = ConversionResult(
            function_name="update_status",
            schema="public",
            parameters=[],
            return_type="VOID",
            steps=[
                ActionStep(
                    type="query",
                    expression="UPDATE contacts SET status = 'qualified' WHERE id = 1 AND status = 'lead'",
                )
            ],
            confidence=0.85,
        )

        enhanced = self.enhancer.enhance(result, source_code=sql_code, language="sql")

        # Should have universal_patterns detected
        assert "universal_patterns" in enhanced.metadata

        # Universal patterns should include state_machine (from the UPDATE statements)
        pattern_names = [p["name"] for p in enhanced.metadata["universal_patterns"]]
        assert "state_machine" in pattern_names

    def test_multiple_universal_patterns(self):
        """Test detection of multiple universal patterns in one code snippet"""
        sql_code = """
        CREATE TABLE organizations (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255),
            tenant_id UUID NOT NULL,
            parent_id INTEGER REFERENCES organizations(id),
            deleted_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            created_by INTEGER,
            updated_by INTEGER
        );
        """

        result = ConversionResult(
            function_name="create_organization",
            schema="public",
            parameters=[],
            return_type="VOID",
            steps=[],
            confidence=0.85,
        )

        enhanced = self.enhancer.enhance(result, source_code=sql_code, language="sql")

        # Should detect multiple patterns
        pattern_names = [p["name"] for p in enhanced.metadata["universal_patterns"]]

        # Expected patterns: multi_tenant, hierarchical, soft_delete, audit_trail
        assert "multi_tenant" in pattern_names
        assert "hierarchical" in pattern_names
        assert "soft_delete" in pattern_names
        assert "audit_trail" in pattern_names

        # Confidence should be significantly boosted
        assert enhanced.confidence >= 0.88


class TestLanguageSpecificEnhancements:
    """Test that language-specific enhancements only run for SQL"""

    def setup_method(self):
        self.enhancer = HeuristicEnhancer()

    def test_sql_gets_all_enhancements(self):
        """Test that SQL gets variable inference + control flow + patterns"""
        sql_code = "SELECT 1"
        result = ConversionResult(
            function_name="test",
            schema="public",
            parameters=[],
            return_type="VOID",
            steps=[],
            confidence=0.85,
        )

        enhanced = self.enhancer.enhance(result, source_code=sql_code, language="sql")

        # Should have variable_purposes metadata (even if empty)
        assert "variable_purposes" in enhanced.metadata

    def test_non_sql_skips_sql_enhancements(self):
        """Test that non-SQL languages skip SQL-specific enhancements"""
        python_code = "class Foo: pass"
        result = ConversionResult(
            function_name="test",
            schema="public",
            parameters=[],
            return_type="VOID",
            steps=[],
            confidence=0.85,
        )

        enhanced = self.enhancer.enhance(result, source_code=python_code, language="python")

        # Should still have metadata
        assert hasattr(enhanced, "metadata")

        # Variable purposes should be empty (not inferred for Python)
        assert enhanced.metadata.get("variable_purposes", {}) == {}
