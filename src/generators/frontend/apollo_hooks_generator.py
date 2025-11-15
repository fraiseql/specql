"""
Apollo Hooks Generator

Generates React hooks using Apollo Client for GraphQL mutations.
Creates useMutation hooks with proper TypeScript typing and error handling.

Output: hooks.ts
"""

from pathlib import Path

from src.core.ast_models import Action, Entity


class ApolloHooksGenerator:
    """
    Generates Apollo Client React hooks for mutations.

    This generator creates:
    - useMutation hooks for each action
    - Proper TypeScript typing
    - Error handling and loading states
    - Cache update logic based on mutation impacts
    """

    def __init__(self, output_dir: Path):
        """
        Initialize the generator.

        Args:
            output_dir: Directory to write the hooks.ts file
        """
        self.output_dir = output_dir
        self.hooks: list[str] = []

    def generate_hooks(self, entities: list[Entity]) -> None:
        """
        Generate Apollo hooks for all entities.

        Args:
            entities: List of parsed entity definitions
        """
        self.hooks = []

        # Add header
        self._add_header()

        # Generate hooks for each entity
        for entity in entities:
            self._generate_entity_hooks(entity)

        # Write to file
        output_file = self.output_dir / "hooks.ts"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(self.hooks))

    def _add_header(self) -> None:
        """Add file header with imports."""
        header = """/**
 * Auto-generated Apollo Client React hooks
 *
 * Generated from SpecQL entity definitions
 * Do not edit manually - regenerate when entities change
 */

import { useMutation, useQuery, gql } from '@apollo/client';
import {
  MutationResult,
  PaginationInput,
  PaginatedResult,
} from './types';

// Re-export types for convenience
export type {
  MutationResult,
  PaginationInput,
  PaginatedResult,
} from './types';

"""
        self.hooks.append(header)

    def _generate_entity_hooks(self, entity: Entity) -> None:
        """
        Generate hooks for a single entity.

        Args:
            entity: The entity to generate hooks for
        """
        entity_name = entity.name

        self.hooks.append(f"// {entity_name} Hooks")
        self.hooks.append("")

        # Generate query hooks first
        self._generate_query_hooks(entity)

        # Generate mutation hooks
        for action in entity.actions:
            self._generate_mutation_hook(entity, action)

        self.hooks.append("")

    def _generate_query_hooks(self, entity: Entity) -> None:
        """
        Generate query hooks for an entity.

        Args:
            entity: The entity to generate query hooks for
        """
        entity_name = entity.name
        lower_name = entity_name.lower()

        # Get one query
        get_one_query = f"""
export const GET_{entity_name.upper()}_QUERY = gql`
  query Get{entity_name}($id: UUID!) {{
    {lower_name}(id: $id) {{
{self._build_entity_fields_fragment(entity)}
    }}
  }}
`;

export const useGet{entity_name} = (id: string) => {{
  return useQuery<{entity_name}>(GET_{entity_name.upper()}_QUERY, {{
    variables: {{ id }},
    skip: !id,
  }});
}};
"""

        # List query with pagination
        list_query = f"""
export const GET_{entity_name.upper()}S_QUERY = gql`
  query Get{entity_name}s($filter: {entity_name}Filter, $pagination: PaginationInput) {{
    {lower_name}s(filter: $filter, pagination: $pagination) {{
      items {{
{self._build_entity_fields_fragment(entity)}
      }}
      totalCount
      hasNextPage
      hasPreviousPage
    }}
  }}
`;

export const useGet{entity_name}s = (filter?: {entity_name}Filter, pagination?: PaginationInput) => {{
  return useQuery<PaginatedResult<{entity_name}>>(GET_{entity_name.upper()}S_QUERY, {{
    variables: {{ filter, pagination }},
  }});
}};
"""

        self.hooks.append(get_one_query)
        self.hooks.append(list_query)

    def _generate_mutation_hook(self, entity: Entity, action: Action) -> None:
        """
        Generate a mutation hook for a specific action.

        Args:
            entity: The entity containing the action
            action: The action to generate a hook for
        """
        action_name = action.name
        pascal_name = self._to_pascal_case(action_name)
        camel_name = self._to_camel_case(action_name)

        # Build GraphQL mutation
        mutation_gql = self._build_mutation_gql(entity, action)

        # Check if action contains call_service steps
        has_call_service = any(step.type == "call_service" for step in action.steps)

        # Build cache update logic
        cache_update = self._build_cache_update_logic(entity, action)

        # Build optimistic response
        optimistic_response = self._build_optimistic_response(entity, action)

        # Build special handling for call_service actions
        call_service_handling = ""
        if has_call_service:
            call_service_handling = self._build_call_service_handling(
                entity, action, camel_name
            )

        hook_code = f"""
export const {pascal_name.upper()}_MUTATION = gql`
{mutation_gql}
`;

export const use{camel_name[0].upper() + camel_name[1:]} = () => {{
  return useMutation<
    {{ {camel_name}: MutationResult<{pascal_name}Result> }},
    {pascal_name}Input
  >(
    {pascal_name.upper()}_MUTATION,
    {{
      {cache_update}
      {optimistic_response}
      onCompleted: (data) => {{
        {call_service_handling}
      }},
      onError: (error) => {{
        console.error(`{pascal_name} mutation failed:`, error);
      }},
    }}
  );
}};
"""

        self.hooks.append(hook_code)

    def _build_call_service_handling(
        self, entity: Entity, action: Action, camel_name: str
    ) -> str:
        """
        Build special handling for call_service actions.

        Args:
            entity: The entity containing the action
            action: The action with call_service steps
            camel_name: The camelCase version of the action name

        Returns:
            JavaScript code for handling call_service completion
        """
        action_name = action.name

        return f"""
        // Handle call_service completion
        if (data?.{camel_name}?.success && data.{camel_name}.job_id) {{
          // console.log('{action_name} initiated job:', data.{camel_name}.job_id);
          // TODO: Implement job status polling or subscription
          // You can poll job status or set up a subscription here
        }}"""

    def _build_mutation_gql(self, entity: Entity, action: Action) -> str:
        """
        Build the GraphQL mutation string.

        Args:
            entity: The entity
            action: The action

        Returns:
            GraphQL mutation string
        """
        action_name = action.name
        pascal_name = self._to_pascal_case(action_name)
        camel_name = self._to_camel_case(action_name)

        # Determine input and output types
        input_type = f"{pascal_name}Input"

        return f"""  mutation {pascal_name}($input: {input_type}!) {{
    {camel_name}(input: $input) {{
      success
      data {{
        ... on {pascal_name}Success {{
{self._build_success_fields(entity, action)}
        }}
        ... on {pascal_name}Error {{
          code
          message
          details
        }}
      }}
      error
      code
    }}
  }}"""

    def _build_success_fields(self, entity: Entity, action: Action) -> str:
        """
        Build the success fields for the mutation response.

        Args:
            entity: The entity
            action: The action

        Returns:
            GraphQL fields string
        """
        entity_name = entity.name
        action_name = action.name

        if action_name.startswith("create_"):
            return f"""          {entity_name.lower()} {{
{self._build_entity_fields_fragment(entity, indent=12)}
          }}
          message"""
        elif action_name.startswith("update_"):
            return f"""          {entity_name.lower()} {{
{self._build_entity_fields_fragment(entity, indent=12)}
          }}
          message"""
        elif action_name.startswith("delete_"):
            return """          success
          message"""
        else:
            return """          result
          message"""

    def _build_entity_fields_fragment(self, entity: Entity, indent: int = 6) -> str:
        """
        Build a GraphQL fragment for entity fields.

        Args:
            entity: The entity
            indent: Number of spaces to indent

        Returns:
            GraphQL fields string
        """
        indent_str = " " * indent
        fields = []

        for field_name in entity.fields.keys():
            fields.append(f"{indent_str}{field_name}")

        return "\n".join(fields)

    def _build_cache_update_logic(self, entity: Entity, action: Action) -> str:
        """
        Build cache update logic for Apollo Client.

        Args:
            entity: The entity
            action: The action

        Returns:
            Cache update configuration string
        """
        entity_name = entity.name
        action_name = action.name

        if action_name.startswith("create_"):
            # Add to list cache
            return f"""update: (cache, {{ data }}) => {{
        if (data?.{self._to_camel_case(action_name)}?.success && data.{self._to_camel_case(action_name)}.data?.{entity_name.lower()}) {{
          const newItem = data.{self._to_camel_case(action_name)}.data.{entity_name.lower()};

          // Update list queries
          cache.modify({{
            fields: {{
              {entity_name.lower()}s(existing = [], {{ readField }}) {{
                return [newItem, ...existing];
              }},
            }},
          }});
        }}
      }},"""
        elif action_name.startswith("update_"):
            # Update existing item in cache
            return f"""update: (cache, {{ data }}) => {{
        if (data?.{self._to_camel_case(action_name)}?.success && data.{self._to_camel_case(action_name)}.data?.{entity_name.lower()}) {{
          const updatedItem = data.{self._to_camel_case(action_name)}.data.{entity_name.lower()};

          // Update the specific item
          cache.modify({{
            id: cache.identify(updatedItem),
            fields: (existing) => ({{
              ...existing,
              ...updatedItem,
            }}),
          }});
        }}
      }},"""
        elif action_name.startswith("delete_"):
            # Remove from cache
            return f"""update: (cache, {{ data, variables }}) => {{
        if (data?.{self._to_camel_case(action_name)}?.success && variables?.input?.id) {{
          cache.evict({{ id: `UUID:${{variables.input.id}}` }});
          cache.gc();
        }}
      }},"""
        else:
            return ""

    def _build_optimistic_response(self, entity: Entity, action: Action) -> str:
        """
        Build optimistic response for better UX.

        Args:
            entity: The entity
            action: The action

        Returns:
            Optimistic response configuration string
        """
        action_name = action.name

        if action_name.startswith("delete_"):
            # For deletes, we can optimistically remove immediately
            return f"""optimisticResponse: (variables) => ({{
        {self._to_camel_case(action_name)}: {{
          success: true,
          data: {{
            success: true,
            message: '{entity.name} deleted successfully',
            __typename: '{self._to_pascal_case(action_name)}Success',
          }},
          error: null,
          code: null,
          __typename: 'MutationResult',
        }},
      }}),"""
        else:
            # For other operations, optimistic updates are more complex
            # We'll skip for now to avoid complexity
            return ""

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
