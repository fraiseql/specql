"""
Unit tests for Pattern Repository Pattern implementation (Phase 5)

Tests the repository pattern architecture for pattern library operations.
"""

import pytest
from unittest.mock import Mock, patch
from src.domain.entities.pattern import Pattern, PatternCategory, SourceType
from src.domain.repositories.pattern_repository import PatternRepository
from src.application.services.pattern_service import PatternService


class TestPatternRepositoryPattern:
    """Test the pattern repository pattern implementation"""

    def test_pattern_entity_creation(self):
        """Test creating a valid pattern entity"""
        pattern = Pattern(
            id=1,
            name="test_pattern",
            category=PatternCategory.WORKFLOW,
            description="A test pattern",
            parameters={"param1": "value1"},
            implementation={"field": "value"},
            source_type=SourceType.MANUAL,
            complexity_score=5.0
        )

        assert pattern.name == "test_pattern"
        assert pattern.category == PatternCategory.WORKFLOW
        assert pattern.is_active  is True
        assert not pattern.has_embedding

    def test_pattern_business_logic(self):
        """Test pattern business logic methods"""
        pattern = Pattern(
            id=None,
            name="test_pattern",
            category=PatternCategory.WORKFLOW,
            description="A test pattern"
        )

        # Test deprecation
        pattern.mark_deprecated("No longer needed")
        assert pattern.deprecated  is True
        assert pattern.deprecated_reason == "No longer needed"
        assert not pattern.is_active

        # Test usage increment
        initial_usage = pattern.times_instantiated
        pattern.increment_usage()
        assert pattern.times_instantiated == initial_usage + 1

    def test_pattern_validation(self):
        """Test pattern validation rules"""
        # Valid pattern
        Pattern(
            id=None,
            name="valid_pattern",
            category=PatternCategory.WORKFLOW,
            description="Valid description"
        )
        # Should not raise

        # Invalid patterns
        with pytest.raises(ValueError, match="Pattern name cannot be empty"):
            Pattern(id=None, name="", category=PatternCategory.WORKFLOW, description="test")

        with pytest.raises(ValueError, match="Pattern description cannot be empty"):
            Pattern(id=None, name="test", category=PatternCategory.WORKFLOW, description="")

        with pytest.raises(ValueError, match="Complexity score must be between 0 and 10"):
            Pattern(id=None, name="test", category=PatternCategory.WORKFLOW, description="test", complexity_score=15.0)

    def test_pattern_service_with_mock_repository(self):
        """Test PatternService with mocked repository"""
        # Create mock repository
        mock_repo = Mock(spec=PatternRepository)

        # Create service
        service = PatternService(mock_repo)

        # Test create pattern
        pattern = service.create_pattern(
            name="test_pattern",
            category="workflow",
            description="Test pattern",
            parameters={"test": "value"}
        )

        # Verify repository was called
        mock_repo.save.assert_called_once()
        assert pattern.name == "test_pattern"
        assert pattern.category == PatternCategory.WORKFLOW

        # Test get pattern
        mock_pattern = Mock()
        mock_repo.get.return_value = mock_pattern
        result = service.get_pattern("test_pattern")
        mock_repo.get.assert_called_once_with("test_pattern")
        assert result == mock_pattern

    def test_pattern_service_find_by_category(self):
        """Test finding patterns by category"""
        mock_repo = Mock(spec=PatternRepository)
        mock_patterns = [
            Mock(category=PatternCategory.WORKFLOW),
            Mock(category=PatternCategory.VALIDATION)
        ]
        mock_repo.find_by_category.return_value = mock_patterns

        service = PatternService(mock_repo)
        result = service.find_patterns_by_category("workflow")

        mock_repo.find_by_category.assert_called_once_with("workflow")
        assert result == mock_patterns

    def test_pattern_service_update_pattern(self):
        """Test updating an existing pattern"""
        mock_repo = Mock(spec=PatternRepository)
        existing_pattern = Pattern(
            id=1,
            name="existing",
            category=PatternCategory.WORKFLOW,
            description="Original description"
        )
        mock_repo.get.return_value = existing_pattern

        service = PatternService(mock_repo)

        updated = service.update_pattern(
            name="existing",
            description="Updated description",
            complexity_score=7.0
        )

        assert updated.description == "Updated description"
        assert updated.complexity_score == 7.0
        mock_repo.save.assert_called_once()

    def test_pattern_service_deprecate_pattern(self):
        """Test deprecating a pattern"""
        mock_repo = Mock(spec=PatternRepository)
        existing_pattern = Pattern(
            id=1,
            name="to_deprecate",
            category=PatternCategory.WORKFLOW,
            description="Pattern to deprecate"
        )
        mock_repo.get.return_value = existing_pattern

        service = PatternService(mock_repo)

        service.deprecate_pattern("to_deprecate", "No longer needed")

        assert existing_pattern.deprecated  is True
        assert existing_pattern.deprecated_reason == "No longer needed"
        mock_repo.save.assert_called_once()

    def test_pattern_service_increment_usage(self):
        """Test incrementing pattern usage"""
        mock_repo = Mock(spec=PatternRepository)
        existing_pattern = Pattern(
            id=1,
            name="used_pattern",
            category=PatternCategory.WORKFLOW,
            description="Pattern to use",
            times_instantiated=5
        )
        mock_repo.get.return_value = existing_pattern

        service = PatternService(mock_repo)

        service.increment_pattern_usage("used_pattern")

        assert existing_pattern.times_instantiated == 6
        mock_repo.save.assert_called_once()


class TestPatternServiceFactory:
    """Test the PatternServiceFactory"""

    def test_get_pattern_service_with_fallback(self):
        """Test service factory with fallback behavior"""
        from src.application.services.pattern_service_factory import PatternServiceFactory

        # Mock the config to return our mock repository
        with patch('src.application.services.pattern_service_factory.get_config') as mock_get_config:
            mock_config = Mock()
            mock_repo = Mock(spec=PatternRepository)
            mock_config.get_pattern_repository.return_value = mock_repo
            mock_get_config.return_value = mock_config

            service = PatternServiceFactory.get_pattern_service()

            # Should return a PatternService instance
            assert isinstance(service, PatternService)
            assert service.repository == mock_repo

    def test_get_pattern_service_fallback_on_failure(self):
        """Test that service factory falls back to in-memory on PostgreSQL failure"""
        from src.application.services.pattern_service_factory import PatternServiceFactory

        # Mock config to simulate PostgreSQL failure
        with patch('src.application.services.pattern_service_factory.get_config') as mock_get_config:
            mock_config = Mock()
            # Make get_pattern_repository raise an exception
            mock_config.get_pattern_repository.side_effect = RuntimeError("PostgreSQL connection failed")
            mock_get_config.return_value = mock_config

            # Should still return a service (with in-memory fallback)
            service = PatternServiceFactory.get_pattern_service_with_fallback()
            assert isinstance(service, PatternService)


class TestPatternValueObjects:
    """Test pattern value objects (enums)"""

    def test_pattern_category_enum(self):
        """Test PatternCategory enum values"""
        assert PatternCategory.WORKFLOW.value == "workflow"
        assert PatternCategory.VALIDATION.value == "validation"
        assert PatternCategory.AUDIT.value == "audit"
        assert PatternCategory.HIERARCHY.value == "hierarchy"
        assert PatternCategory.STATE_MACHINE.value == "state_machine"
        assert PatternCategory.APPROVAL.value == "approval"
        assert PatternCategory.NOTIFICATION.value == "notification"
        assert PatternCategory.CALCULATION.value == "calculation"
        assert PatternCategory.SOFT_DELETE.value == "soft_delete"

    def test_source_type_enum(self):
        """Test SourceType enum values"""
        assert SourceType.MANUAL.value == "manual"
        assert SourceType.LLM_GENERATED.value == "llm_generated"
        assert SourceType.DISCOVERED.value == "discovered"
        assert SourceType.MIGRATED.value == "migrated"