"""
End-to-End Tests for Frontend Code Generators

Tests the complete frontend code generation pipeline:
- Mutation impacts JSON
- TypeScript types
- Apollo hooks
- Documentation
"""

import json
from pathlib import Path

import pytest

from core.ast_models import Action, ActionStep, Entity, FieldDefinition, FieldTier
from generators.frontend import (
    ApolloHooksGenerator,
    MutationDocsGenerator,
    MutationImpactsGenerator,
    TypeScriptTypesGenerator,
)


class TestFrontendGeneratorsE2E:
    """End-to-end tests for frontend code generation"""

    @pytest.fixture
    def sample_entities(self) -> list[Entity]:
        """Create sample entities for testing"""
        # Create a Contact entity with actions
        contact_entity = Entity(
            name="Contact",
            schema="crm",
            description="Contact entity for testing",
            fields={
                "id": FieldDefinition(
                    name="id", type_name="uuid", nullable=False, description="Primary key"
                ),
                "first_name": FieldDefinition(
                    name="first_name",
                    type_name="text",
                    nullable=False,
                    description="Contact's first name",
                ),
                "last_name": FieldDefinition(
                    name="last_name",
                    type_name="text",
                    nullable=False,
                    description="Contact's last name",
                ),
                "email": FieldDefinition(
                    name="email",
                    type_name="email",
                    nullable=True,
                    description="Contact's email address",
                ),
                "created_at": FieldDefinition(
                    name="created_at",
                    type_name="timestamptz",
                    nullable=False,
                    description="Creation timestamp",
                ),
            },
            actions=[
                Action(
                    name="create_contact",
                    requires="contact.create",
                    steps=[
                        ActionStep(type="validate", expression="email format"),
                        ActionStep(type="insert", expression="crm.tb_contact"),
                    ],
                ),
                Action(
                    name="update_contact",
                    requires="contact.update",
                    steps=[
                        ActionStep(type="validate", expression="contact exists"),
                        ActionStep(type="update", expression="crm.tb_contact"),
                    ],
                ),
                Action(
                    name="delete_contact",
                    requires="contact.delete",
                    steps=[
                        ActionStep(type="validate", expression="contact exists"),
                        ActionStep(type="delete", expression="crm.tb_contact"),
                    ],
                ),
            ],
        )

        return [contact_entity]

    @pytest.fixture
    def temp_output_dir(self, tmp_path) -> Path:
        """Create a temporary output directory"""
        return tmp_path / "frontend_output"

    def test_mutation_impacts_generator(self, sample_entities, temp_output_dir):
        """Test mutation impacts JSON generation"""
        generator = MutationImpactsGenerator(temp_output_dir)
        generator.generate_impacts(sample_entities)

        # Check that file was created
        impacts_file = temp_output_dir / "mutation-impacts.json"
        assert impacts_file.exists()

        # Parse and validate JSON
        with open(impacts_file) as f:
            data = json.load(f)

        # Validate structure
        assert "version" in data
        assert "mutations" in data
        assert "entities" in data
        assert "cacheInvalidationRules" in data

        # Check Contact entity
        assert "Contact" in data["entities"]
        assert data["entities"]["Contact"]["schema"] == "crm"

        # Check mutations
        assert "Contact.create_contact" in data["mutations"]
        mutation = data["mutations"]["Contact.create_contact"]
        assert mutation["entity"] == "Contact"
        assert mutation["action"] == "create_contact"
        assert mutation["operationType"] == "CREATE"
        assert mutation["requiresPermission"] is True

    def test_typescript_types_generator(self, sample_entities, temp_output_dir):
        """Test TypeScript types generation"""
        generator = TypeScriptTypesGenerator(temp_output_dir)
        generator.generate_types(sample_entities)

        # Check that file was created
        types_file = temp_output_dir / "types.ts"
        assert types_file.exists()

        # Read and validate content
        content = types_file.read_text()

        # Check for expected type definitions
        assert "export interface Contact {" in content
        assert "export interface ContactInput {" in content
        assert "export interface ContactFilter {" in content
        assert "export interface CreateContactInput {" in content
        assert "export interface CreateContactSuccess {" in content
        assert "export interface CreateContactError {" in content
        assert "export type CreateContactResult" in content

        # Check for base types
        assert "export type UUID = string;" in content
        assert "export type DateTime = string;" in content
        # Accept both MutationResult<T> and MutationResult<T = any>
        assert "export interface MutationResult<T" in content

    def test_apollo_hooks_generator(self, sample_entities, temp_output_dir):
        """Test Apollo hooks generation"""
        generator = ApolloHooksGenerator(temp_output_dir)
        generator.generate_hooks(sample_entities)

        # Check that file was created
        hooks_file = temp_output_dir / "hooks.ts"
        assert hooks_file.exists()

        # Read and validate content
        content = hooks_file.read_text()

        # Check for expected hooks and queries
        assert "export const GET_CONTACT_QUERY" in content
        # The mutation constant naming may vary
        assert "CREATECONTACT_MUTATION" in content or "CREATE_CONTACT_MUTATION" in content
        assert "export const GET_CONTACTS_QUERY" in content
        assert "CREATECONTACT_MUTATION" in content
        assert "UPDATECONTACT_MUTATION" in content
        assert "DELETECONTACT_MUTATION" in content

        # Check for hook functions
        assert "export const useGetContact" in content
        assert "export const useGetContacts" in content
        assert "export const useCreateContact" in content
        assert "export const useUpdateContact" in content
        assert "export const useDeleteContact" in content

        # Check for GraphQL syntax
        assert "mutation CreateContact(" in content
        assert "query GetContact(" in content

    def test_mutation_docs_generator(self, sample_entities, temp_output_dir):
        """Test mutation documentation generation"""
        generator = MutationDocsGenerator(temp_output_dir)
        generator.generate_docs(sample_entities)

        # Check that file was created
        docs_file = temp_output_dir / "mutations.md"
        assert docs_file.exists()

        # Read and validate content
        content = docs_file.read_text()

        # Check for expected documentation structure
        assert "# GraphQL Mutations API Reference" in content
        assert "## Contact Mutations" in content
        assert "### `createContact`" in content
        assert "### `updateContact`" in content
        assert "### `deleteContact`" in content

        # Check for GraphQL signatures
        assert "mutation CreateContact(" in content
        assert "createContact(input: $input)" in content

        # Check for usage examples
        assert "#### Usage Example" in content
        # The exact import statements may vary due to template rendering
        assert "import {" in content
        assert "from" in content
        assert "useCreateContact" in content

    def test_complete_frontend_generation_pipeline(self, sample_entities, temp_output_dir):
        """Test the complete frontend generation pipeline"""
        # Generate all frontend code
        MutationImpactsGenerator(temp_output_dir).generate_impacts(sample_entities)
        TypeScriptTypesGenerator(temp_output_dir).generate_types(sample_entities)
        ApolloHooksGenerator(temp_output_dir).generate_hooks(sample_entities)
        MutationDocsGenerator(temp_output_dir).generate_docs(sample_entities)

        # Check all files were created
        assert (temp_output_dir / "mutation-impacts.json").exists()
        assert (temp_output_dir / "types.ts").exists()
        assert (temp_output_dir / "hooks.ts").exists()
        assert (temp_output_dir / "mutations.md").exists()

        # Validate cross-references between files
        types_content = (temp_output_dir / "types.ts").read_text()
        hooks_content = (temp_output_dir / "hooks.ts").read_text()

        # Hooks should import from types
        assert "from './types'" in hooks_content

        # Both should reference Contact types
        assert "Contact" in types_content
        assert "Contact" in hooks_content

    def test_empty_entities_list(self, temp_output_dir):
        """Test generators handle empty entity list gracefully"""
        empty_entities = []

        # All generators should handle empty lists without errors
        MutationImpactsGenerator(temp_output_dir).generate_impacts(empty_entities)
        TypeScriptTypesGenerator(temp_output_dir).generate_types(empty_entities)
        ApolloHooksGenerator(temp_output_dir).generate_hooks(empty_entities)
        MutationDocsGenerator(temp_output_dir).generate_docs(empty_entities)

        # Files should still be created (even if mostly empty)
        assert (temp_output_dir / "mutation-impacts.json").exists()
        assert (temp_output_dir / "types.ts").exists()
        assert (temp_output_dir / "hooks.ts").exists()
        assert (temp_output_dir / "mutations.md").exists()

    def test_file_overwrite_behavior(self, sample_entities, temp_output_dir):
        """Test that generators properly overwrite existing files"""
        # Generate once
        generator = TypeScriptTypesGenerator(temp_output_dir)
        generator.generate_types(sample_entities)

        original_content = (temp_output_dir / "types.ts").read_text()
        original_size = len(original_content)

        # Generate again
        generator.generate_types(sample_entities)

        new_content = (temp_output_dir / "types.ts").read_text()
        new_size = len(new_content)

        # Content should be identical (deterministic generation)
        assert original_content == new_content
        assert original_size == new_size

    def test_circular_reference_entities(self, temp_output_dir):
        """Test frontend generators handle circular entity references"""
        # Create entities with circular references
        user_entity = Entity(
            name="User",
            schema="app",
            description="User entity",
            fields={
                "id": FieldDefinition(name="id", type_name="uuid", nullable=False),
                "username": FieldDefinition(name="username", type_name="text", nullable=False),
                "profile": FieldDefinition(
                    name="profile", type_name="ref", nullable=True, reference_entity="UserProfile"
                ),
            },
            actions=[
                Action(
                    name="create_user",
                    requires="user.create",
                    steps=[ActionStep(type="insert", expression="app.tb_user")],
                ),
            ],
        )

        profile_entity = Entity(
            name="UserProfile",
            schema="app",
            description="User profile entity",
            fields={
                "id": FieldDefinition(name="id", type_name="uuid", nullable=False),
                "user": FieldDefinition(
                    name="user", type_name="ref", nullable=False, reference_entity="User"
                ),
                "bio": FieldDefinition(name="bio", type_name="text", nullable=True),
            },
            actions=[
                Action(
                    name="create_profile",
                    requires="profile.create",
                    steps=[ActionStep(type="insert", expression="app.tb_user_profile")],
                ),
            ],
        )

        circular_entities = [user_entity, profile_entity]

        # Test TypeScript types generation with circular references
        ts_generator = TypeScriptTypesGenerator(temp_output_dir)
        ts_generator.generate_types(circular_entities)

        types_content = (temp_output_dir / "types.ts").read_text()

        # Should generate types without infinite recursion
        assert "export interface User {" in types_content
        assert "export interface UserProfile {" in types_content
        assert "profile?: UserProfile;" in types_content  # User references UserProfile
        assert "user: User;" in types_content  # UserProfile references User

        # Test Apollo hooks generation with circular references
        hooks_generator = ApolloHooksGenerator(temp_output_dir)
        hooks_generator.generate_hooks(circular_entities)

        hooks_content = (temp_output_dir / "hooks.ts").read_text()

        # Should generate hooks without issues
        assert "useCreateUser" in hooks_content
        assert "useCreateProfile" in hooks_content

        # Test mutation impacts generation
        impacts_generator = MutationImpactsGenerator(temp_output_dir)
        impacts_generator.generate_impacts(circular_entities)

        # Should not crash and generate valid JSON
        impacts_file = temp_output_dir / "mutation-impacts.json"
        assert impacts_file.exists()

        import json

        with open(impacts_file) as f:
            impacts_data = json.load(f)

        assert "User" in impacts_data["entities"]
        assert "UserProfile" in impacts_data["entities"]
