"""
Mutation Documentation Generator

Generates comprehensive documentation for GraphQL mutations including:
- API reference
- Usage examples
- Error handling
- Cache behavior

Output: mutations.md
"""

from pathlib import Path

from src.core.ast_models import Action, Entity


class MutationDocsGenerator:
    """
    Generates documentation for GraphQL mutations.

    This generator creates:
    - API reference documentation
    - Usage examples in React/TypeScript
    - Error handling guides
    - Cache invalidation documentation
    """

    def __init__(self, output_dir: Path):
        """
        Initialize the generator.

        Args:
            output_dir: Directory to write the mutations.md file
        """
        self.output_dir = output_dir
        self.docs: list[str] = []

    def generate_docs(self, entities: list[Entity]) -> None:
        """
        Generate mutation documentation for all entities.

        Args:
            entities: List of parsed entity definitions
        """
        self.docs = []

        # Add header
        self._add_header()

        # Generate docs for each entity
        for entity in entities:
            self._generate_entity_docs(entity)

        # Add usage examples
        self._add_usage_examples()

        # Write to file
        output_file = self.output_dir / "mutations.md"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(self.docs))

    def _add_header(self) -> None:
        """Add document header."""
        header = """# GraphQL Mutations API Reference

This document provides comprehensive documentation for all GraphQL mutations generated from SpecQL entities.

## Overview

Mutations are operations that modify data on the server. Each mutation follows a consistent pattern:
- Takes an `input` parameter with mutation-specific data
- Returns a `MutationResult` with success/error information
- Includes proper error handling and validation

## Mutation Result Format

All mutations return a `MutationResult<T>` where T is the specific result type:

```typescript
interface MutationResult<T> {
  success: boolean;
  data?: T;
  error?: string;
  code?: string;
}
```

## Error Codes

Common error codes across all mutations:
- `VALIDATION_ERROR`: Input validation failed
- `PERMISSION_DENIED`: User lacks required permissions
- `NOT_FOUND`: Referenced entity doesn't exist
- `CONFLICT`: Operation would create an invalid state
- `INTERNAL_ERROR`: Unexpected server error

---

"""
        self.docs.append(header)

    def _generate_entity_docs(self, entity: Entity) -> None:
        """
        Generate documentation for a single entity.

        Args:
            entity: The entity to document
        """
        entity_name = entity.name

        self.docs.append(f"## {entity_name} Mutations")
        self.docs.append("")

        if not entity.actions:
            self.docs.append("No mutations defined for this entity.")
            self.docs.append("")
            return

        for action in entity.actions:
            self._generate_action_docs(entity, action)

        self.docs.append("")

    def _generate_action_docs(self, entity: Entity, action: Action) -> None:
        """
        Generate documentation for a single action.

        Args:
            entity: The entity containing the action
            action: The action to document
        """
        action_name = action.name
        pascal_name = self._to_pascal_case(action_name)
        camel_name = self._to_camel_case(action_name)

        # Mutation header
        self.docs.append(f"### `{camel_name}`")
        self.docs.append("")

        # Description
        description = self._get_action_description(entity, action)
        self.docs.append(description)
        self.docs.append("")

        # Permissions
        if action.requires:
            self.docs.append(f"**Required Permission:** `{action.requires}`")
            self.docs.append("")

        # GraphQL signature
        self.docs.append("#### GraphQL Signature")
        self.docs.append("")
        self.docs.append("```graphql")
        self.docs.append(f"mutation {pascal_name}($input: {pascal_name}Input!) {{")
        self.docs.append(f"  {camel_name}(input: $input) {{")
        self.docs.append("    success")
        self.docs.append("    data {")
        self.docs.append("      ... on {pascal_name}Success {")
        self._add_success_fields_docs(entity, action, indent="        ")
        self.docs.append("      }")
        self.docs.append("      ... on {pascal_name}Error {")
        self.docs.append("        code")
        self.docs.append("        message")
        self.docs.append("        details")
        self.docs.append("      }")
        self.docs.append("    }")
        self.docs.append("    error")
        self.docs.append("    code")
        self.docs.append("  }")
        self.docs.append("}")
        self.docs.append("```")
        self.docs.append("")

        # Input parameters
        self._add_input_docs(entity, action)

        # Success response
        self._add_success_response_docs(entity, action)

        # Error responses
        self._add_error_docs(action)

        # Usage example
        self._add_usage_example(entity, action)

        # Cache behavior
        self._add_cache_behavior_docs(entity, action)

        self.docs.append("---")
        self.docs.append("")

    def _add_success_fields_docs(
        self, entity: Entity, action: Action, indent: str
    ) -> None:
        """
        Add success fields documentation.

        Args:
            entity: The entity
            action: The action
            indent: Indentation string
        """
        action_name = action.name
        entity_name = entity.name

        if action_name.startswith("create_"):
            self.docs.append(f"{indent}{entity_name.lower()} {{")
            self._add_entity_fields_list(entity, indent + "  ")
            self.docs.append(f"{indent}}}")
            self.docs.append(f"{indent}message")
        elif action_name.startswith("update_"):
            self.docs.append(f"{indent}{entity_name.lower()} {{")
            self._add_entity_fields_list(entity, indent + "  ")
            self.docs.append(f"{indent}}}")
            self.docs.append(f"{indent}message")
        elif action_name.startswith("delete_"):
            self.docs.append(f"{indent}success")
            self.docs.append(f"{indent}message")
        else:
            self.docs.append(f"{indent}result")
            self.docs.append(f"{indent}message")

    def _add_entity_fields_list(self, entity: Entity, indent: str) -> None:
        """
        Add list of entity fields.

        Args:
            entity: The entity
            indent: Indentation string
        """
        for field_name in entity.fields.keys():
            self.docs.append(f"{indent}{field_name}")

    def _add_input_docs(self, entity: Entity, action: Action) -> None:
        """
        Add input parameters documentation.

        Args:
            entity: The entity
            action: The action
        """
        action_name = action.name
        pascal_name = self._to_pascal_case(action_name)

        self.docs.append("#### Input Parameters")
        self.docs.append("")
        self.docs.append(f"Type: `{pascal_name}Input`")
        self.docs.append("")

        if action_name.startswith("create_"):
            self.docs.append(
                "Fields from the {entity.name} entity (excluding auto-generated fields like `id`, `created_at`, etc.):"
            )
            self.docs.append("")
            self.docs.append("| Field | Type | Required | Description |")
            self.docs.append("|-------|------|----------|-------------|")

            for field_name, field_def in entity.fields.items():
                if field_name not in [
                    "id",
                    "created_at",
                    "updated_at",
                    "created_by",
                    "updated_by",
                ]:
                    required = (
                        "No"
                        if field_def.nullable or field_def.default is not None
                        else "Yes"
                    )
                    ts_type = self._field_to_typescript_doc(field_def)
                    desc = field_def.description or f"{field_name} field"
                    self.docs.append(
                        f"| `{field_name}` | `{ts_type}` | {required} | {desc} |"
                    )

        elif action_name.startswith("update_"):
            self.docs.append(
                "Update operations require the entity ID and optionally any fields to update:"
            )
            self.docs.append("")
            self.docs.append("| Field | Type | Required | Description |")
            self.docs.append("|-------|------|----------|-------------|")
            self.docs.append("| `id` | `UUID` | Yes | Entity ID to update |")

            for field_name, field_def in entity.fields.items():
                if field_name not in [
                    "id",
                    "created_at",
                    "updated_at",
                    "created_by",
                    "updated_by",
                ]:
                    ts_type = self._field_to_typescript_doc(field_def)
                    desc = field_def.description or f"{field_name} field"
                    self.docs.append(f"| `{field_name}` | `{ts_type}` | No | {desc} |")

        elif action_name.startswith("delete_"):
            self.docs.append("Delete operations only require the entity ID:")
            self.docs.append("")
            self.docs.append("| Field | Type | Required | Description |")
            self.docs.append("|-------|------|----------|-------------|")
            self.docs.append("| `id` | `UUID` | Yes | Entity ID to delete |")

        self.docs.append("")

    def _add_success_response_docs(self, entity: Entity, action: Action) -> None:
        """
        Add success response documentation.

        Args:
            entity: The entity
            action: The action
        """
        action_name = action.name
        pascal_name = self._to_pascal_case(action_name)

        self.docs.append("#### Success Response")
        self.docs.append("")
        self.docs.append(f"Type: `{pascal_name}Success`")
        self.docs.append("")

        if action_name.startswith("create_"):
            self.docs.append(
                "- `{entity.name.lower()}`: The newly created {entity.name} entity with all fields populated"
            )
            self.docs.append("- `message`: Success confirmation message")
        elif action_name.startswith("update_"):
            self.docs.append(
                "- `{entity.name.lower()}`: The updated {entity.name} entity with all fields populated"
            )
            self.docs.append("- `message`: Success confirmation message")
        elif action_name.startswith("delete_"):
            self.docs.append("- `success`: Always `true` for successful deletions")
            self.docs.append("- `message`: Success confirmation message")
        else:
            self.docs.append("- `result`: Operation-specific result data")
            self.docs.append("- `message`: Success confirmation message")

        self.docs.append("")

    def _add_error_docs(self, action: Action) -> None:
        """
        Add error response documentation.

        Args:
            action: The action
        """
        self.docs.append("#### Error Responses")
        self.docs.append("")
        self.docs.append("All mutations can return the following error structure:")
        self.docs.append("")
        self.docs.append("- `code`: Error code (string)")
        self.docs.append("- `message`: Human-readable error message")
        self.docs.append("- `details`: Additional error details (optional)")
        self.docs.append("")

        # Add action-specific errors
        action_name = action.name
        if action_name.startswith("create_"):
            self.docs.append("**Possible errors:**")
            self.docs.append("- `VALIDATION_ERROR`: Invalid input data")
            self.docs.append("- `PERMISSION_DENIED`: Insufficient permissions")
            self.docs.append(
                "- `CONFLICT`: Entity already exists or constraint violation"
            )
        elif action_name.startswith("update_"):
            self.docs.append("**Possible errors:**")
            self.docs.append("- `VALIDATION_ERROR`: Invalid input data")
            self.docs.append("- `NOT_FOUND`: Entity with given ID doesn't exist")
            self.docs.append("- `PERMISSION_DENIED`: Insufficient permissions")
            self.docs.append("- `CONFLICT`: Update would violate constraints")
        elif action_name.startswith("delete_"):
            self.docs.append("**Possible errors:**")
            self.docs.append("- `NOT_FOUND`: Entity with given ID doesn't exist")
            self.docs.append("- `PERMISSION_DENIED`: Insufficient permissions")
            self.docs.append(
                "- `CONFLICT`: Deletion would violate referential integrity"
            )

        self.docs.append("")

    def _add_usage_example(self, entity: Entity, action: Action) -> None:
        """
        Add usage example in React/TypeScript.

        Args:
            entity: The entity
            action: The action
        """
        action_name = action.name
        self._to_pascal_case(action_name)
        camel_name = self._to_camel_case(action_name)
        f"use{camel_name[0].upper()}{camel_name[1:]}"

        self.docs.append("#### Usage Example")
        self.docs.append("")
        self.docs.append("```typescript")
        self.docs.append("import { {hook_name} } from '../hooks';")
        self.docs.append("import type { {pascal_name}Input } from '../types';")
        self.docs.append("")
        self.docs.append("function {entity.name}Form() {{")
        self.docs.append(
            "  const [{camel_name}, {{ loading, error }}] = {hook_name}();"
        )
        self.docs.append("")
        self.docs.append(
            "  const handleSubmit = async (input: {pascal_name}Input) => {{"
        )
        self.docs.append("    try {{")
        self.docs.append("      const result = await {camel_name}({{")
        self.docs.append("        variables: {{ input }},")
        self.docs.append("      }});")
        self.docs.append("")
        self.docs.append("      if (result.data?.{camel_name}.success) {{")
        self.docs.append(
            "        // console.log('Success:', result.data.{camel_name}.data);"
        )
        self.docs.append("      }} else {{")
        self.docs.append(
            "        console.error('Error:', result.data?.{camel_name}.error);"
        )
        self.docs.append("      }}")
        self.docs.append("    }} catch (err) {{")
        self.docs.append("      console.error('Mutation failed:', err);")
        self.docs.append("    }}")
        self.docs.append("  }};")
        self.docs.append("")
        self.docs.append("  return (")
        self.docs.append("    <form onSubmit={{handleSubmit}}>")
        self.docs.append('      <button type="submit" disabled={{loading}}>')
        self.docs.append("        {{loading ? 'Submitting...' : 'Submit'}}")
        self.docs.append("      </button>")
        self.docs.append("      {{error && <div>Error: {{error.message}}</div>}}")
        self.docs.append("    </form>")
        self.docs.append("  );")
        self.docs.append("}}")
        self.docs.append("```")
        self.docs.append("")

    def _add_cache_behavior_docs(self, entity: Entity, action: Action) -> None:
        """
        Add cache behavior documentation.

        Args:
            entity: The entity
            action: The action
        """
        action_name = action.name

        self.docs.append("#### Cache Behavior")
        self.docs.append("")

        if action_name.startswith("create_"):
            self.docs.append("**Automatic cache updates:**")
            self.docs.append(
                "- Adds the new entity to any cached `{entity.name.lower()}s` queries"
            )
            self.docs.append("- Updates list views immediately")
            self.docs.append("")
            self.docs.append("**Recommended:** No manual cache updates needed")
        elif action_name.startswith("update_"):
            self.docs.append("**Automatic cache updates:**")
            self.docs.append("- Updates the specific entity in cache by ID")
            self.docs.append("- Refreshes any cached queries containing this entity")
            self.docs.append("")
            self.docs.append("**Recommended:** No manual cache updates needed")
        elif action_name.startswith("delete_"):
            self.docs.append("**Automatic cache updates:**")
            self.docs.append("- Removes the entity from cache completely")
            self.docs.append("- Updates any cached lists to remove the deleted item")
            self.docs.append("- Triggers garbage collection to clean up references")
            self.docs.append("")
            self.docs.append("**Recommended:** No manual cache updates needed")
        else:
            self.docs.append(
                "**Cache behavior:** Custom - check mutation impacts for details"
            )

        self.docs.append("")

    def _add_usage_examples(self) -> None:
        """Add general usage examples section."""
        examples = """

## General Usage Patterns

### Error Handling

```typescript
const [mutation, { loading, error }] = useCreateContact();

const handleSubmit = async (input: CreateContactInput) => {
  const result = await mutation({
    variables: { input },
  });

  if (result.data?.createContact.success) {
    // Success - entity was created
    const newContact = result.data.createContact.data.contact;
    navigate(`/contacts/${newContact.id}`);
  } else {
    // Handle error
    const error = result.data?.createContact.error;
    const code = result.data?.createContact.code;

    switch (code) {
      case 'VALIDATION_ERROR':
        setFieldErrors(error.details);
        break;
      case 'PERMISSION_DENIED':
        showPermissionError();
        break;
      default:
        showGenericError(error.message);
    }
  }
};
```

### Loading States

```typescript
const [mutation, { loading }] = useUpdateContact();

return (
  <button
    onClick={handleUpdate}
    disabled={loading}
  >
    {loading ? 'Updating...' : 'Update Contact'}
  </button>
);
```

### Optimistic Updates

For better UX, mutations include optimistic updates where possible:

```typescript
// For deletes, the UI updates immediately
const [deleteContact] = useDeleteContact();

const handleDelete = async (contactId: string) => {
  // UI updates immediately (optimistic)
  await deleteContact({
    variables: { input: { id: contactId } },
  });
  // Cache is updated automatically
};
```

### Cache Management

Apollo Client automatically manages cache updates for all mutations. Manual cache operations are typically not needed.

---

*Generated automatically from SpecQL entity definitions*
"""
        self.docs.append(examples)

    def _get_action_description(self, entity: Entity, action: Action) -> str:
        """
        Get human-readable description for an action.

        Args:
            entity: The entity
            action: The action

        Returns:
            Description string
        """
        action_name = action.name
        entity_name = entity.name

        if action_name.startswith("create_"):
            return f"Creates a new {entity_name} record with the provided data."
        elif action_name.startswith("update_"):
            return f"Updates an existing {entity_name} record with the provided data."
        elif action_name.startswith("delete_"):
            return f"Deletes an existing {entity_name} record."
        else:
            return f"Performs a {action_name.replace('_', ' ')} operation on a {entity_name} record."

    def _field_to_typescript_doc(self, field_def) -> str:
        """
        Convert field definition to TypeScript type for documentation.

        Args:
            field_def: The field definition

        Returns:
            TypeScript type string for docs
        """
        # Simplified version for docs
        type_name = field_def.type_name

        type_mapping = {
            "text": "string",
            "varchar": "string",
            "integer": "number",
            "bigint": "number",
            "numeric": "number",
            "boolean": "boolean",
            "date": "Date",
            "timestamptz": "DateTime",
            "uuid": "UUID",
            "jsonb": "JSONValue",
        }

        return type_mapping.get(type_name, "any")

    def _to_camel_case(self, snake_str: str) -> str:
        """
        Convert snake_case to camelCase.

        Args:
            snake_str: String in snake_case format

        Returns:
            String in camelCase format
        """
        components = snake_str.split("_")
        return components[0] + "".join(x.capitalize() for x in components[1:])

    def _to_pascal_case(self, snake_str: str) -> str:
        """
        Convert snake_case to PascalCase.

        Args:
            snake_str: String in snake_case format

        Returns:
            String in PascalCase format
        """
        components = snake_str.split("_")
        return "".join(x.capitalize() for x in components)
