# Week 27: React Code Generation

**Date**: TBD (After Week 26 complete)
**Duration**: 5-6 days
**Status**: 📅 Planned
**Objective**: Generate production-ready React/TypeScript code from UniversalFrontend

**Prerequisites**: Week 26 complete (React parser implemented)

**Output**:
- React component generators (pages, forms, lists, detail views)
- TypeScript type generation
- React Router integration
- TanStack Query hooks
- Complete round-trip (parse → generate → working app)

---

## 🎯 Executive Summary

This week implements **code generation** for React applications - taking the UniversalFrontend grammar from Week 25 and generating production-ready React/TypeScript code.

**Key Deliverables**:
1. **Page Generators**: List, Form, Detail, Custom pages
2. **Component Library Integration**: Shadcn/ui, MUI, or custom
3. **Type Safety**: Full TypeScript types from entities
4. **Data Fetching**: TanStack Query hooks with GraphQL
5. **Routing**: React Router v6 configuration
6. **Form Handling**: React Hook Form with validation

**Code Leverage**: 50 lines of UniversalFrontend YAML → 2000+ lines of React/TypeScript

---

## 📅 Daily Breakdown

### Day 1: Generator Infrastructure

**Morning Block (4 hours): Core Generator Framework**

**File**: `src/frontend/generators/react_generator.py`

```python
"""
React Code Generator

Generates React/TypeScript components from UniversalFrontend.
"""

from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass

from src.frontend.universal_component_schema import (
    UniversalFrontend,
    Page,
    ListPage,
    FormPage,
    DetailPage,
    CustomPage,
    EntityFrontend,
    FieldFrontend
)


@dataclass
class GeneratedFile:
    """Generated React file"""
    path: Path
    content: str
    file_type: str  # 'component' | 'hook' | 'type' | 'route'


class ReactGenerator:
    """Generate React application from UniversalFrontend"""

    def __init__(self, output_dir: Path, component_library: str = 'shadcn'):
        self.output_dir = output_dir
        self.component_library = component_library
        self.page_generators = {
            'list': ListPageGenerator(component_library),
            'form': FormPageGenerator(component_library),
            'detail': DetailPageGenerator(component_library),
            'custom': CustomPageGenerator(component_library)
        }

    def generate(self, frontend: UniversalFrontend) -> List[GeneratedFile]:
        """Generate complete React application"""
        files = []

        # 1. Generate TypeScript types
        files.extend(self._generate_types(frontend))

        # 2. Generate GraphQL hooks
        files.extend(self._generate_hooks(frontend))

        # 3. Generate pages
        files.extend(self._generate_pages(frontend))

        # 4. Generate routing
        files.append(self._generate_router(frontend))

        # 5. Generate navigation
        files.append(self._generate_navigation(frontend))

        return files

    def _generate_types(self, frontend: UniversalFrontend) -> List[GeneratedFile]:
        """Generate TypeScript type definitions"""
        generator = TypeScriptTypeGenerator()
        return generator.generate(frontend.entities, frontend.fields)

    def _generate_hooks(self, frontend: UniversalFrontend) -> List[GeneratedFile]:
        """Generate TanStack Query hooks for GraphQL"""
        generator = QueryHookGenerator()
        return generator.generate(frontend.entities, frontend.actions)

    def _generate_pages(self, frontend: UniversalFrontend) -> List[GeneratedFile]:
        """Generate page components"""
        files = []

        for page in frontend.pages:
            generator = self.page_generators.get(page.type)
            if generator:
                files.append(generator.generate(page, frontend))

        return files

    def _generate_router(self, frontend: UniversalFrontend) -> GeneratedFile:
        """Generate React Router configuration"""
        generator = RouterGenerator()
        return generator.generate(frontend.pages)

    def _generate_navigation(self, frontend: UniversalFrontend) -> GeneratedFile:
        """Generate navigation component"""
        generator = NavigationGenerator(self.component_library)
        return generator.generate(frontend.navigation)


class TypeScriptTypeGenerator:
    """Generate TypeScript types from entities"""

    def generate(
        self,
        entities: Dict[str, EntityFrontend],
        fields: Dict[str, Dict[str, FieldFrontend]]
    ) -> List[GeneratedFile]:
        """Generate types.ts file"""

        type_definitions = []

        for entity_name, entity in entities.items():
            entity_fields = fields.get(entity_name, {})
            type_def = self._generate_entity_type(entity_name, entity_fields)
            type_definitions.append(type_def)

        content = self._format_types_file(type_definitions)

        return [GeneratedFile(
            path=Path('src/types/entities.ts'),
            content=content,
            file_type='type'
        )]

    def _generate_entity_type(
        self,
        entity_name: str,
        fields: Dict[str, FieldFrontend]
    ) -> str:
        """Generate TypeScript interface for entity"""

        field_lines = []
        for field_name, field_config in fields.items():
            ts_type = self._map_widget_to_ts_type(field_config.widget)
            required = '?' if not field_config.required else ''
            field_lines.append(f"  {field_name}{required}: {ts_type};")

        fields_str = '\n'.join(field_lines)

        return f"""
export interface {entity_name} {{
{fields_str}
}}

export type Create{entity_name}Input = Omit<{entity_name}, 'id' | 'createdAt' | 'updatedAt'>;
export type Update{entity_name}Input = Partial<Create{entity_name}Input>;
"""

    def _map_widget_to_ts_type(self, widget: Optional[str]) -> str:
        """Map widget type to TypeScript type"""
        mapping = {
            'text': 'string',
            'textarea': 'string',
            'email': 'string',
            'password': 'string',
            'number': 'number',
            'integer': 'number',
            'date': 'Date',
            'datetime': 'Date',
            'checkbox': 'boolean',
            'switch': 'boolean',
            'select': 'string',
            'multiselect': 'string[]',
            'tags': 'string[]',
            'json': 'Record<string, unknown>',
        }
        return mapping.get(widget, 'string')
```

**Afternoon Block (4 hours): List Page Generator**

```python
# src/frontend/generators/react_list_page_generator.py
"""Generate React list page components"""

from typing import Dict
from pathlib import Path

from src.frontend.universal_component_schema import ListPage, UniversalFrontend
from .react_generator import GeneratedFile


class ListPageGenerator:
    """Generate React list page"""

    def __init__(self, component_library: str):
        self.component_library = component_library

    def generate(self, page: ListPage, frontend: UniversalFrontend) -> GeneratedFile:
        """Generate list page component"""

        entity = frontend.entities.get(page.entity)
        fields = frontend.fields.get(page.entity, {})

        # Determine columns
        columns = page.list_config.columns if page.list_config else list(fields.keys())[:5]

        # Generate component code
        content = self._generate_component(page, entity, fields, columns)

        # Generate file path
        file_path = Path(f"src/pages/{page.entity}/{page.name}.tsx")

        return GeneratedFile(
            path=file_path,
            content=content,
            file_type='component'
        )

    def _generate_component(
        self,
        page: ListPage,
        entity: EntityFrontend,
        fields: Dict,
        columns: List[str]
    ) -> str:
        """Generate React component code"""

        # Component imports
        imports = self._generate_imports(columns, fields)

        # Column definitions
        column_defs = self._generate_column_definitions(columns, fields)

        # Filters
        filters = self._generate_filters(page) if page.list_config else ''

        # Actions
        actions = self._generate_actions(page) if page.list_config else ''

        component_name = page.name.replace('-', '_').title().replace('_', '')

        return f'''
{imports}

export function {component_name}() {{
  const {{ data, isLoading, error }} = use{page.entity}List();

  const columns = React.useMemo<ColumnDef<{page.entity}>[]>(
    () => [
{column_defs}
    ],
    []
  );

  const table = useReactTable({{
    data: data ?? [],
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
  }});

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {{error.message}}</div>;

  return (
    <div className="container mx-auto py-6">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">{page.title or entity.label}</h1>
{actions}
      </div>

{filters}

      <DataTable table={{table}} />

      <div className="flex items-center justify-between mt-4">
        <Button
          onClick={{() => table.previousPage()}}
          disabled={{!table.getCanPreviousPage()}}
        >
          Previous
        </Button>
        <span>
          Page {{table.getState().pagination.pageIndex + 1}} of {{table.getPageCount()}}
        </span>
        <Button
          onClick={{() => table.nextPage()}}
          disabled={{!table.getCanNextPage()}}
        >
          Next
        </Button>
      </div>
    </div>
  );
}}
'''

    def _generate_imports(self, columns: List[str], fields: Dict) -> str:
        """Generate import statements"""
        return '''
import React from 'react';
import { useReactTable, ColumnDef, getCoreRowModel, getPaginationRowModel, getSortedRowModel } from '@tanstack/react-table';
import { Button } from '@/components/ui/button';
import { DataTable } from '@/components/ui/data-table';
'''

    def _generate_column_definitions(self, columns: List[str], fields: Dict) -> str:
        """Generate TanStack Table column definitions"""
        column_lines = []

        for col in columns:
            field_config = fields.get(col)
            label = field_config.label if field_config else col.replace('_', ' ').title()

            column_lines.append(f'''      {{
        accessorKey: '{col}',
        header: '{label}',
      }},''')

        return '\n'.join(column_lines)

    def _generate_filters(self, page: ListPage) -> str:
        """Generate filter UI"""
        if not page.list_config or not page.list_config.filters:
            return ''

        return '''
      <div className="flex gap-2 mb-4">
        {/* TODO: Generate filters based on config */}
      </div>
'''

    def _generate_actions(self, page: ListPage) -> str:
        """Generate action buttons"""
        if not page.list_config or not page.list_config.primary_actions:
            return ''

        return '''
        <div className="flex gap-2">
          <Button onClick={() => navigate(`/${page.entity}/new`)}>
            Create New
          </Button>
        </div>
'''
```

---

### Day 2: Form Page Generator

**Morning**: Generate form pages with React Hook Form
**Afternoon**: Field widgets with validation

**Key Output**: Form components with:
- React Hook Form integration
- Field-level validation
- Error handling
- Submit handlers
- GraphQL mutations

---

### Day 3: Detail Page & Routing

**Morning**: Detail page generator
**Afternoon**: React Router v6 configuration

**Generated Router**:
```typescript
// src/routes/index.tsx
import { createBrowserRouter } from 'react-router-dom';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    children: [
      { path: 'contacts', element: <ContactListPage /> },
      { path: 'contacts/:id', element: <ContactDetailPage /> },
      { path: 'contacts/new', element: <ContactFormPage /> },
      { path: 'contacts/:id/edit', element: <ContactFormPage /> },
    ]
  }
]);
```

---

### Day 4: GraphQL Integration

**Morning**: Generate TanStack Query hooks
**Afternoon**: Mutation hooks with optimistic updates

**Generated Hook**:
```typescript
// src/hooks/useContacts.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { graphql } from '@/gql';

const ContactListQuery = graphql(`
  query ContactList {
    contacts {
      id
      email
      company { id name }
      status
    }
  }
`);

export function useContactList() {
  return useQuery({
    queryKey: ['contacts'],
    queryFn: async () => {
      const result = await request(ContactListQuery);
      return result.contacts;
    }
  });
}

export function useCreateContact() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (input: CreateContactInput) => {
      return request(CreateContactMutation, { input });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] });
    }
  });
}
```

---

### Day 5: Integration Testing & CLI

**Morning**: Round-trip testing (parse → generate → run)
**Afternoon**: CLI commands and documentation

**CLI Commands**:
```bash
# Generate React app from UniversalFrontend YAML
specql generate-react frontend.yaml --output src/ --library shadcn

# With Next.js support
specql generate-react frontend.yaml --framework next --output src/

# With custom component library
specql generate-react frontend.yaml --library mui --output src/
```

---

## ✅ Success Criteria

- [ ] List page generator working (TanStack Table)
- [ ] Form page generator with React Hook Form
- [ ] Detail page generator
- [ ] TypeScript types generated
- [ ] GraphQL hooks generated (TanStack Query)
- [ ] React Router configuration generated
- [ ] Navigation component generated
- [ ] Round-trip test passing (parse React → generate React)
- [ ] 100+ unit tests passing
- [ ] CLI commands functional
- [ ] Documentation complete

---

## 🧪 Testing Strategy

**Unit Tests**:
- Component generation for each page type
- TypeScript type generation
- Hook generation
- Router configuration

**Integration Tests**:
- Generate complete React app from YAML
- Run generated app (compile check)
- Visual regression tests
- Round-trip: parse existing React app → generate → compare

**Example Test**:
```python
def test_generate_list_page():
    frontend = UniversalFrontend(
        entities={'Contact': EntityFrontend(label='Contacts')},
        fields={'Contact': {
            'email': FieldFrontend(label='Email', widget=WidgetType.EMAIL),
            'name': FieldFrontend(label='Name', widget=WidgetType.TEXT)
        }},
        pages=[ListPage(
            name='contact-list',
            route='/contacts',
            type='list',
            entity='Contact',
            list_config=ListPageConfig(columns=['email', 'name'])
        )]
    )

    generator = ReactGenerator(output_dir=Path('output'))
    files = generator.generate(frontend)

    # Should generate list page component
    list_page = next(f for f in files if 'contact-list' in str(f.path))
    assert 'useReactTable' in list_page.content
    assert 'accessorKey: \'email\'' in list_page.content
```

---

## 🔗 Related Files

- **Previous**: [Week 26: React Parser Foundation](./WEEK_26.md)
- **Next**: [Week 28: Vue Parser & Generation](./WEEK_28.md)
- **Grammar**: [Week 25: Universal Component Grammar](./WEEK_25.md)

---

**Status**: 📅 Planned (builds on Week 26 parser)
**Complexity**: High (template generation + best practices)
**Risk**: Low (React ecosystem mature, patterns established)
