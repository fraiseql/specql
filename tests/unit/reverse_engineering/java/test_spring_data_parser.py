"""
Unit tests for Spring Data repository parser
"""

import pytest

from reverse_engineering.java_action_parser import JavaActionParser


class TestSpringDataParser:
    """Test Spring Data repository action detection"""

    @pytest.fixture
    def parser(self):
        return JavaActionParser()

    def test_crud_repository_methods(self, parser):
        """Test detecting standard CRUD repository methods"""
        java_code = """
package com.example.repository;

import org.springframework.data.repository.CrudRepository;

public interface ContactRepository extends CrudRepository<Contact, Long> {
    // Standard methods inherited: save(), findById(), findAll(), delete()
}
"""
        # EXPECTED TO FAIL: Repository analysis not implemented
        actions = parser.extract_repository_actions_from_code(java_code)

        # Should detect inherited CRUD methods
        assert len(actions) >= 4
        assert any(a["type"] == "create" for a in actions)  # save
        assert any(a["type"] == "read" for a in actions)  # findById, findAll
        # Note: CrudRepository doesn't have a separate update method
        assert any(a["type"] == "delete" for a in actions)  # deleteById

    def test_custom_query_methods(self, parser):
        """Test detecting custom query methods by naming convention"""
        java_code = """
public interface ContactRepository extends JpaRepository<Contact, Long> {
    List<Contact> findByEmail(String email);
    Contact findByEmailAndCompanyId(String email, Long companyId);
    List<Contact> findByActiveTrue();
    void deleteByEmail(String email);
}
"""
        actions = parser.extract_repository_actions_from_code(java_code)

        # EXPECTED TO FAIL
        find_by_email = next(a for a in actions if a["name"] == "findByEmail")
        assert find_by_email["type"] == "read"

        delete_by_email = next(a for a in actions if a["name"] == "deleteByEmail")
        assert delete_by_email["type"] == "delete"

    def test_query_annotation(self, parser):
        """Test detecting @Query annotation"""
        java_code = """
public interface ContactRepository extends JpaRepository<Contact, Long> {
    @Query("SELECT c FROM Contact c WHERE c.email = :email")
    Contact findContactByEmail(@Param("email") String email);
}
"""
        actions = parser.extract_repository_actions_from_code(java_code)

        # EXPECTED TO FAIL
        assert len(actions) >= 5  # 4 standard + 1 custom
        find_contact_action = next(a for a in actions if a["name"] == "findContactByEmail")
        assert find_contact_action["type"] == "read"
        assert find_contact_action["has_custom_query"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
