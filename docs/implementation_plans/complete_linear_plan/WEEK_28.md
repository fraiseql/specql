# Week 28: Vue Parser & Code Generation

**Date**: TBD (After Week 27 complete)
**Duration**: 5-6 days
**Status**: 📅 Planned
**Objective**: Parse existing Vue 3/TypeScript components and generate Vue code from UniversalFrontend

**Prerequisites**: Week 27 complete (React generation working)

**Output**:
- Vue 3 Composition API parser
- Vue component generators (pages, forms, lists, detail views)
- Vue Router integration
- Pinia state management
- VueQuery (TanStack Query for Vue)

---

## 🎯 Executive Summary

This week extends SpecQL's frontend support to **Vue 3** - the second most popular web framework. We'll implement both parsing (reverse engineering) and code generation, following the same patterns established for React in Weeks 26-27.

**Why Vue**:
- 18%+ market share (second after React)
- Strong in enterprise (especially Asia/Europe)
- Composition API similar to React Hooks
- Excellent TypeScript support in Vue 3
- Reference implementation for Angular parser (Week 29)

**Key Differences from React**:
- Single File Components (.vue files)
- Template syntax (HTML-like) vs JSX
- `<script setup>` vs function components
- `ref` / `reactive` vs `useState`
- Vue Router vs React Router
- Pinia vs Redux/Zustand

---

## 📅 Daily Breakdown

### Day 1: Vue Parser Infrastructure

**Morning Block (4 hours): Vue SFC Parser**

**File**: `src/frontend/parsers/vue_parser.py`

```python
"""
Vue 3 Component Parser

Parses Vue 3 Single File Components (.vue) into UniversalFrontend.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

from src.frontend.universal_component_schema import UniversalFrontend


@dataclass
class VueSFCParts:
    """Parts of a Vue Single File Component"""
    template: Optional[str] = None
    script: Optional[str] = None
    script_setup: Optional[str] = None  # <script setup>
    style: Optional[str] = None
    script_ast: Optional[Dict] = None


class VueSFCParser:
    """Parse Vue Single File Components"""

    def __init__(self):
        self.sfc_parser_script = self._get_sfc_parser_script()

    def parse_file(self, file_path: Path) -> VueSFCParts:
        """Parse .vue file into parts"""
        # Call Node.js script using @vue/compiler-sfc
        result = subprocess.run(
            ['node', str(self.sfc_parser_script), str(file_path)],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise ValueError(f"Vue SFC parsing failed: {result.stderr}")

        data = json.loads(result.stdout)

        return VueSFCParts(
            template=data.get('template'),
            script=data.get('script'),
            script_setup=data.get('scriptSetup'),
            style=data.get('style'),
            script_ast=data.get('scriptAst')
        )

    def _get_sfc_parser_script(self) -> Path:
        """Get path to Vue SFC parsing script"""
        return Path(__file__).parent / 'vue_sfc_parser.js'


class VueComponentExtractor:
    """Extract component information from Vue SFC"""

    def __init__(self):
        self.sfc_parser = VueSFCParser()

    def extract_component(self, file_path: Path) -> Optional[Dict]:
        """Extract component metadata from Vue file"""
        sfc = self.sfc_parser.parse_file(file_path)

        # Extract from <script setup> or regular <script>
        script_data = self._extract_script_data(sfc)

        # Extract from <template>
        template_data = self._extract_template_data(sfc.template)

        return {
            'name': self._extract_component_name(file_path),
            'props': script_data.get('props', []),
            'refs': script_data.get('refs', []),
            'composables': script_data.get('composables', []),
            'template_structure': template_data
        }

    def _extract_script_data(self, sfc: VueSFCParts) -> Dict:
        """Extract data from <script setup> or <script>"""
        if sfc.script_setup:
            return self._extract_from_script_setup(sfc.script_setup, sfc.script_ast)
        elif sfc.script:
            return self._extract_from_script(sfc.script, sfc.script_ast)
        return {}

    def _extract_from_script_setup(self, script: str, ast: Dict) -> Dict:
        """Extract from Composition API <script setup>"""
        return {
            'props': self._find_defineProps(ast),
            'refs': self._find_refs(ast),
            'composables': self._find_composables(ast),
            'computed': self._find_computed(ast)
        }

    def _find_defineProps(self, ast: Dict) -> List[Dict]:
        """Find defineProps() call"""
        # Look for defineProps<{ ... }>() or defineProps({ ... })
        for node in self._walk_ast(ast):
            if (node.get('type') == 'CallExpression' and
                node.get('callee', {}).get('name') == 'defineProps'):
                return self._extract_props_from_node(node)
        return []

    def _find_refs(self, ast: Dict) -> List[Dict]:
        """Find ref() calls"""
        refs = []
        for node in self._walk_ast(ast):
            if (node.get('type') == 'CallExpression' and
                node.get('callee', {}).get('name') == 'ref'):
                refs.append(self._extract_ref_info(node))
        return refs

    def _find_composables(self, ast: Dict) -> List[str]:
        """Find composable usage (useQuery, useRouter, etc.)"""
        composables = []
        for node in self._walk_ast(ast):
            if (node.get('type') == 'CallExpression' and
                isinstance(node.get('callee', {}).get('name'), str) and
                node['callee']['name'].startswith('use')):
                composables.append(node['callee']['name'])
        return list(set(composables))

    def _extract_template_data(self, template: Optional[str]) -> Dict:
        """Extract structure from <template>"""
        if not template:
            return {}

        # Parse template to find:
        # - v-for (list rendering)
        # - v-model (form fields)
        # - component usage
        return {
            'has_list': 'v-for' in template,
            'has_form': 'v-model' in template or '<form' in template,
            'components': self._find_used_components(template)
        }

    def _find_used_components(self, template: str) -> List[str]:
        """Find components used in template"""
        import re
        # Match PascalCase component tags
        pattern = r'<([A-Z][a-zA-Z0-9]*)'
        return list(set(re.findall(pattern, template)))
```

**Afternoon Block (4 hours): Vue SFC Parser Script**

**File**: `src/frontend/parsers/vue_sfc_parser.js`

```javascript
#!/usr/bin/env node

/**
 * Vue SFC Parser
 *
 * Uses @vue/compiler-sfc to parse .vue files
 */

const fs = require('fs');
const { parse } = require('@vue/compiler-sfc');
const babelParser = require('@babel/parser');

const filePath = process.argv[2];

if (!filePath) {
  console.error('Usage: node vue_sfc_parser.js <file_path>');
  process.exit(1);
}

try {
  const source = fs.readFileSync(filePath, 'utf-8');
  const { descriptor } = parse(source, { filename: filePath });

  const result = {
    template: descriptor.template?.content,
    script: descriptor.script?.content,
    scriptSetup: descriptor.scriptSetup?.content,
    style: descriptor.styles?.[0]?.content,
  };

  // Parse <script setup> with Babel for AST
  if (descriptor.scriptSetup) {
    const scriptAst = babelParser.parse(descriptor.scriptSetup.content, {
      sourceType: 'module',
      plugins: ['typescript']
    });
    result.scriptAst = scriptAst;
  }

  console.log(JSON.stringify(result, null, 2));
} catch (error) {
  console.error('Parse error:', error.message);
  process.exit(1);
}
```

---

### Day 2: Vue Pattern Recognition

**Morning**: Detect page types from Vue components
**Afternoon**: Extract field configurations from forms

**Pattern Detection**:
- **List pages**: v-for, pagination components, table components
- **Form pages**: v-model, validation, submit handlers
- **Detail pages**: Single entity display, action buttons

---

### Day 3: Vue Code Generation

**Morning Block (4 hours): List Page Generator**

```python
# src/frontend/generators/vue_list_page_generator.py
"""Generate Vue 3 list page components"""

from pathlib import Path
from typing import Dict, List

from src.frontend.universal_component_schema import ListPage, UniversalFrontend
from .react_generator import GeneratedFile


class VueListPageGenerator:
    """Generate Vue 3 list page"""

    def __init__(self, component_library: str = 'element-plus'):
        self.component_library = component_library

    def generate(self, page: ListPage, frontend: UniversalFrontend) -> GeneratedFile:
        """Generate Vue list page component"""

        entity = frontend.entities.get(page.entity)
        fields = frontend.fields.get(page.entity, {})
        columns = page.list_config.columns if page.list_config else list(fields.keys())[:5]

        content = self._generate_sfc(page, entity, fields, columns)
        file_path = Path(f"src/pages/{page.entity}/{page.name}.vue")

        return GeneratedFile(path=file_path, content=content, file_type='component')

    def _generate_sfc(
        self,
        page: ListPage,
        entity,
        fields: Dict,
        columns: List[str]
    ) -> str:
        """Generate Vue Single File Component"""

        script_setup = self._generate_script_setup(page, entity, columns)
        template = self._generate_template(page, entity, fields, columns)
        style = self._generate_style()

        return f'''<script setup lang="ts">
{script_setup}
</script>

<template>
{template}
</template>

<style scoped>
{style}
</style>
'''

    def _generate_script_setup(self, page: ListPage, entity, columns: List[str]) -> str:
        """Generate <script setup> content"""

        component_name = page.name.replace('-', '_')

        return f'''
import {{ ref, computed }} from 'vue';
import {{ useQuery }} from '@tanstack/vue-query';
import {{ use{page.entity}List }} from '@/composables/use{page.entity}';

const {{ data, isLoading, error }} = use{page.entity}List();

const currentPage = ref(1);
const pageSize = ref(20);

const paginatedData = computed(() => {{
  const start = (currentPage.value - 1) * pageSize.value;
  const end = start + pageSize.value;
  return data.value?.slice(start, end) ?? [];
}});

const totalPages = computed(() =>
  Math.ceil((data.value?.length ?? 0) / pageSize.value)
);
'''

    def _generate_template(
        self,
        page: ListPage,
        entity,
        fields: Dict,
        columns: List[str]
    ) -> str:
        """Generate <template> content"""

        # Table columns
        column_els = []
        for col in columns:
            field_config = fields.get(col)
            label = field_config.label if field_config else col.replace('_', ' ').title()
            column_els.append(f'      <el-table-column prop="{col}" label="{label}" />')

        columns_html = '\n'.join(column_els)

        return f'''
  <div class="list-page">
    <div class="header">
      <h1>{page.title or entity.label}</h1>
      <el-button type="primary" @click="createNew">Create New</el-button>
    </div>

    <el-table v-if="!isLoading" :data="paginatedData" stripe>
{columns_html}
      <el-table-column label="Actions">
        <template #default="{{ row }}">
          <el-button size="small" @click="viewDetails(row.id)">View</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="currentPage"
      :page-size="pageSize"
      :total="data?.length ?? 0"
      layout="prev, pager, next"
    />
  </div>
'''

    def _generate_style(self) -> str:
        """Generate <style> content"""
        return '''
.list-page {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
'''
```

**Afternoon**: Form and detail page generators

---

### Day 4: Vue Router & State Management

**Morning**: Generate Vue Router v4 configuration
**Afternoon**: Generate Pinia stores for state management

**Generated Router**:
```typescript
// src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router';

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/contacts',
      name: 'contact-list',
      component: () => import('@/pages/contacts/ContactList.vue')
    },
    {
      path: '/contacts/:id',
      name: 'contact-detail',
      component: () => import('@/pages/contacts/ContactDetail.vue')
    },
    {
      path: '/contacts/new',
      name: 'contact-create',
      component: () => import('@/pages/contacts/ContactForm.vue')
    }
  ]
});
```

---

### Day 5: Integration Testing & CLI

**Morning**: Round-trip testing (parse Vue → generate Vue)
**Afternoon**: CLI integration and documentation

**CLI Command**:
```bash
# Parse existing Vue app
specql parse-vue src/pages --output frontend.yaml

# Generate Vue app from UniversalFrontend
specql generate-vue frontend.yaml --output src/ --library element-plus

# With Nuxt 3 support
specql generate-vue frontend.yaml --framework nuxt --output src/
```

---

## ✅ Success Criteria

- [ ] Vue SFC parser working (@vue/compiler-sfc)
- [ ] Pattern detection for Vue components
- [ ] List page generator (Element Plus / Vuetify)
- [ ] Form page generator (v-model, validation)
- [ ] Detail page generator
- [ ] TypeScript types generated
- [ ] VueQuery composables generated
- [ ] Vue Router configuration generated
- [ ] Pinia stores generated
- [ ] Round-trip test passing (parse Vue → generate Vue)
- [ ] 100+ unit tests passing
- [ ] CLI commands functional
- [ ] Documentation complete

---

## 🧪 Testing Strategy

**Unit Tests**:
- Vue SFC parsing
- Component generation for each page type
- Composable generation
- Router configuration

**Integration Tests**:
- Generate complete Vue 3 app from YAML
- Run generated app (compile check with Vite)
- Round-trip: parse Vue app → generate → compare

---

## 🔗 Related Files

- **Previous**: [Week 27: React Code Generation](./WEEK_27.md)
- **Next**: [Week 29: Angular Parser & Generation](./WEEK_29.md)
- **Grammar**: [Week 25: Universal Component Grammar](./WEEK_25.md)

---

**Status**: 📅 Planned (follows React pattern from Weeks 26-27)
**Complexity**: Medium (similar to React with SFC differences)
**Risk**: Low (Vue 3 ecosystem mature, Composition API well-documented)
