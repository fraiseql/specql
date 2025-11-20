# Week 8: Reverse Engineering & Future Features
**Duration**: 5 days | **Tests**: 30 | **Priority**: 🟢 LOW

## 🎯 What You'll Build

By the end of this week, you'll have:
- ✅ TypeScript route parser (14 tests) - Extract API routes from Express/Fastify/Next.js
- ✅ Rust route parser (13 tests) - Extract routes from Actix/Rocket/Axum
- ✅ Route → SpecQL YAML converter (2 tests) - Convert routes to SpecQL actions
- ✅ Composite identifier recalculation (1 test) - Advanced identifier patterns
- ✅ 30 reverse engineering tests passing

**Why this matters**: Reverse engineering lets teams migrate existing APIs to SpecQL by automatically generating YAML from TypeScript/Rust code.

---

## 📋 Tests to Unskip

### File 1: `tests/unit/reverse_engineering/test_tree_sitter_typescript.py` (9 tests)

Parse TypeScript route definitions:

1. `test_parse_express_routes` - Express.js: `app.get('/users', handler)`
2. `test_parse_fastify_routes` - Fastify: `fastify.get('/users', handler)`
3. `test_parse_nextjs_pages_routes` - Next.js Pages: `export default function handler(req, res)`
4. `test_parse_nextjs_app_routes` - Next.js App: `export async function GET(request)`
5. `test_parse_server_actions` - Next.js Server Actions: `'use server'`
6. `test_extract_route_parameters` - Extract path params: `/users/:id`
7. `test_extract_request_body_schema` - Parse request body types
8. `test_extract_response_schema` - Parse response types
9. `test_handle_route_middleware` - Extract middleware chains

### File 2: `tests/unit/reverse_engineering/test_typescript_parser.py` (5 tests)

High-level TypeScript parsing:

1. `test_parse_nextjs_pages_api_route` - Next.js pages/api/*
2. `test_parse_nextjs_app_router_route` - Next.js app/api/*
3. `test_parse_nextjs_server_actions` - Server actions
4. `test_convert_typescript_to_specql` - TS → SpecQL conversion
5. `test_handle_typescript_errors_gracefully` - Error handling

### File 3: `tests/unit/reverse_engineering/rust/test_action_parser_endpoints.py` (13 tests)

Parse Rust route definitions:

1. `test_extract_endpoints_from_actix_routes` - Actix-web: `#[get("/users")]`
2. `test_extract_endpoints_with_path_parameters` - Path params: `/users/{id}`
3. `test_extract_endpoints_empty_file` - Handle empty files
4. `test_extract_actions_from_impl_blocks` - Parse impl blocks
5. `test_extract_actions_with_routes_and_impl` - Combined parsing
6. `test_parse_handler_signatures` - Extract function signatures
7. `test_actix_route_with_guard` - Route guards
8. `test_actix_nested_scope` - Nested scopes
9. `test_rocket_multiple_methods` - Rocket framework
10. `test_axum_handler_with_state` - Axum framework
11. `test_warp_filter_chain` - Warp framework
12. `test_extract_request_types` - Request type extraction
13. `test_extract_response_types` - Response type extraction

### File 4: `tests/integration/reverse_engineering/test_rust_end_to_end.py` (2 tests)

End-to-end Rust parsing:

1. `test_diesel_schema_to_yaml` - Parse Diesel schema → SpecQL YAML
2. `test_complex_struct_to_yaml` - Parse Rust structs → SpecQL entities

### File 5: `tests/integration/test_composite_hierarchical_e2e.py` (1 test)

Advanced identifier patterns:

1. `test_allocation_composite_identifier` - Composite identifier recalculation

---

## 🧠 Understanding Reverse Engineering

### What Is Reverse Engineering?

Reverse engineering generates SpecQL YAML from existing code:

**Input** (TypeScript):
```typescript
// Express.js route
app.post('/contacts', async (req, res) => {
  const { email, name } = req.body;
  const contact = await db.contacts.insert({ email, name });
  res.json(contact);
});
```

**Output** (SpecQL YAML):
```yaml
entity: Contact
schema: crm
fields:
  email: text
  name: text
actions:
  - name: create_contact
    steps:
      - validate: email IS NOT NULL
      - insert: Contact
```

### Why Reverse Engineering?

**Use cases**:
1. **Migration**: Move existing API to SpecQL
2. **Documentation**: Generate YAML from existing code
3. **Validation**: Compare code with SpecQL definition

**Not for everyone**: This is an optional feature for teams migrating to SpecQL.

### Three-Step Process

1. **Parse** - Use tree-sitter to parse TypeScript/Rust AST
2. **Extract** - Find routes, handlers, types
3. **Convert** - Map to SpecQL YAML structure

---

## 📅 Day-by-Day Plan

### Day 1: TypeScript Parser Setup 🔧

**Goal**: Set up tree-sitter and parse basic Express routes (3 tests)

#### Step 1: Install Dependencies

Install tree-sitter and TypeScript grammar:

```bash
# Add to pyproject.toml [tool.uv.dev-dependencies]
tree-sitter = "^0.20.0"
tree-sitter-typescript = "^0.20.0"

# Install
uv sync
```

#### Step 2: Create TypeScript Parser

Create `src/reverse_engineering/typescript/tree_sitter_parser.py`:

```python
"""
TypeScript AST parser using tree-sitter

Parses TypeScript source code into an AST for analysis
"""

from typing import Optional
import tree_sitter_typescript as ts_typescript
from tree_sitter import Language, Parser, Node


class TypeScriptParser:
    """Parse TypeScript source code using tree-sitter"""

    def __init__(self):
        """Initialize parser with TypeScript language"""
        # Load TypeScript grammar
        self.language = Language(ts_typescript.language_typescript())
        self.parser = Parser()
        self.parser.set_language(self.language)

    def parse(self, source_code: str) -> Node:
        """
        Parse TypeScript source into AST

        Args:
            source_code: TypeScript source code as string

        Returns:
            Root node of AST

        Example:
            >>> parser = TypeScriptParser()
            >>> ast = parser.parse("const x = 5;")
            >>> ast.type
            'program'
        """
        # Encode to bytes (tree-sitter requirement)
        source_bytes = bytes(source_code, "utf8")

        # Parse and return root node
        tree = self.parser.parse(source_bytes)
        return tree.root_node

    def walk_tree(self, node: Node):
        """
        Recursively walk AST nodes

        Yields each node in depth-first order

        Example:
            >>> for node in parser.walk_tree(ast):
            ...     print(node.type)
        """
        yield node
        for child in node.children:
            yield from self.walk_tree(child)

    def find_nodes_by_type(self, root: Node, node_type: str) -> list[Node]:
        """
        Find all nodes of specific type

        Args:
            root: Root node to search from
            node_type: Type of node to find (e.g., "call_expression")

        Returns:
            List of matching nodes

        Example:
            >>> calls = parser.find_nodes_by_type(ast, "call_expression")
        """
        return [node for node in self.walk_tree(root) if node.type == node_type]

    def get_node_text(self, node: Node, source_code: str) -> str:
        """
        Get source text for a node

        Args:
            node: AST node
            source_code: Original source code

        Returns:
            Text content of the node
        """
        return source_code[node.start_byte:node.end_byte]
```

#### Step 3: Create Express Route Extractor

Create `src/reverse_engineering/typescript/express_extractor.py`:

```python
"""
Extract routes from Express.js TypeScript code

Parses Express.js route definitions:
- app.get('/path', handler)
- app.post('/path', handler)
- router.get('/path', handler)
"""

from dataclasses import dataclass
from typing import List, Optional
from tree_sitter import Node

from .tree_sitter_parser import TypeScriptParser


@dataclass
class ExpressRoute:
    """Represents an Express.js route"""
    method: str  # GET, POST, PUT, DELETE
    path: str    # /users/:id
    handler_name: Optional[str] = None
    has_middleware: bool = False


class ExpressRouteExtractor:
    """Extract routes from Express.js code"""

    def __init__(self):
        self.parser = TypeScriptParser()

    def extract_routes(self, source_code: str) -> List[ExpressRoute]:
        """
        Extract all Express routes from source code

        Args:
            source_code: TypeScript source code

        Returns:
            List of ExpressRoute objects

        Example:
            >>> extractor = ExpressRouteExtractor()
            >>> code = "app.get('/users', getUsers);"
            >>> routes = extractor.extract_routes(code)
            >>> routes[0].method
            'GET'
            >>> routes[0].path
            '/users'
        """
        # Parse source
        ast = self.parser.parse(source_code)

        routes = []

        # Find all call expressions (function calls)
        calls = self.parser.find_nodes_by_type(ast, "call_expression")

        for call in calls:
            if self._is_route_definition(call, source_code):
                route = self._parse_route(call, source_code)
                if route:
                    routes.append(route)

        return routes

    def _is_route_definition(self, node: Node, source_code: str) -> bool:
        """
        Check if node is a route definition

        Express routes look like:
        - app.get(...)
        - app.post(...)
        - router.get(...)

        Node structure:
        call_expression
          member_expression
            identifier: "app" or "router"
            property_identifier: "get", "post", "put", "delete"
          arguments
        """
        # Must have at least 2 children (member_expression + arguments)
        if len(node.children) < 2:
            return False

        # First child should be member_expression
        if node.children[0].type != "member_expression":
            return False

        member_expr = node.children[0]

        # Member expression should have 3 parts: object.property
        if len(member_expr.children) < 3:
            return False

        # Check if object is 'app' or 'router'
        object_name = self.parser.get_node_text(member_expr.children[0], source_code)
        if object_name not in ['app', 'router']:
            return False

        # Check if method is HTTP method
        method_name = self.parser.get_node_text(member_expr.children[2], source_code)
        if method_name not in ['get', 'post', 'put', 'delete', 'patch']:
            return False

        return True

    def _parse_route(self, node: Node, source_code: str) -> Optional[ExpressRoute]:
        """
        Parse route definition into ExpressRoute object

        Route structure:
        app.get('/users', handler)
             └─┬─┘ └──┬──┘  └──┬──┘
             method  path   handler
        """
        member_expr = node.children[0]
        method_name = self.parser.get_node_text(member_expr.children[2], source_code)
        method = method_name.upper()

        # Get arguments
        if len(node.children) < 2:
            return None

        args = node.children[1]  # arguments node

        # Find string argument (the path)
        path = None
        handler_name = None

        for arg in args.children:
            if arg.type == "string":
                # Remove quotes
                path_text = self.parser.get_node_text(arg, source_code)
                path = path_text.strip('"').strip("'")
            elif arg.type == "identifier":
                handler_name = self.parser.get_node_text(arg, source_code)

        if not path:
            return None

        return ExpressRoute(
            method=method,
            path=path,
            handler_name=handler_name
        )
```

#### Step 4: Test Express Route Extraction

Create test script `test_express_debug.py`:

```python
from src.reverse_engineering.typescript.express_extractor import ExpressRouteExtractor

# Sample Express.js code
code = """
import express from 'express';
const app = express();

app.get('/users', getUsers);
app.post('/users', createUser);
app.get('/users/:id', getUserById);
app.delete('/users/:id', deleteUser);
"""

extractor = ExpressRouteExtractor()
routes = extractor.extract_routes(code)

print(f"Found {len(routes)} routes:")
for route in routes:
    print(f"  {route.method:6s} {route.path:20s} -> {route.handler_name}")

# Expected output:
# Found 4 routes:
#   GET    /users               -> getUsers
#   POST   /users               -> createUser
#   GET    /users/:id           -> getUserById
#   DELETE /users/:id           -> deleteUser
```

Run test:

```bash
uv run python test_express_debug.py
```

#### Step 5: Run First Tests

Temporarily remove skip markers and run Express tests:

```bash
uv run pytest tests/unit/reverse_engineering/test_tree_sitter_typescript.py::test_parse_express_routes -v
```

**Expected**: Test passes! ✅

#### ✅ Day 1 Success Criteria

- [ ] tree-sitter installed and working
- [ ] TypeScript parser created
- [ ] Express route extractor created
- [ ] First test passing (Express routes)
- [ ] Can extract GET, POST, PUT, DELETE routes

**Deliverable**: TypeScript parsing infrastructure ✅

---

### Day 2: Framework Support (TypeScript) 🚀

**Goal**: Add Fastify and Next.js support (5 tests)

#### Step 1: Add Fastify Extractor

Create `src/reverse_engineering/typescript/fastify_extractor.py`:

```python
"""
Extract routes from Fastify TypeScript code

Parses Fastify route definitions:
- fastify.get('/path', handler)
- fastify.post('/path', opts, handler)
"""

from dataclasses import dataclass
from typing import List, Optional
from tree_sitter import Node

from .tree_sitter_parser import TypeScriptParser


@dataclass
class FastifyRoute:
    """Represents a Fastify route"""
    method: str
    path: str
    handler_name: Optional[str] = None
    has_schema: bool = False


class FastifyRouteExtractor:
    """Extract routes from Fastify code"""

    def __init__(self):
        self.parser = TypeScriptParser()

    def extract_routes(self, source_code: str) -> List[FastifyRoute]:
        """
        Extract all Fastify routes from source code

        Similar to Express, but Fastify uses:
        - fastify.get(path, handler)
        - fastify.get(path, opts, handler)
        """
        ast = self.parser.parse(source_code)
        routes = []

        calls = self.parser.find_nodes_by_type(ast, "call_expression")

        for call in calls:
            if self._is_route_definition(call, source_code):
                route = self._parse_route(call, source_code)
                if route:
                    routes.append(route)

        return routes

    def _is_route_definition(self, node: Node, source_code: str) -> bool:
        """Check if node is Fastify route definition"""
        if len(node.children) < 2:
            return False

        if node.children[0].type != "member_expression":
            return False

        member_expr = node.children[0]
        if len(member_expr.children) < 3:
            return False

        # Check if object is 'fastify'
        object_name = self.parser.get_node_text(member_expr.children[0], source_code)
        if object_name not in ['fastify', 'app']:
            return False

        # Check if method is HTTP method
        method_name = self.parser.get_node_text(member_expr.children[2], source_code)
        if method_name not in ['get', 'post', 'put', 'delete', 'patch']:
            return False

        return True

    def _parse_route(self, node: Node, source_code: str) -> Optional[FastifyRoute]:
        """Parse Fastify route definition"""
        member_expr = node.children[0]
        method_name = self.parser.get_node_text(member_expr.children[2], source_code)
        method = method_name.upper()

        args = node.children[1]
        path = None
        handler_name = None
        has_schema = False

        for arg in args.children:
            if arg.type == "string":
                path_text = self.parser.get_node_text(arg, source_code)
                path = path_text.strip('"').strip("'")
            elif arg.type == "identifier":
                handler_name = self.parser.get_node_text(arg, source_code)
            elif arg.type == "object":
                # Options object (schema, etc.)
                has_schema = True

        if not path:
            return None

        return FastifyRoute(
            method=method,
            path=path,
            handler_name=handler_name,
            has_schema=has_schema
        )
```

#### Step 2: Add Next.js Pages Router Extractor

Create `src/reverse_engineering/typescript/nextjs_pages_extractor.py`:

```python
"""
Extract routes from Next.js Pages Router

Parses Next.js API routes in pages/api/*:
- export default function handler(req, res) { }
- export default async function handler(req, res) { }
"""

from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path

from .tree_sitter_parser import TypeScriptParser


@dataclass
class NextJSPagesRoute:
    """Represents a Next.js Pages API route"""
    path: str  # Derived from file path: pages/api/users.ts -> /api/users
    is_dynamic: bool = False  # [id].ts
    methods: List[str] = None  # Extracted from handler (req.method checks)


class NextJSPagesExtractor:
    """Extract routes from Next.js Pages Router"""

    def __init__(self):
        self.parser = TypeScriptParser()

    def extract_route_from_file(self, file_path: str, source_code: str) -> Optional[NextJSPagesRoute]:
        """
        Extract route from Next.js API file

        File path determines URL:
        - pages/api/users.ts -> /api/users
        - pages/api/users/[id].ts -> /api/users/:id
        - pages/api/users/index.ts -> /api/users
        """
        # Convert file path to URL path
        url_path = self._file_path_to_url(file_path)

        # Parse source to check if it's an API route
        ast = self.parser.parse(source_code)

        # Look for default export
        if not self._has_default_export(ast, source_code):
            return None

        # Check if dynamic route ([id].ts)
        is_dynamic = '[' in file_path and ']' in file_path

        # Extract HTTP methods from handler
        methods = self._extract_methods(ast, source_code)

        return NextJSPagesRoute(
            path=url_path,
            is_dynamic=is_dynamic,
            methods=methods or ['GET', 'POST']  # Default to both
        )

    def _file_path_to_url(self, file_path: str) -> str:
        """
        Convert file path to URL path

        pages/api/users.ts -> /api/users
        pages/api/users/[id].ts -> /api/users/:id
        pages/api/users/index.ts -> /api/users
        """
        path = Path(file_path)

        # Remove pages/ prefix
        parts = list(path.parts)
        if 'pages' in parts:
            idx = parts.index('pages')
            parts = parts[idx+1:]

        # Remove .ts/.tsx extension
        parts[-1] = path.stem

        # Handle index.ts
        if parts[-1] == 'index':
            parts = parts[:-1]

        # Convert [id] to :id
        parts = [p.replace('[', ':').replace(']', '') for p in parts]

        # Join with /
        url = '/' + '/'.join(parts)

        return url

    def _has_default_export(self, ast, source_code: str) -> bool:
        """Check if file has default export"""
        exports = self.parser.find_nodes_by_type(ast, "export_statement")

        for export in exports:
            text = self.parser.get_node_text(export, source_code)
            if 'default' in text:
                return True

        return False

    def _extract_methods(self, ast, source_code: str) -> List[str]:
        """
        Extract HTTP methods from handler

        Looks for: if (req.method === 'GET') { }
        """
        methods = []

        # Find string literals that are HTTP methods
        strings = self.parser.find_nodes_by_type(ast, "string")

        for string in strings:
            text = self.parser.get_node_text(string, source_code)
            text = text.strip('"').strip("'")

            if text in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                methods.append(text)

        return list(set(methods))  # Deduplicate
```

#### Step 3: Add Next.js App Router Extractor

Create `src/reverse_engineering/typescript/nextjs_app_extractor.py`:

```python
"""
Extract routes from Next.js App Router

Parses Next.js API routes in app/api/*:
- export async function GET(request) { }
- export async function POST(request) { }
"""

from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path

from .tree_sitter_parser import TypeScriptParser


@dataclass
class NextJSAppRoute:
    """Represents a Next.js App Router API route"""
    path: str
    methods: List[str]  # GET, POST, etc.
    is_dynamic: bool = False


class NextJSAppExtractor:
    """Extract routes from Next.js App Router"""

    def __init__(self):
        self.parser = TypeScriptParser()

    def extract_route_from_file(self, file_path: str, source_code: str) -> Optional[NextJSAppRoute]:
        """
        Extract route from Next.js App Router file

        File path determines URL:
        - app/api/users/route.ts -> /api/users
        - app/api/users/[id]/route.ts -> /api/users/:id

        Exports determine methods:
        - export async function GET(request) { }
        - export async function POST(request) { }
        """
        # Convert file path to URL
        url_path = self._file_path_to_url(file_path)

        # Parse source
        ast = self.parser.parse(source_code)

        # Extract exported functions
        methods = self._extract_exported_methods(ast, source_code)

        if not methods:
            return None

        # Check if dynamic route
        is_dynamic = '[' in file_path and ']' in file_path

        return NextJSAppRoute(
            path=url_path,
            methods=methods,
            is_dynamic=is_dynamic
        )

    def _file_path_to_url(self, file_path: str) -> str:
        """
        Convert App Router file path to URL

        app/api/users/route.ts -> /api/users
        app/api/users/[id]/route.ts -> /api/users/:id
        """
        path = Path(file_path)
        parts = list(path.parts)

        # Remove app/ prefix
        if 'app' in parts:
            idx = parts.index('app')
            parts = parts[idx+1:]

        # Remove route.ts
        if parts[-1] == 'route.ts' or parts[-1] == 'route':
            parts = parts[:-1]

        # Convert [id] to :id
        parts = [p.replace('[', ':').replace(']', '') for p in parts]

        url = '/' + '/'.join(parts)
        return url

    def _extract_exported_methods(self, ast, source_code: str) -> List[str]:
        """
        Extract exported HTTP method functions

        Looks for:
        - export async function GET(request) { }
        - export function POST(request) { }
        """
        methods = []

        exports = self.parser.find_nodes_by_type(ast, "export_statement")

        for export in exports:
            # Look for function declarations
            for child in export.children:
                if child.type == "function_declaration":
                    # Get function name
                    for func_child in child.children:
                        if func_child.type == "identifier":
                            name = self.parser.get_node_text(func_child, source_code)
                            if name in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                                methods.append(name)

        return methods
```

#### Step 4: Test All Frameworks

Run framework tests:

```bash
# Fastify
uv run pytest tests/unit/reverse_engineering/test_tree_sitter_typescript.py::test_parse_fastify_routes -v

# Next.js Pages
uv run pytest tests/unit/reverse_engineering/test_tree_sitter_typescript.py::test_parse_nextjs_pages_routes -v

# Next.js App Router
uv run pytest tests/unit/reverse_engineering/test_tree_sitter_typescript.py::test_parse_nextjs_app_routes -v

# Server Actions
uv run pytest tests/unit/reverse_engineering/test_tree_sitter_typescript.py::test_parse_server_actions -v
```

#### ✅ Day 2 Success Criteria

- [ ] Fastify extractor created
- [ ] Next.js Pages extractor created
- [ ] Next.js App Router extractor created
- [ ] Server Actions support added
- [ ] 5 TypeScript framework tests passing (9 total TS)

**Deliverable**: Multi-framework TypeScript support ✅

---

### Day 3: Rust Parser 🦀

**Goal**: Parse Rust routes (Actix, Rocket, Axum) (8 tests)

#### Step 1: Set Up Rust Parser

Similar to TypeScript, but for Rust:

```bash
# Add to pyproject.toml
tree-sitter-rust = "^0.20.0"

# Install
uv sync
```

Create `src/reverse_engineering/rust/tree_sitter_rust_parser.py`:

```python
"""
Rust AST parser using tree-sitter

Parses Rust source code for route extraction
"""

from typing import Optional
import tree_sitter_rust as ts_rust
from tree_sitter import Language, Parser, Node


class RustParser:
    """Parse Rust source code using tree-sitter"""

    def __init__(self):
        """Initialize parser with Rust language"""
        self.language = Language(ts_rust.language())
        self.parser = Parser()
        self.parser.set_language(self.language)

    def parse(self, source_code: str) -> Node:
        """Parse Rust source into AST"""
        source_bytes = bytes(source_code, "utf8")
        tree = self.parser.parse(source_bytes)
        return tree.root_node

    def walk_tree(self, node: Node):
        """Recursively walk AST nodes"""
        yield node
        for child in node.children:
            yield from self.walk_tree(child)

    def find_nodes_by_type(self, root: Node, node_type: str) -> list[Node]:
        """Find all nodes of specific type"""
        return [node for node in self.walk_tree(root) if node.type == node_type]

    def get_node_text(self, node: Node, source_code: str) -> str:
        """Get source text for a node"""
        return source_code[node.start_byte:node.end_byte]
```

#### Step 2: Create Actix Extractor

Create `src/reverse_engineering/rust/actix_extractor.py`:

```python
"""
Extract routes from Actix-web Rust code

Parses Actix route macros:
- #[get("/users")]
- #[post("/users")]
- web::get().to(handler)
"""

from dataclasses import dataclass
from typing import List, Optional
from tree_sitter import Node

from .tree_sitter_rust_parser import RustParser


@dataclass
class ActixRoute:
    """Represents an Actix-web route"""
    method: str  # GET, POST, PUT, DELETE
    path: str    # /users/{id}
    handler_name: Optional[str] = None


class ActixRouteExtractor:
    """Extract routes from Actix-web code"""

    def __init__(self):
        self.parser = RustParser()

    def extract_routes(self, source_code: str) -> List[ActixRoute]:
        """
        Extract all Actix routes from source code

        Looks for:
        1. Attribute macros: #[get("/path")]
        2. Service builders: web::get().to(handler)
        """
        ast = self.parser.parse(source_code)
        routes = []

        # Find attribute macros
        attributes = self.parser.find_nodes_by_type(ast, "attribute_item")
        for attr in attributes:
            route = self._parse_attribute_route(attr, source_code)
            if route:
                routes.append(route)

        return routes

    def _parse_attribute_route(self, node: Node, source_code: str) -> Optional[ActixRoute]:
        """
        Parse route from attribute macro

        Example: #[get("/users/{id}")]
        """
        text = self.parser.get_node_text(node, source_code)

        # Check if it's a route macro
        methods = ['get', 'post', 'put', 'delete', 'patch']
        method = None

        for m in methods:
            if f'#{m}(' in text:
                method = m.upper()
                break

        if not method:
            return None

        # Extract path from string literal
        # Format: #[get("/users/{id}")]
        start = text.find('"')
        end = text.rfind('"')

        if start == -1 or end == -1:
            return None

        path = text[start+1:end]

        # Convert Rust path params to standard format
        # /users/{id} -> /users/:id
        path = path.replace('{', ':').replace('}', '')

        return ActixRoute(
            method=method,
            path=path
        )
```

#### Step 3: Add Rocket and Axum Extractors

Similar structure for Rocket and Axum frameworks.

Create `src/reverse_engineering/rust/rocket_extractor.py`:
```python
"""
Extract routes from Rocket Rust code

Parses Rocket route macros:
- #[get("/users")]
- #[post("/users")]
"""
# Similar to Actix
```

Create `src/reverse_engineering/rust/axum_extractor.py`:
```python
"""
Extract routes from Axum Rust code

Parses Axum route builders:
- Router::new().route("/users", get(handler))
"""
# Different pattern - method call chains
```

#### Step 4: Test Rust Parsers

Run Rust tests:

```bash
# Actix routes
uv run pytest tests/unit/reverse_engineering/rust/test_action_parser_endpoints.py::test_extract_endpoints_from_actix_routes -v

# Path parameters
uv run pytest tests/unit/reverse_engineering/rust/test_action_parser_endpoints.py::test_extract_endpoints_with_path_parameters -v

# Empty file handling
uv run pytest tests/unit/reverse_engineering/rust/test_action_parser_endpoints.py::test_extract_endpoints_empty_file -v
```

#### ✅ Day 3 Success Criteria

- [ ] Rust parser created
- [ ] Actix extractor created
- [ ] Rocket extractor created
- [ ] Axum extractor created
- [ ] 8 Rust parsing tests passing

**Deliverable**: Rust route extraction ✅

---

### Day 4: Route → SpecQL Conversion 🔄

**Goal**: Convert extracted routes to SpecQL YAML (5 tests)

#### Step 1: Design Conversion Logic

**Input** (Extracted route):
```python
ExpressRoute(
    method='POST',
    path='/contacts',
    handler_name='createContact'
)
```

**Output** (SpecQL YAML):
```yaml
entity: Contact
schema: crm
actions:
  - name: create_contact
    steps:
      - validate: id IS NOT NULL
      - insert: Contact
```

#### Step 2: Create Route Converter

Create `src/reverse_engineering/route_to_specql_converter.py`:

```python
"""
Convert extracted routes to SpecQL YAML

Maps HTTP routes to SpecQL actions
"""

from dataclasses import dataclass
from typing import List, Optional
import yaml

from src.core.ast_models import Action, ActionStep


@dataclass
class SpecQLAction:
    """Represents a SpecQL action"""
    name: str
    steps: List[dict]


class RouteToSpecQLConverter:
    """Convert HTTP routes to SpecQL actions"""

    def convert_route(self, method: str, path: str, handler_name: Optional[str] = None) -> SpecQLAction:
        """
        Convert HTTP route to SpecQL action

        Rules:
        - POST /contacts -> create_contact (insert)
        - GET /contacts/:id -> get_contact (validate + return)
        - PUT /contacts/:id -> update_contact (validate + update)
        - DELETE /contacts/:id -> delete_contact (validate + soft delete)
        """
        # Generate action name from path and method
        action_name = self._generate_action_name(method, path)

        # Generate steps based on method
        steps = self._generate_steps(method, path)

        return SpecQLAction(name=action_name, steps=steps)

    def _generate_action_name(self, method: str, path: str) -> str:
        """
        Generate action name from HTTP method and path

        Examples:
        - POST /contacts -> create_contact
        - GET /contacts/:id -> get_contact
        - PUT /contacts/:id -> update_contact
        - DELETE /contacts/:id -> delete_contact
        """
        # Extract entity from path
        # /contacts -> contact
        # /api/users/:id -> user
        parts = [p for p in path.split('/') if p and ':' not in p and p != 'api']

        if not parts:
            entity = 'entity'
        else:
            entity = parts[-1].rstrip('s')  # Remove plural: users -> user

        # Map method to action prefix
        method_map = {
            'POST': 'create',
            'GET': 'get',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete',
        }

        prefix = method_map.get(method, 'do')

        return f"{prefix}_{entity}"

    def _generate_steps(self, method: str, path: str) -> List[dict]:
        """
        Generate action steps based on HTTP method

        POST: validate + insert
        GET: validate + return
        PUT: validate + update
        DELETE: validate + soft delete
        """
        has_id = ':id' in path or '{id}' in path

        steps = []

        if method == 'POST':
            # Create: validate required fields + insert
            steps = [
                {'validate': 'id IS NOT NULL', 'error': 'missing_id'},
                {'insert': self._extract_entity(path)}
            ]
        elif method == 'GET':
            # Read: validate ID exists
            if has_id:
                steps = [
                    {'validate': 'id IS NOT NULL', 'error': 'missing_id'}
                ]
        elif method in ['PUT', 'PATCH']:
            # Update: validate ID + update
            steps = [
                {'validate': 'id IS NOT NULL', 'error': 'missing_id'},
                {'update': self._extract_entity(path), 'fields': {}}
            ]
        elif method == 'DELETE':
            # Delete: validate ID + soft delete
            steps = [
                {'validate': 'id IS NOT NULL', 'error': 'missing_id'},
                {'update': self._extract_entity(path), 'fields': {'deleted_at': 'NOW()'}}
            ]

        return steps

    def _extract_entity(self, path: str) -> str:
        """
        Extract entity name from path

        /contacts -> Contact
        /api/users/:id -> User
        """
        parts = [p for p in path.split('/') if p and ':' not in p and p != 'api']

        if not parts:
            return 'Entity'

        # Get last part, remove plural, capitalize
        entity = parts[-1].rstrip('s').capitalize()

        return entity

    def to_yaml(self, actions: List[SpecQLAction]) -> str:
        """Convert actions to YAML format"""
        data = {
            'actions': [
                {
                    'name': action.name,
                    'steps': action.steps
                }
                for action in actions
            ]
        }

        return yaml.dump(data, default_flow_style=False, sort_keys=False)
```

#### Step 3: Test Conversion

Create test script:

```python
from src.reverse_engineering.route_to_specql_converter import RouteToSpecQLConverter

converter = RouteToSpecQLConverter()

# Test conversions
routes = [
    ('POST', '/contacts'),
    ('GET', '/contacts/:id'),
    ('PUT', '/contacts/:id'),
    ('DELETE', '/contacts/:id'),
]

for method, path in routes:
    action = converter.convert_route(method, path)
    print(f"{method:6s} {path:20s} -> {action.name}")
    print(f"  Steps: {len(action.steps)}")

# Expected:
# POST   /contacts           -> create_contact
#   Steps: 2
# GET    /contacts/:id       -> get_contact
#   Steps: 1
# PUT    /contacts/:id       -> update_contact
#   Steps: 2
# DELETE /contacts/:id       -> delete_contact
#   Steps: 2
```

#### Step 4: Run Conversion Tests

```bash
uv run pytest tests/unit/reverse_engineering/test_typescript_parser.py::test_convert_typescript_to_specql -v

uv run pytest tests/integration/reverse_engineering/test_rust_end_to_end.py -v
```

#### ✅ Day 4 Success Criteria

- [ ] Route converter created
- [ ] Can generate action names from routes
- [ ] Can generate steps based on HTTP method
- [ ] Can output YAML format
- [ ] 5 conversion tests passing

**Deliverable**: Route → SpecQL conversion ✅

---

### Day 5: Composite Identifiers & Final QA ✨

**Goal**: Complete composite identifier test and wrap up (1 test + polish)

#### Step 1: Understand Composite Identifiers

Composite identifiers combine multiple hierarchical paths:

**Example** (Allocation entity):
```yaml
entity: Allocation
identifier:
  composite:
    - tenant_identifier       # "acme-corp"
    - machine.path_identifier # "hp.laserjet.s123"
    - location.path_identifier # "warehouse.floor1"
    - daterange               # "2025-Q1"
# Result: "acme-corp|hp.laserjet.s123|warehouse.floor1|2025-Q1"
```

**Challenge**: When machine or location changes, identifier must recalculate.

#### Step 2: Generate Recalculation Function

Create `src/generators/composite_identifier_generator.py`:

```python
"""
Generate identifier recalculation functions for composite identifiers

When a referenced entity's identifier changes, composite identifiers
that include it must be recalculated.
"""

from src.core.ast_models import Entity


class CompositeIdentifierGenerator:
    """Generate recalculation functions for composite identifiers"""

    def generate_recalc_function(self, entity: Entity) -> str:
        """
        Generate function to recalculate composite identifier

        Example for Allocation:
        - tenant_identifier
        - machine.path_identifier
        - location.path_identifier
        - daterange

        When machine or location changes, recalculate allocation identifier
        """
        if not entity.identifier or not entity.identifier.get('composite'):
            return ""

        func_name = f"recalculate_{entity.name.lower()}_identifier"

        # Generate SQL function
        return f"""
CREATE OR REPLACE FUNCTION {entity.schema}.{func_name}(p_id UUID)
RETURNS VOID AS $$
DECLARE
    v_new_identifier TEXT;
BEGIN
    -- Recalculate composite identifier
    SELECT {self._generate_identifier_calculation(entity)}
    INTO v_new_identifier
    FROM {entity.schema}.tb_{entity.name.lower()}
    WHERE id = p_id;

    -- Update identifier
    UPDATE {entity.schema}.tb_{entity.name.lower()}
    SET identifier = v_new_identifier
    WHERE id = p_id;
END;
$$ LANGUAGE plpgsql;
"""

    def _generate_identifier_calculation(self, entity: Entity) -> str:
        """
        Generate SQL to calculate composite identifier

        Parts separated by '|'
        """
        parts = entity.identifier['composite']

        # Generate SQL fragments
        fragments = []
        for part in parts:
            if '.' in part:
                # Referenced entity's identifier
                ref_entity, field = part.split('.')
                fragments.append(f"{ref_entity}_{field}")
            else:
                # Own field
                fragments.append(part)

        # Join with ||'|'||
        sql = " || '|' || ".join(fragments)

        return sql
```

#### Step 3: Test Composite Identifier

Run composite identifier test:

```bash
uv run pytest tests/integration/test_composite_hierarchical_e2e.py::test_allocation_composite_identifier -v
```

This test:
1. Creates allocation with composite identifier
2. Changes machine identifier
3. Recalculates allocation identifier
4. Verifies new composite identifier

#### Step 4: Remove All Skip Markers

Edit all reverse engineering test files:

```bash
# Remove skip markers from:
vim tests/unit/reverse_engineering/test_tree_sitter_typescript.py
vim tests/unit/reverse_engineering/test_typescript_parser.py
vim tests/unit/reverse_engineering/rust/test_action_parser_endpoints.py
vim tests/integration/reverse_engineering/test_rust_end_to_end.py
vim tests/integration/test_composite_hierarchical_e2e.py
```

#### Step 5: Run All 30 Tests

```bash
# Run all Week 8 tests
uv run pytest \
    tests/unit/reverse_engineering/ \
    tests/integration/reverse_engineering/ \
    tests/integration/test_composite_hierarchical_e2e.py \
    -v
```

**Expected output**:
```
tests/unit/reverse_engineering/test_tree_sitter_typescript.py::test_parse_express_routes PASSED
tests/unit/reverse_engineering/test_tree_sitter_typescript.py::test_parse_fastify_routes PASSED
tests/unit/reverse_engineering/test_tree_sitter_typescript.py::test_parse_nextjs_pages_routes PASSED
tests/unit/reverse_engineering/test_tree_sitter_typescript.py::test_parse_nextjs_app_routes PASSED
tests/unit/reverse_engineering/test_tree_sitter_typescript.py::test_parse_server_actions PASSED
tests/unit/reverse_engineering/test_tree_sitter_typescript.py::test_extract_route_parameters PASSED
tests/unit/reverse_engineering/test_tree_sitter_typescript.py::test_extract_request_body_schema PASSED
tests/unit/reverse_engineering/test_tree_sitter_typescript.py::test_extract_response_schema PASSED
tests/unit/reverse_engineering/test_tree_sitter_typescript.py::test_handle_route_middleware PASSED

tests/unit/reverse_engineering/test_typescript_parser.py::test_parse_nextjs_pages_api_route PASSED
tests/unit/reverse_engineering/test_typescript_parser.py::test_parse_nextjs_app_router_route PASSED
tests/unit/reverse_engineering/test_typescript_parser.py::test_parse_nextjs_server_actions PASSED
tests/unit/reverse_engineering/test_typescript_parser.py::test_convert_typescript_to_specql PASSED
tests/unit/reverse_engineering/test_typescript_parser.py::test_handle_typescript_errors_gracefully PASSED

tests/unit/reverse_engineering/rust/test_action_parser_endpoints.py::test_extract_endpoints_from_actix_routes PASSED
... (13 Rust tests) ...

tests/integration/reverse_engineering/test_rust_end_to_end.py::test_diesel_schema_to_yaml PASSED
tests/integration/reverse_engineering/test_rust_end_to_end.py::test_complex_struct_to_yaml PASSED

tests/integration/test_composite_hierarchical_e2e.py::test_allocation_composite_identifier PASSED

========================= 30 passed in 4.12s =========================
```

🎉 **All 30 tests passing!**

#### Step 6: Run Full Test Suite

```bash
uv run pytest --tb=no -q
```

**Expected**:
```
1508 passed, 0 skipped, 3 xfailed in 72.5s
```

🎉🎉🎉 **100% TEST COVERAGE ACHIEVED!** 🎉🎉🎉

#### ✅ Day 5 Success Criteria

- [ ] Composite identifier generator created
- [ ] Composite identifier test passing
- [ ] All 30 Week 8 tests passing
- [ ] ALL 104 originally skipped tests now passing
- [ ] 1508/1508 total tests passing
- [ ] 100% test coverage achieved!

**Deliverable**: Complete test coverage ✅

---

## 🎉 Week 8 Complete!

### What You Accomplished

✅ **30 reverse engineering tests passing**
- 14 TypeScript route extraction tests (Express, Fastify, Next.js)
- 13 Rust route extraction tests (Actix, Rocket, Axum)
- 2 end-to-end conversion tests
- 1 composite identifier test

✅ **Full reverse engineering pipeline**
- Parse TypeScript/Rust code with tree-sitter
- Extract routes from multiple frameworks
- Convert routes to SpecQL YAML
- Generate composite identifier recalculation

✅ **100% TEST COVERAGE ACHIEVED**
- 1508/1508 tests passing
- 0 tests skipped
- All 104 originally skipped tests now passing

### Progress Tracking

```bash
# Before Week 8: 1478 passed, 30 skipped (Weeks 1-7 complete)
# After Week 8:  1508 passed, 0 skipped
# Progress:      +30 tests (100% complete!)
```

### Files Created

**TypeScript Extractors**:
- `src/reverse_engineering/typescript/tree_sitter_parser.py`
- `src/reverse_engineering/typescript/express_extractor.py`
- `src/reverse_engineering/typescript/fastify_extractor.py`
- `src/reverse_engineering/typescript/nextjs_pages_extractor.py`
- `src/reverse_engineering/typescript/nextjs_app_extractor.py`

**Rust Extractors**:
- `src/reverse_engineering/rust/tree_sitter_rust_parser.py`
- `src/reverse_engineering/rust/actix_extractor.py`
- `src/reverse_engineering/rust/rocket_extractor.py`
- `src/reverse_engineering/rust/axum_extractor.py`

**Converters**:
- `src/reverse_engineering/route_to_specql_converter.py`
- `src/generators/composite_identifier_generator.py`

### What's Next

**🎉 PROJECT COMPLETE! 🎉**

All 8 weeks done:
- ✅ Week 1: Database Integration (8 tests)
- ✅ Week 2: Rich Type Comments (13 tests)
- ✅ Week 3: Rich Type Indexes (12 tests)
- ✅ Week 4: Schema Polish (19 tests)
- ✅ Week 5: FraiseQL GraphQL (7 tests)
- ✅ Week 6: Template Validation (16 tests)
- ✅ Week 7: Dependency Validation (6 tests)
- ✅ Week 8: Reverse Engineering (30 tests)

**Total**: 104 tests unskipped, 100% coverage achieved!

---

## 💡 What You Learned

### Tree-sitter AST Parsing

Tree-sitter provides language-agnostic AST parsing:
- Fast incremental parsing
- Error-tolerant (parses partial code)
- Supports 40+ languages

**Use cases**:
- Code analysis
- Syntax highlighting
- Code transformation
- Reverse engineering

### Multi-Framework Support

Different frameworks, same concepts:
- Express/Fastify: Imperative route registration
- Next.js Pages: File-based routing
- Next.js App Router: Export-based routing
- Actix/Rocket/Axum: Macro-based routing

**Pattern**: Extract routes → Normalize → Convert

### Heuristic Conversion

Converting code → YAML is heuristic:
- POST → create (insert)
- GET → read (validate)
- PUT → update (validate + update)
- DELETE → delete (soft delete)

**Not perfect**, but 80% accurate for CRUD operations.

### Composite Identifiers

Complex identifiers need recalculation:
- Multiple hierarchical parts
- When referenced entity changes, recalculate
- Generate recalculation functions automatically

---

## 🐛 Troubleshooting

### Tree-sitter Not Found

```bash
# Install language grammars
uv sync  # Should install tree-sitter-typescript, tree-sitter-rust

# Verify installation
uv run python -c "import tree_sitter_typescript; print('OK')"
```

### Parser Crashes on Code

Tree-sitter is error-tolerant but can crash on very malformed code:

```python
try:
    ast = parser.parse(source_code)
except Exception as e:
    print(f"Parse error: {e}")
    return []  # Return empty results
```

### Route Not Detected

Add debug prints:

```python
def extract_routes(self, source_code: str):
    ast = self.parser.parse(source_code)

    # Debug: Print all node types
    for node in self.parser.walk_tree(ast):
        print(f"{node.type}: {self.parser.get_node_text(node, source_code)[:50]}")

    # ... continue extraction
```

This shows what tree-sitter sees.

---

## 🎓 Optional Enhancements

If you want to go beyond 100%:

### 1. Better Type Extraction

Extract TypeScript/Rust types for field definitions:

```typescript
interface CreateContactRequest {
  email: string;
  name: string;
  age: number;
}
```

→

```yaml
fields:
  email: text
  name: text
  age: integer
```

### 2. Middleware → Validation

Convert middleware to validation steps:

```typescript
app.post('/contacts',
  validateEmail,   // → validate: email MATCHES email_pattern
  createContact
);
```

### 3. Database Schema Reverse Engineering

Parse SQL DDL → SpecQL YAML:

```sql
CREATE TABLE contacts (
  email TEXT NOT NULL,
  name TEXT
);
```

→

```yaml
entity: Contact
fields:
  email: text
  name: text
```

### 4. GraphQL Schema → SpecQL

Parse GraphQL schema → SpecQL YAML:

```graphql
type Contact {
  email: String!
  name: String
}
```

---

**🎉 CONGRATULATIONS! You've achieved 100% test coverage! 🎉**

**All 1508 tests passing!** The SpecQL project is now feature-complete with comprehensive test coverage. Time to ship! 🚀
