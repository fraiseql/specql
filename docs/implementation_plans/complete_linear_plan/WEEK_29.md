# Week 29: Angular Parser & Code Generation

**Date**: TBD (After Week 28 complete)
**Duration**: 5-6 days
**Status**: 📅 Planned
**Objective**: Parse existing Angular/TypeScript components and generate Angular code from UniversalFrontend

**Prerequisites**: Week 28 complete (Vue generation working)

**Output**:
- Angular component parser (TypeScript decorators)
- Angular component generators (pages, forms, lists, detail views)
- Angular Router integration
- RxJS patterns for data fetching
- NgRx for state management (optional)

---

## 🎯 Executive Summary

This week extends SpecQL's frontend support to **Angular** - the enterprise web framework. We'll implement both parsing (reverse engineering) and code generation, completing support for the three major web frameworks.

**Why Angular**:
- 12%+ market share (strong in enterprise)
- Dominant in finance, healthcare, government
- Full framework (batteries included)
- TypeScript-first (best static analysis)
- Complete ecosystem (routing, forms, HTTP, state)

**Key Differences from React/Vue**:
- Class-based components with decorators
- Templates (HTML with directives)
- Dependency injection system
- RxJS observables (vs promises)
- Modules (NgModule) - being phased out for standalone
- Signals (new in Angular 16+)

**Framework Coverage After This Week**: React + Vue + Angular = 70%+ of web development market

---

## 📅 Daily Breakdown

### Day 1: Angular Component Parser

**Morning Block (4 hours): TypeScript Decorator Parser**

**File**: `src/frontend/parsers/angular_parser.py`

```python
"""
Angular Component Parser

Parses Angular/TypeScript components into UniversalFrontend.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

from src.frontend.universal_component_schema import UniversalFrontend


@dataclass
class AngularComponent:
    """Angular component metadata"""
    selector: str
    template: Optional[str] = None
    template_url: Optional[str] = None
    styles: List[str] = None
    class_name: str = ''
    inputs: List[Dict] = None
    outputs: List[Dict] = None
    providers: List[str] = None
    standalone: bool = False


class AngularComponentParser:
    """Parse Angular components"""

    def __init__(self):
        self.ts_parser_script = self._get_ts_parser_script()

    def parse_file(self, file_path: Path) -> Optional[AngularComponent]:
        """Parse Angular component file"""
        # Use TypeScript compiler API
        result = subprocess.run(
            ['node', str(self.ts_parser_script), str(file_path)],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise ValueError(f"Angular parsing failed: {result.stderr}")

        data = json.loads(result.stdout)
        if not data:
            return None

        return AngularComponent(
            selector=data.get('selector', ''),
            template=data.get('template'),
            template_url=data.get('templateUrl'),
            styles=data.get('styles', []),
            class_name=data.get('className', ''),
            inputs=data.get('inputs', []),
            outputs=data.get('outputs', []),
            providers=data.get('providers', []),
            standalone=data.get('standalone', False)
        )

    def _get_ts_parser_script(self) -> Path:
        return Path(__file__).parent / 'angular_parser.js'


class AngularComponentExtractor:
    """Extract component information from Angular files"""

    def __init__(self):
        self.parser = AngularComponentParser()

    def extract_component(self, file_path: Path) -> Optional[Dict]:
        """Extract component metadata"""
        component = self.parser.parse_file(file_path)
        if not component:
            return None

        # Load template if templateUrl
        template_content = component.template
        if component.template_url and not template_content:
            template_path = file_path.parent / component.template_url
            if template_path.exists():
                template_content = template_path.read_text()

        return {
            'name': component.class_name,
            'selector': component.selector,
            'inputs': component.inputs,
            'outputs': component.outputs,
            'template_structure': self._analyze_template(template_content),
            'services': self._extract_services(file_path),
            'standalone': component.standalone
        }

    def _analyze_template(self, template: Optional[str]) -> Dict:
        """Analyze Angular template"""
        if not template:
            return {}

        return {
            'has_list': '*ngFor' in template,
            'has_form': 'formGroup' in template or 'ngModel' in template,
            'has_table': 'mat-table' in template or '<table' in template,
            'directives': self._find_directives(template),
            'components': self._find_component_usage(template)
        }

    def _find_directives(self, template: str) -> List[str]:
        """Find Angular directives used"""
        import re
        # Match *ngFor, *ngIf, [formGroup], etc.
        directives = []

        # Structural directives
        directives.extend(re.findall(r'\*(\w+)', template))

        # Attribute directives
        directives.extend(re.findall(r'\[(\w+)\]', template))

        return list(set(directives))

    def _extract_services(self, file_path: Path) -> List[str]:
        """Extract injected services from constructor"""
        content = file_path.read_text()

        import re
        # Match: constructor(private myService: MyService)
        pattern = r'constructor\s*\((.*?)\)'
        match = re.search(pattern, content, re.DOTALL)

        if not match:
            return []

        constructor_params = match.group(1)

        # Extract service types
        service_pattern = r'(?:private|public|protected)?\s+(\w+):\s+(\w+)'
        services = re.findall(service_pattern, constructor_params)

        return [service_type for _, service_type in services]
```

**Afternoon Block (4 hours): Angular Parser Script**

**File**: `src/frontend/parsers/angular_parser.js`

```javascript
#!/usr/bin/env node

/**
 * Angular Component Parser
 *
 * Uses TypeScript compiler API to parse Angular components
 */

const fs = require('fs');
const ts = require('typescript');

const filePath = process.argv[2];

if (!filePath) {
  console.error('Usage: node angular_parser.js <file_path>');
  process.exit(1);
}

try {
  const source = fs.readFileSync(filePath, 'utf-8');
  const sourceFile = ts.createSourceFile(
    filePath,
    source,
    ts.ScriptTarget.Latest,
    true
  );

  let componentMetadata = null;

  function visit(node) {
    // Find @Component decorator
    if (ts.isDecorator(node)) {
      const expression = node.expression;
      if (ts.isCallExpression(expression) &&
          expression.expression.getText(sourceFile) === 'Component') {

        const arg = expression.arguments[0];
        if (ts.isObjectLiteralExpression(arg)) {
          componentMetadata = extractComponentMetadata(arg);
        }
      }
    }

    // Find class declaration
    if (ts.isClassDeclaration(node) && componentMetadata) {
      componentMetadata.className = node.name?.getText(sourceFile);

      // Extract inputs/outputs
      node.members.forEach(member => {
        if (ts.isPropertyDeclaration(member)) {
          const decorators = ts.getDecorators(member);
          decorators?.forEach(decorator => {
            const text = decorator.expression.getText(sourceFile);
            if (text.startsWith('Input')) {
              componentMetadata.inputs = componentMetadata.inputs || [];
              componentMetadata.inputs.push({
                name: member.name.getText(sourceFile),
                type: member.type?.getText(sourceFile)
              });
            } else if (text.startsWith('Output')) {
              componentMetadata.outputs = componentMetadata.outputs || [];
              componentMetadata.outputs.push({
                name: member.name.getText(sourceFile),
                type: member.type?.getText(sourceFile)
              });
            }
          });
        }
      });
    }

    ts.forEachChild(node, visit);
  }

  function extractComponentMetadata(node) {
    const metadata = {};

    node.properties.forEach(prop => {
      if (ts.isPropertyAssignment(prop)) {
        const name = prop.name.getText(sourceFile);
        const value = prop.initializer;

        if (ts.isStringLiteral(value)) {
          metadata[name] = value.text;
        } else if (ts.isArrayLiteralExpression(value)) {
          metadata[name] = value.elements.map(e => e.getText(sourceFile));
        } else if (name === 'standalone') {
          metadata[name] = value.kind === ts.SyntaxKind.TrueKeyword;
        }
      }
    });

    return metadata;
  }

  visit(sourceFile);

  console.log(JSON.stringify(componentMetadata, null, 2));
} catch (error) {
  console.error('Parse error:', error.message);
  process.exit(1);
}
```

---

### Day 2: Angular Pattern Recognition

**Morning**: Detect page types from Angular components
**Afternoon**: Extract form configurations (Reactive Forms)

**Pattern Detection**:
- **List pages**: *ngFor, mat-table, pagination
- **Form pages**: formGroup, formControl, validators
- **Detail pages**: Single entity display, read-only

---

### Day 3: Angular Code Generation

**Morning Block (4 hours): Component Generators**

```python
# src/frontend/generators/angular_list_page_generator.py
"""Generate Angular list page components"""

from pathlib import Path
from typing import Dict, List

from src.frontend.universal_component_schema import ListPage, UniversalFrontend
from .react_generator import GeneratedFile


class AngularListPageGenerator:
    """Generate Angular list page"""

    def __init__(self, component_library: str = 'material'):
        self.component_library = component_library

    def generate(self, page: ListPage, frontend: UniversalFrontend) -> List[GeneratedFile]:
        """Generate Angular component files"""

        entity = frontend.entities.get(page.entity)
        fields = frontend.fields.get(page.entity, {})
        columns = page.list_config.columns if page.list_config else list(fields.keys())[:5]

        component_name = self._to_component_name(page.name)

        return [
            self._generate_component_ts(component_name, page, entity, fields, columns),
            self._generate_component_html(component_name, page, entity, fields, columns),
            self._generate_component_css(component_name)
        ]

    def _generate_component_ts(
        self,
        component_name: str,
        page: ListPage,
        entity,
        fields: Dict,
        columns: List[str]
    ) -> GeneratedFile:
        """Generate .component.ts file"""

        class_name = self._to_class_name(component_name)
        selector = self._to_selector(component_name)

        content = f'''
import {{ Component, OnInit }} from '@angular/core';
import {{ CommonModule }} from '@angular/common';
import {{ MatTableModule }} from '@angular/material/table';
import {{ MatPaginatorModule }} from '@angular/material/paginator';
import {{ MatButtonModule }} from '@angular/material/button';
import {{ Observable }} from 'rxjs';

import {{ {page.entity} }} from '@/models/{page.entity.lower()}';
import {{ {page.entity}Service }} from '@/services/{page.entity.lower()}.service';

@Component({{
  selector: '{selector}',
  standalone: true,
  imports: [
    CommonModule,
    MatTableModule,
    MatPaginatorModule,
    MatButtonModule
  ],
  templateUrl: './{component_name}.component.html',
  styleUrls: ['./{component_name}.component.css']
}})
export class {class_name}Component implements OnInit {{
  displayedColumns: string[] = {columns};
  dataSource$: Observable<{page.entity}[]>;

  constructor(private {page.entity.lower()}Service: {page.entity}Service) {{}}

  ngOnInit(): void {{
    this.dataSource$ = this.{page.entity.lower()}Service.getAll();
  }}

  viewDetails(id: string): void {{
    // Navigate to detail page
  }}

  createNew(): void {{
    // Navigate to create page
  }}
}}
'''

        return GeneratedFile(
            path=Path(f"src/app/pages/{page.entity.lower()}/{component_name}.component.ts"),
            content=content,
            file_type='component'
        )

    def _generate_component_html(
        self,
        component_name: str,
        page: ListPage,
        entity,
        fields: Dict,
        columns: List[str]
    ) -> GeneratedFile:
        """Generate .component.html file"""

        # Generate mat-table columns
        column_defs = []
        for col in columns:
            field_config = fields.get(col)
            label = field_config.label if field_config else col.replace('_', ' ').title()

            column_defs.append(f'''
    <ng-container matColumnDef="{col}">
      <th mat-header-cell *matHeaderCellDef>{label}</th>
      <td mat-cell *matCellDef="let element">{{{{ element.{col} }}}}</td>
    </ng-container>
''')

        columns_html = ''.join(column_defs)

        content = f'''
<div class="list-page">
  <div class="header">
    <h1>{page.title or entity.label}</h1>
    <button mat-raised-button color="primary" (click)="createNew()">
      Create New
    </button>
  </div>

  <table mat-table [dataSource]="dataSource$ | async" class="mat-elevation-z8">
{columns_html}

    <ng-container matColumnDef="actions">
      <th mat-header-cell *matHeaderCellDef>Actions</th>
      <td mat-cell *matCellDef="let element">
        <button mat-button (click)="viewDetails(element.id)">View</button>
      </td>
    </ng-container>

    <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
    <tr mat-row *matRowDef="let row; columns: displayedColumns;"></tr>
  </table>

  <mat-paginator [pageSizeOptions]="[10, 20, 50]" showFirstLastButtons></mat-paginator>
</div>
'''

        return GeneratedFile(
            path=Path(f"src/app/pages/{page.entity.lower()}/{component_name}.component.html"),
            content=content,
            file_type='component'
        )

    def _to_component_name(self, name: str) -> str:
        """Convert to kebab-case"""
        return name.lower().replace('_', '-')

    def _to_class_name(self, component_name: str) -> str:
        """Convert to PascalCase"""
        return ''.join(word.title() for word in component_name.split('-'))

    def _to_selector(self, component_name: str) -> str:
        """Generate component selector"""
        return f'app-{component_name}'
```

**Afternoon**: Form and detail page generators with Reactive Forms

---

### Day 4: Angular Services & Routing

**Morning**: Generate Angular services (HTTP + RxJS)
**Afternoon**: Generate Angular Router configuration

**Generated Service**:
```typescript
// src/app/services/contact.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { Contact } from '@/models/contact';

@Injectable({
  providedIn: 'root'
})
export class ContactService {
  private apiUrl = '/graphql';

  constructor(private http: HttpClient) {}

  getAll(): Observable<Contact[]> {
    const query = `
      query {
        contacts {
          id email company { id name } status
        }
      }
    `;

    return this.http.post<{ data: { contacts: Contact[] } }>(
      this.apiUrl,
      { query }
    ).pipe(
      map(response => response.data.contacts)
    );
  }
}
```

---

### Day 5: Integration Testing & CLI

**Morning**: Round-trip testing (parse Angular → generate Angular)
**Afternoon**: CLI integration and documentation

**CLI Command**:
```bash
# Parse existing Angular app
specql parse-angular src/app --output frontend.yaml

# Generate Angular app from UniversalFrontend
specql generate-angular frontend.yaml --output src/app --library material

# With standalone components
specql generate-angular frontend.yaml --standalone --output src/app
```

---

## ✅ Success Criteria

- [ ] Angular component parser working (TypeScript compiler API)
- [ ] Pattern detection for Angular components
- [ ] List page generator (Angular Material)
- [ ] Form page generator (Reactive Forms)
- [ ] Detail page generator
- [ ] TypeScript types/models generated
- [ ] Angular services generated (HttpClient + RxJS)
- [ ] Angular Router configuration generated
- [ ] Standalone components support
- [ ] Round-trip test passing (parse Angular → generate Angular)
- [ ] 100+ unit tests passing
- [ ] CLI commands functional
- [ ] Documentation complete

---

## 🧪 Testing Strategy

**Unit Tests**:
- Angular component parsing
- Decorator extraction
- Component generation for each page type
- Service generation
- Router configuration

**Integration Tests**:
- Generate complete Angular app from YAML
- Run generated app (compile check with Angular CLI)
- Round-trip: parse Angular app → generate → compare

---

## 🔗 Related Files

- **Previous**: [Week 28: Vue Parser & Generation](./WEEK_28.md)
- **Next**: [Week 30: Multi-Framework Testing](./WEEK_30.md)
- **Grammar**: [Week 25: Universal Component Grammar](./WEEK_25.md)

---

**Status**: 📅 Planned (completes major framework coverage)
**Complexity**: High (Angular most complex of the three)
**Risk**: Low (TypeScript compiler API well-documented)
**Impact**: Covers React + Vue + Angular = 70%+ of web market
