# Week 26: React Parser Foundation

**Date**: TBD (After Week 25 complete)
**Duration**: 5-6 days
**Status**: 📅 Planned
**Objective**: Parse existing React/TypeScript components into UniversalFrontend AST

**Prerequisites**: Week 25 complete (Universal Component Grammar implemented)

**Output**:
- React AST parser using Babel
- Component pattern recognition
- Props/state extraction
- Routing extraction (React Router)
- Foundation for React code generation (Week 27)

---

## 🎯 Executive Summary

This week implements **reverse engineering** for React applications - parsing existing React/TypeScript code into the UniversalFrontend grammar defined in Week 25.

**Key Insight**: Just like we reverse-engineered Python/SQLAlchemy, Java/JPA, etc., we now reverse-engineer React components to extract:
- Component structure (pages, forms, lists, detail views)
- Field configurations (widgets, validation)
- Actions and their side effects
- Navigation structure

**Why React First**:
- Most popular web framework (40%+ market share)
- Rich ecosystem (React Router, React Hook Form, TanStack Table)
- TypeScript support for better static analysis
- Reference implementation for Vue/Angular parsers

---

## 📅 Daily Breakdown

### Day 1: Babel AST Parser Setup

**Morning Block (4 hours): Parser Infrastructure**

**File**: `src/frontend/parsers/react_parser.py`

```python
"""
React/TypeScript Component Parser

Parses React components using Babel AST into UniversalFrontend.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

from src.frontend.universal_component_schema import (
    UniversalFrontend,
    EntityFrontend,
    FieldFrontend,
    Page,
    Action,
    Layout,
    NavItem
)


@dataclass
class BabelNode:
    """Wrapper for Babel AST node"""
    type: str
    data: Dict

    @classmethod
    def from_dict(cls, data: Dict) -> 'BabelNode':
        return cls(type=data.get('type', ''), data=data)


class ReactASTParser:
    """Parse React components using Babel"""

    def __init__(self):
        self.babel_parser_script = self._get_babel_script()

    def parse_file(self, file_path: Path) -> Dict:
        """Parse React/TypeScript file to Babel AST"""
        # Call Node.js script to parse with Babel
        result = subprocess.run(
            ['node', str(self.babel_parser_script), str(file_path)],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise ValueError(f"Babel parsing failed: {result.stderr}")

        return json.loads(result.stdout)

    def _get_babel_script(self) -> Path:
        """Get path to Babel parsing script"""
        # Script that uses @babel/parser
        return Path(__file__).parent / 'babel_parser.js'


class ReactComponentExtractor:
    """Extract component information from Babel AST"""

    def __init__(self):
        self.ast_parser = ReactASTParser()

    def extract_component(self, file_path: Path) -> Optional[Dict]:
        """Extract component metadata from React file"""
        ast = self.ast_parser.parse_file(file_path)

        # Find component declaration
        component_node = self._find_component_declaration(ast)
        if not component_node:
            return None

        return {
            'name': self._extract_component_name(component_node),
            'props': self._extract_props(component_node),
            'state': self._extract_state(component_node),
            'hooks': self._extract_hooks(component_node),
            'jsx': self._extract_jsx_structure(component_node)
        }

    def _find_component_declaration(self, ast: Dict) -> Optional[BabelNode]:
        """Find main component declaration in AST"""
        # Look for function component or class component
        for node in self._walk_ast(ast):
            if self._is_component_node(node):
                return BabelNode.from_dict(node)
        return None

    def _is_component_node(self, node: Dict) -> bool:
        """Check if node is a React component"""
        node_type = node.get('type')

        # Function component
        if node_type in ['FunctionDeclaration', 'ArrowFunctionExpression']:
            # Check if returns JSX
            return self._returns_jsx(node)

        # Class component
        if node_type == 'ClassDeclaration':
            # Check if extends React.Component
            return self._extends_react_component(node)

        return False

    def _returns_jsx(self, node: Dict) -> bool:
        """Check if function returns JSX"""
        # Look for JSXElement in return statement
        for child in self._walk_ast(node):
            if child.get('type') == 'JSXElement':
                return True
        return False

    def _walk_ast(self, node: Dict) -> List[Dict]:
        """Walk AST depth-first"""
        nodes = [node]

        for key, value in node.items():
            if isinstance(value, dict):
                nodes.extend(self._walk_ast(value))
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        nodes.extend(self._walk_ast(item))

        return nodes
```

**Afternoon Block (4 hours): Babel Integration Script**

**File**: `src/frontend/parsers/babel_parser.js`

```javascript
#!/usr/bin/env node

/**
 * Babel Parser for React Components
 *
 * Usage: node babel_parser.js <file_path>
 * Output: JSON AST to stdout
 */

const fs = require('fs');
const parser = require('@babel/parser');

const filePath = process.argv[2];

if (!filePath) {
  console.error('Usage: node babel_parser.js <file_path>');
  process.exit(1);
}

try {
  const code = fs.readFileSync(filePath, 'utf-8');

  const ast = parser.parse(code, {
    sourceType: 'module',
    plugins: [
      'jsx',
      'typescript',
      'decorators-legacy',
      'classProperties',
      'objectRestSpread'
    ]
  });

  console.log(JSON.stringify(ast, null, 2));
} catch (error) {
  console.error('Parse error:', error.message);
  process.exit(1);
}
```

---

### Day 2: Component Pattern Recognition

**Morning Block (4 hours): Page Type Detection**

Implement pattern recognition for different page types:

```python
# src/frontend/parsers/react_patterns.py
"""React component pattern recognition"""

from typing import Optional, Literal
from dataclasses import dataclass

from src.frontend.universal_component_schema import PageType


@dataclass
class ComponentPattern:
    """Detected component pattern"""
    page_type: PageType
    confidence: float  # 0.0 to 1.0
    indicators: List[str]


class ReactPatternDetector:
    """Detect page types from React components"""

    def detect_page_type(self, component_data: Dict) -> Optional[ComponentPattern]:
        """Detect what type of page this component represents"""

        # Check for list page patterns
        if self._is_list_page(component_data):
            return ComponentPattern(
                page_type=PageType.LIST,
                confidence=self._calculate_confidence(component_data, 'list'),
                indicators=self._get_list_indicators(component_data)
            )

        # Check for form page patterns
        if self._is_form_page(component_data):
            return ComponentPattern(
                page_type=PageType.FORM,
                confidence=self._calculate_confidence(component_data, 'form'),
                indicators=self._get_form_indicators(component_data)
            )

        # Check for detail page patterns
        if self._is_detail_page(component_data):
            return ComponentPattern(
                page_type=PageType.DETAIL,
                confidence=self._calculate_confidence(component_data, 'detail'),
                indicators=self._get_detail_indicators(component_data)
            )

        # Default to custom page
        return ComponentPattern(
            page_type=PageType.CUSTOM,
            confidence=1.0,
            indicators=['no_standard_pattern']
        )

    def _is_list_page(self, component_data: Dict) -> bool:
        """Check if component is a list page"""
        indicators = 0

        # Check for table libraries
        jsx = component_data.get('jsx', {})
        if self._uses_library(jsx, ['TanStackTable', 'DataGrid', 'Table']):
            indicators += 2

        # Check for pagination
        if self._has_pagination(jsx):
            indicators += 1

        # Check for filters
        if self._has_filters(jsx):
            indicators += 1

        # Check for sorting
        hooks = component_data.get('hooks', [])
        if any(h.get('name') in ['useSortBy', 'useTable'] for h in hooks):
            indicators += 1

        return indicators >= 2

    def _is_form_page(self, component_data: Dict) -> bool:
        """Check if component is a form page"""
        indicators = 0

        # Check for form libraries
        hooks = component_data.get('hooks', [])
        if any(h.get('name') in ['useForm', 'useFormik'] for h in hooks):
            indicators += 2

        # Check for form elements
        jsx = component_data.get('jsx', {})
        if self._has_form_elements(jsx):
            indicators += 1

        # Check for validation
        if self._has_validation(component_data):
            indicators += 1

        # Check for submit handler
        if self._has_submit_handler(component_data):
            indicators += 1

        return indicators >= 2

    def _is_detail_page(self, component_data: Dict) -> bool:
        """Check if component is a detail page"""
        indicators = 0

        # Check for single entity fetch
        hooks = component_data.get('hooks', [])
        if any(h.get('name') in ['useQuery', 'useSWR'] for h in hooks):
            # Check if fetching single entity (has :id param)
            if self._fetches_single_entity(hooks):
                indicators += 2

        # Check for read-only fields
        jsx = component_data.get('jsx', {})
        if self._has_readonly_fields(jsx):
            indicators += 1

        # Check for action buttons
        if self._has_action_buttons(jsx):
            indicators += 1

        return indicators >= 2
```

**Afternoon Block (4 hours): Field Extraction**

Extract field configurations from form components.

---

### Day 3: Props & State Analysis

**Morning**: Extract props interfaces (TypeScript types)
**Afternoon**: Extract state management (useState, useReducer)

---

### Day 4: Routing & Navigation

**Morning**: Extract React Router routes
**Afternoon**: Build navigation tree from routing config

---

### Day 5: Integration & Testing

**Morning**: CLI command for React parsing
**Afternoon**: Integration tests with real React projects

**CLI Command**:
```bash
specql parse-react src/components --output frontend.yaml
```

---

## ✅ Success Criteria

- [ ] Babel AST parser working for React/TypeScript
- [ ] Component pattern detection (list/form/detail/custom)
- [ ] Props and state extraction
- [ ] Field configuration extraction
- [ ] Routing extraction (React Router)
- [ ] 100+ unit tests passing
- [ ] Integration tests with real React apps
- [ ] CLI command functional
- [ ] Documentation complete

---

## 🧪 Testing Strategy

**Unit Tests**:
- Babel parsing for various component styles
- Pattern detection accuracy
- Props/state extraction
- Field configuration mapping

**Integration Tests**:
- Parse real React applications
- Verify UniversalFrontend output
- Round-trip test (parse → generate → compare)

**Test Data**:
```typescript
// tests/fixtures/react/SimpleListPage.tsx
import { useTable } from '@tanstack/react-table';

interface User {
  id: string;
  email: string;
  name: string;
}

export function UserListPage() {
  const { data, isLoading } = useQuery<User[]>('/api/users');

  const table = useTable({
    data: data ?? [],
    columns: [
      { accessorKey: 'email', header: 'Email' },
      { accessorKey: 'name', header: 'Name' }
    ]
  });

  return (
    <div>
      <h1>Users</h1>
      <Table {...table} />
    </div>
  );
}
```

Expected output: `ListPage` with columns=[email, name]

---

## 🔗 Related Files

- **Previous**: [Week 25: Universal Component Grammar](./WEEK_25.md)
- **Next**: [Week 27: React Code Generation](./WEEK_27.md)
- **Reference Pattern**: `done/WEEK_7_8_PYTHON_REVERSE_ENGINEERING.md` (similar approach)

---

**Status**: 📅 Planned (builds on Week 25 grammar)
**Complexity**: High (AST parsing + pattern recognition)
**Risk**: Medium (Babel ecosystem well-established)
