# Week 8 Option B: Full Completion Plan (100%)

**Goal**: Achieve 254/254 tests passing (100% completion)
**Duration**: 16-20 hours
**Current Status**: 242/254 passing (95.3%)
**Remaining**: 12 issues (6 Rust framework tests, 5 TypeScript imports, 1 bug)

---

## 📊 Overview

This plan implements ALL remaining Week 8 features to achieve 100% test completion.

### Completion Stages

| Stage | Tasks | Tests Fixed | Time | Cumulative |
|-------|-------|-------------|------|------------|
| Stage 1 | Quick Wins | 6 | 1 hour | 248/254 (97.6%) |
| Stage 2 | Actix Advanced | 3 | 6-8 hours | 251/254 (98.8%) |
| Stage 3 | Other Frameworks | 3 | 6-8 hours | 254/254 (100%) |
| Stage 4 | Code TODOs | 0 | 4-6 hours | 254/254 (100% + polish) |

**Total**: 16-22 hours

---

## 🎯 Stage 1: Quick Wins (1 hour)

### Priority: **HIGH** | Difficulty: **EASY** | Impact: **+6 tests**

These are simple fixes that unlock 6 tests immediately.

---

### Task 1.1: Fix TypeScript Import Errors (30 min)

**Problem**: 5 tests fail with import errors for new `tree_sitter_typescript_parser.py`

**Failing Tests**:
- `test_parse_server_actions`
- `test_parse_complex_typescript`
- `test_parse_error_handling`
- `test_empty_code`
- `test_no_routes`

**Root Cause**: New file exists but not properly imported

#### Step 1: Add to `__init__.py`

**File**: `src/reverse_engineering/typescript/__init__.py`

```python
# Add this import
from .tree_sitter_typescript_parser import TreeSitterTypeScriptParser

__all__ = [
    'TypeScriptParser',
    'ExpressExtractor',
    'FastifyExtractor',
    'NextJSPagesExtractor',
    'NextJSAppExtractor',
    'TreeSitterTypeScriptParser',  # NEW
]
```

#### Step 2: Fix test imports

**File**: `tests/unit/reverse_engineering/test_tree_sitter_typescript.py`

Check if tests import correctly:
```python
from src.reverse_engineering.typescript.tree_sitter_typescript_parser import TreeSitterTypeScriptParser
```

#### Step 3: Verify

```bash
uv run pytest tests/unit/reverse_engineering/test_tree_sitter_typescript.py -v
```

**Expected**: All 5 tests should pass (or run without import errors)

**Result**: 247/254 passing (97.2%)

---

### Task 1.2: Fix Rocket Path Normalization Bug (15 min)

**Problem**: Test expects raw Rocket syntax but gets normalized

**Failing Test**: `test_extract_rocket_routes_from_ast`
- **Expected**: `/users/<id>` (raw Rocket syntax)
- **Got**: `/users/{id}` (normalized)

**Root Cause**: Normalization happens too early in extraction pipeline

#### Solution: Conditional Normalization

**File**: `src/reverse_engineering/tree_sitter_rust_parser.py`

**Current code** (line 481-484):
```python
# Normalize Rocket's <param> to standard {param}
if framework == "rocket":
    path = self._normalize_rocket_path(path)
return (method.upper(), path, framework)
```

**Fix**: Add context parameter
```python
def _parse_route_attribute(self, attr_node: Node, normalize: bool = False) -> Optional[tuple]:
    """Parse route attribute from various frameworks."""
    attr_text = self._get_node_text(attr_node)
    http_methods = ["get", "post", "put", "delete", "patch", "head", "options"]

    for method in http_methods:
        if attr_text.startswith(f"#[{method}"):
            path = self._extract_string_literal(attr_node)
            if path:
                framework = self._detect_framework_from_attribute(attr_node, path)
                # Only normalize when explicitly requested (for endpoints)
                if normalize and framework == "rocket":
                    path = self._normalize_rocket_path(path)
                return (method.upper(), path, framework)

    return None
```

Update callers:
```python
# In extract_routes() - DON'T normalize
route_info = self._parse_route_attribute(attr)

# In rust_action_parser.py - DO normalize for endpoints
# Add normalize=True when used for endpoint extraction
```

#### Verify

```bash
uv run pytest tests/unit/reverse_engineering/test_tree_sitter_rust.py::TestTreeSitterRustParser::test_extract_rocket_routes_from_ast -v
```

**Result**: 248/254 passing (97.6%)

---

### Task 1.3: Document Quick Wins (15 min)

Update `week8_FINAL_completion_plan.md` with Stage 1 completion status.

**Result**: Stage 1 Complete - 248/254 passing ✅

---

## 🔧 Stage 2: Actix Advanced Features (6-8 hours)

### Priority: **MEDIUM** | Difficulty: **HARD** | Impact: **+3 tests**

Implement advanced Actix-Web features using tree-sitter queries.

---

### Task 2.1: Actix Path Parameter Extraction (2-3 hours)

**Failing Test**: `test_extract_endpoints_with_path_parameters`

**Problem**: Not extracting parameters from handler function signatures

**Example**:
```rust
#[get("/api/users/{id}")]
pub async fn get_user(path: web::Path<i32>) -> HttpResponse { }
```

**Expected**:
```python
{
    "method": "GET",
    "path": "/api/users/{id}",
    "handler": "get_user",
    "parameters": [
        {"name": "path", "type": "web::Path<i32>"}
    ]
}
```

#### Implementation Plan

##### Step 1: Add parameter extraction to RustRoute dataclass

**File**: `src/reverse_engineering/tree_sitter_rust_parser.py`

```python
@dataclass
class RustRoute:
    """Represents an HTTP route."""

    method: str
    path: str
    handler: str
    framework: str = "actix"
    is_async: bool = False
    parameters: List[dict] = field(default_factory=list)  # NEW
```

##### Step 2: Implement `_extract_function_parameters()`

```python
def _extract_function_parameters(self, fn_node: Node) -> List[dict]:
    """Extract parameters from function signature."""
    parameters = []

    # Find parameters node
    for child in fn_node.children:
        if child.type == "parameters":
            for param_node in child.children:
                if param_node.type == "parameter":
                    param_info = self._parse_parameter(param_node)
                    if param_info:
                        parameters.append(param_info)

    return parameters

def _parse_parameter(self, param_node: Node) -> Optional[dict]:
    """Parse a single parameter (name: Type)."""
    param_name = None
    param_type = None

    for child in param_node.children:
        if child.type == "identifier":
            param_name = self._get_node_text(child)
        elif child.type == "type_identifier" or child.type.endswith("_type"):
            param_type = self._get_node_text(child)

    if param_name and param_name not in ["self", "&self", "&mut self"]:
        return {
            "name": param_name,
            "type": param_type or "unknown"
        }

    return None
```

##### Step 3: Update `_extract_route_from_function()`

```python
def _extract_route_from_function(self, fn_node: Node) -> Optional[RustRoute]:
    """Extract route information from a function with attributes."""
    fn_name = self._get_function_name(fn_node)
    is_async = self._is_async_function(fn_node)
    attributes = self._get_attributes(fn_node)
    parameters = self._extract_function_parameters(fn_node)  # NEW

    for attr in attributes:
        route_info = self._parse_route_attribute(attr, normalize=True)  # NEW: normalize for endpoints
        if route_info:
            method, path, framework = route_info
            return RustRoute(
                method=method,
                path=path,
                handler=fn_name,
                framework=framework,
                is_async=is_async,
                parameters=parameters,  # NEW
            )

    return None
```

##### Step 4: Update downstream code

**File**: `src/reverse_engineering/rust_parser.py`

Update `_convert_ts_routes_to_route_handlers()`:
```python
def _convert_ts_routes_to_route_handlers(self, ts_routes) -> List[RouteHandlerInfo]:
    """Convert tree-sitter RustRoute objects to RouteHandlerInfo objects."""
    routes = []
    for ts_route in ts_routes:
        route = RouteHandlerInfo(
            method=ts_route.method,
            path=ts_route.path,
            function_name=ts_route.handler,
            is_async=ts_route.is_async,
            return_type="",
            parameters=ts_route.parameters,  # NEW: pass through
        )
        routes.append(route)
    return routes
```

##### Step 5: Test

```bash
# Test single failing test
uv run pytest tests/unit/reverse_engineering/rust/test_action_parser_endpoints.py::TestRustActionParserEndpoints::test_extract_endpoints_with_path_parameters -v

# Run full suite
uv run pytest tests/unit/reverse_engineering/rust/test_action_parser_endpoints.py -v
```

**Expected**: Test passes, parameters extracted correctly

**Result**: 249/254 passing (97.8%)

---

### Task 2.2: Actix Guard Function Support (1-2 hours)

**Failing Test**: `test_actix_route_with_guard`

**Problem**: Not detecting routes with `.guard()` method chains

**Example**:
```rust
use actix_web::{get, guard, HttpResponse};

#[get("/admin")]
pub async fn admin_route() -> HttpResponse {
    HttpResponse::Ok().finish()
}
```

**Note**: Guards are typically in application config, not attributes

#### Implementation Plan

##### Step 1: Research guard patterns

Guards in Actix are usually applied at configuration level:
```rust
App::new()
    .service(
        web::resource("/admin")
            .route(web::get().to(admin_route).guard(guard::Header("admin", "true")))
    )
```

##### Step 2: Decision Point

**Option A**: Parse application configuration (complex)
**Option B**: Detect guard imports and mark routes (simple)

**Recommended**: Option B for now

##### Step 3: Add guard detection

```python
def _has_guard_annotation(self, fn_node: Node) -> bool:
    """Check if function has guard-related code."""
    # Look for guard imports in parent scope
    # Or check for guard-related attributes
    attributes = self._get_attributes(fn_node)
    for attr in attributes:
        attr_text = self._get_node_text(attr)
        if "guard" in attr_text.lower():
            return True
    return False
```

##### Step 4: Update RustRoute

```python
@dataclass
class RustRoute:
    """Represents an HTTP route."""

    method: str
    path: str
    handler: str
    framework: str = "actix"
    is_async: bool = False
    parameters: List[dict] = field(default_factory=list)
    has_guard: bool = False  # NEW
```

##### Step 5: Test

```bash
uv run pytest tests/unit/reverse_engineering/rust/test_action_parser_endpoints.py::TestRustActionParserEndpoints::test_actix_route_with_guard -v
```

**Expected**: Guard detection works (may need test adjustment)

**Result**: 250/254 passing (98.4%)

---

### Task 2.3: Actix Nested Scope Support (2-3 hours)

**Failing Test**: `test_actix_nested_scope`

**Problem**: Not handling nested `web::scope()` calls

**Example**:
```rust
App::new()
    .service(
        web::scope("/api")
            .service(
                web::scope("/users")
                    .service(web::resource("").route(web::get().to(list_users)))
                    .service(web::resource("/{id}").route(web::get().to(get_user)))
            )
    )
```

**Expected Paths**:
- `/api/users` (GET)
- `/api/users/{id}` (GET)

#### Implementation Plan

This is **complex** - requires parsing Rust application configuration code, which is beyond simple attribute parsing.

##### Step 1: Add scope detection

**File**: `src/reverse_engineering/tree_sitter_rust_parser.py`

```python
def extract_scope_hierarchy(self, ast: Node) -> List[dict]:
    """Extract web::scope() hierarchies from application config."""
    scopes = []

    # Find all call expressions
    calls = self._find_all(ast, "call_expression")

    for call in calls:
        if self._is_scope_call(call):
            scope_info = self._parse_scope(call)
            if scope_info:
                scopes.append(scope_info)

    return scopes

def _is_scope_call(self, call_node: Node) -> bool:
    """Check if call is web::scope()."""
    func_text = ""
    for child in call_node.children:
        if child.type in ["scoped_identifier", "field_expression"]:
            func_text = self._get_node_text(child)
            break

    return "scope" in func_text.lower()

def _parse_scope(self, scope_call: Node) -> Optional[dict]:
    """Parse a web::scope() call."""
    path = None
    nested_services = []

    # Extract scope path from arguments
    for child in scope_call.children:
        if child.type == "arguments":
            path = self._extract_string_literal(child)
        elif child.type == "call_expression":
            # Handle chained .service() calls
            if "service" in self._get_node_text(child):
                service = self._parse_service_call(child)
                if service:
                    nested_services.append(service)

    if path:
        return {
            "path": path,
            "services": nested_services
        }

    return None
```

##### Step 2: Implement scope path concatenation

```python
def _build_full_paths(self, scopes: List[dict]) -> List[dict]:
    """Build full paths by concatenating scope hierarchies."""
    routes = []

    def traverse(scope, prefix=""):
        full_prefix = prefix + scope["path"]

        for service in scope.get("services", []):
            if "path" in service:
                full_path = full_prefix + service["path"]
                routes.append({
                    "method": service.get("method", "GET"),
                    "path": full_path,
                    "handler": service.get("handler", "unknown")
                })

            # Handle nested scopes
            if "nested_scope" in service:
                traverse(service["nested_scope"], full_prefix)

    for scope in scopes:
        traverse(scope)

    return routes
```

##### Step 3: Integrate with main extraction

```python
def extract_routes(self, ast: Node) -> List[RustRoute]:
    """Extract routes from Rust code."""
    routes = []

    # Extract attribute-based routes (existing)
    attr_routes = self._extract_attribute_routes(ast)
    routes.extend(attr_routes)

    # Extract scope-based routes (NEW)
    scopes = self.extract_scope_hierarchy(ast)
    scope_routes = self._build_full_paths(scopes)

    for route_info in scope_routes:
        routes.append(RustRoute(
            method=route_info["method"],
            path=route_info["path"],
            handler=route_info["handler"],
            framework="actix",
            is_async=False,  # TODO: detect from handler
        ))

    return routes
```

##### Step 4: Test

```bash
uv run pytest tests/unit/reverse_engineering/rust/test_action_parser_endpoints.py::TestRustActionParserEndpoints::test_actix_nested_scope -v
```

**Expected**: Nested scopes properly concatenated

**Result**: 251/254 passing (98.8%)

**Time Checkpoint**: ~6-8 hours elapsed

---

## 🌐 Stage 3: Other Framework Support (6-8 hours)

### Priority: **MEDIUM** | Difficulty: **HARD** | Impact: **+3 tests**

---

### Task 3.1: Axum State Management (2-3 hours)

**Failing Test**: `test_axum_handler_with_state`

**Problem**: Not detecting Axum `Router::new().route()` chains

**Example**:
```rust
use axum::{Router, routing::get};

fn routes() -> Router {
    Router::new()
        .route("/users", get(list_users))
        .route("/users/:id", get(get_user))
}
```

#### Implementation Plan

##### Step 1: Add Axum route detection

Already exists at line 359-370 in `tree_sitter_rust_parser.py`, but may need enhancement.

##### Step 2: Enhance `_extract_axum_routes()`

```python
def _extract_axum_routes(self, ast: Node) -> List[RustRoute]:
    """Extract Axum routes from Router method chains."""
    routes = []

    # Find Router::new() chains
    call_exprs = self._find_all(ast, "call_expression")

    for call_expr in call_exprs:
        # Look for Router::new()
        if self._is_router_new(call_expr):
            # Traverse method chain
            chain_routes = self._extract_route_chain(call_expr.parent)
            routes.extend(chain_routes)

    return routes

def _is_router_new(self, call_expr: Node) -> bool:
    """Check if call is Router::new()."""
    func_text = self._get_function_call_name(call_expr)
    return "Router" in func_text and "new" in func_text

def _extract_route_chain(self, chain_node: Node) -> List[RustRoute]:
    """Extract all .route() calls from method chain."""
    routes = []

    # Walk up the chain
    current = chain_node
    while current:
        if current.type == "call_expression":
            if self._is_route_method(current):
                route = self._parse_axum_route(current)
                if route:
                    routes.append(route)

        # Check next in chain
        if current.parent and current.parent.type == "call_expression":
            current = current.parent
        else:
            break

    return routes

def _is_route_method(self, call_expr: Node) -> bool:
    """Check if call is .route() method."""
    for child in call_expr.children:
        if child.type == "field_expression":
            text = self._get_node_text(child)
            if text.endswith(".route"):
                return True
    return False

def _parse_axum_route(self, route_call: Node) -> Optional[RustRoute]:
    """Parse .route(path, handler) call."""
    path = None
    handler = None
    method = "GET"  # Default

    # Extract arguments: .route("/path", get(handler))
    for child in route_call.children:
        if child.type == "arguments":
            args = list(child.children)
            if len(args) >= 2:
                # First arg is path
                path = self._extract_string_literal(args[0])

                # Second arg is method + handler: get(handler)
                method_call = args[1]
                if method_call.type == "call_expression":
                    method, handler = self._extract_axum_method_and_handler(method_call)

    if path and handler:
        # Normalize Axum :param to {param}
        path = path.replace(":", "{").replace("}", "}")

        return RustRoute(
            method=method,
            path=path,
            handler=handler,
            framework="axum",
            is_async=True,  # Axum handlers are typically async
        )

    return None
```

##### Step 3: Test

```bash
uv run pytest tests/unit/reverse_engineering/rust/test_action_parser_endpoints.py::TestRustActionParserEndpoints::test_axum_handler_with_state -v
```

**Expected**: Axum routes extracted from Router chains

**Result**: 252/254 passing (99.2%)

---

### Task 3.2: Warp Filter Chain Support (2-3 hours)

**Failing Test**: `test_warp_filter_chain`

**Problem**: Not parsing Warp filter composition

**Example**:
```rust
use warp::Filter;

let routes = warp::path("users")
    .and(warp::get())
    .map(|| "users list");
```

#### Implementation Plan

##### Step 1: Add Warp detection

```python
def _extract_warp_filters(self, ast: Node) -> List[RustRoute]:
    """Extract routes from Warp filter chains."""
    routes = []

    # Find all expressions that look like filter chains
    # warp::path("...").and(warp::get())

    call_exprs = self._find_all(ast, "call_expression")

    for call_expr in call_exprs:
        if self._is_warp_path(call_expr):
            filter_route = self._parse_warp_filter_chain(call_expr)
            if filter_route:
                routes.append(filter_route)

    return routes

def _is_warp_path(self, call_expr: Node) -> bool:
    """Check if call is warp::path()."""
    func_text = self._get_function_call_name(call_expr)
    return "warp" in func_text and "path" in func_text

def _parse_warp_filter_chain(self, path_call: Node) -> Optional[RustRoute]:
    """Parse a Warp filter chain starting from path()."""
    path = self._extract_string_literal(path_call)
    method = None
    handler = None

    # Walk the method chain (.and(), .map(), etc.)
    current = path_call.parent
    while current:
        if current.type == "call_expression":
            method_name = self._get_method_name(current)

            if method_name == "and":
                # Check for method filter: .and(warp::get())
                method = self._extract_warp_method(current)

            elif method_name == "map":
                # Extract handler from .map(|| handler)
                handler = self._extract_warp_handler(current)

        # Move up chain
        if current.parent:
            current = current.parent
        else:
            break

    if path:
        return RustRoute(
            method=method or "GET",
            path=f"/{path}",
            handler=handler or "warp_handler",
            framework="warp",
            is_async=False,
        )

    return None

def _extract_warp_method(self, and_call: Node) -> Optional[str]:
    """Extract HTTP method from .and(warp::get()) call."""
    for child in and_call.children:
        if child.type == "arguments":
            arg_text = self._get_node_text(child)
            if "get" in arg_text:
                return "GET"
            elif "post" in arg_text:
                return "POST"
            elif "put" in arg_text:
                return "PUT"
            elif "delete" in arg_text:
                return "DELETE"
    return None

def _extract_warp_handler(self, map_call: Node) -> Optional[str]:
    """Extract handler from .map() call."""
    for child in map_call.children:
        if child.type == "arguments":
            # Try to extract closure or function name
            closure = child.children[0] if child.children else None
            if closure:
                return "warp_closure"  # Simplified
    return None
```

##### Step 2: Integrate

Add to `extract_routes()`:
```python
# Extract Warp filter chains
warp_routes = self._extract_warp_filters(ast)
routes.extend(warp_routes)
```

##### Step 3: Test

```bash
uv run pytest tests/unit/reverse_engineering/rust/test_action_parser_endpoints.py::TestRustActionParserEndpoints::test_warp_filter_chain -v
```

**Expected**: Basic Warp filters detected

**Result**: 253/254 passing (99.6%)

---

### Task 3.3: Tide Endpoint Support (2-3 hours)

**Failing Test**: `test_tide_endpoint`

**Problem**: Not detecting Tide `at()` method chains

**Example**:
```rust
use tide::Request;

let mut app = tide::new();
app.at("/users").get(list_users);
app.at("/users/:id").get(get_user);
```

#### Implementation Plan

##### Step 1: Add Tide detection

```python
def _extract_tide_routes(self, ast: Node) -> List[RustRoute]:
    """Extract routes from Tide .at() method chains."""
    routes = []

    # Find all .at() calls
    call_exprs = self._find_all(ast, "call_expression")

    for call_expr in call_exprs:
        if self._is_tide_at(call_expr):
            tide_route = self._parse_tide_route(call_expr)
            if tide_route:
                routes.append(tide_route)

    return routes

def _is_tide_at(self, call_expr: Node) -> bool:
    """Check if call is .at() method."""
    for child in call_expr.children:
        if child.type == "field_expression":
            text = self._get_node_text(child)
            if ".at" in text:
                return True
    return False

def _parse_tide_route(self, at_call: Node) -> Optional[RustRoute]:
    """Parse .at(path).get(handler) chain."""
    path = self._extract_string_literal(at_call)
    method = None
    handler = None

    # Check for chained method call: .at("/path").get(handler)
    parent = at_call.parent
    if parent and parent.type == "call_expression":
        method_name = self._get_method_name(parent)

        if method_name in ["get", "post", "put", "delete"]:
            method = method_name.upper()
            handler = self._extract_tide_handler(parent)

    if path and method:
        # Normalize Tide :param to {param}
        path = path.replace(":", "{").replace("}", "}")

        return RustRoute(
            method=method,
            path=path,
            handler=handler or "tide_handler",
            framework="tide",
            is_async=True,
        )

    return None

def _extract_tide_handler(self, method_call: Node) -> Optional[str]:
    """Extract handler from .get(handler) call."""
    for child in method_call.children:
        if child.type == "arguments":
            # Extract first argument (handler function)
            if child.children:
                handler_node = child.children[0]
                return self._get_node_text(handler_node)
    return None
```

##### Step 2: Integrate

Add to `extract_routes()`:
```python
# Extract Tide routes
tide_routes = self._extract_tide_routes(ast)
routes.extend(tide_routes)
```

##### Step 3: Test

```bash
uv run pytest tests/unit/reverse_engineering/rust/test_action_parser_endpoints.py::TestRustActionParserEndpoints::test_tide_endpoint -v
```

**Expected**: Tide routes detected from .at() chains

**Result**: 254/254 passing (100%) 🎉

**Time Checkpoint**: ~12-16 hours elapsed

---

## 🧹 Stage 4: Code Polish & TODOs (4-6 hours)

### Priority: **LOW** | Difficulty: **MEDIUM** | Impact: **Code Quality**

These don't affect tests but improve code quality.

---

### Task 4.1: SQL CTE & Expression Parsing (2 hours)

**File**: `src/reverse_engineering/ast_to_specql_mapper.py`

**TODO 1** (Line 428): More robust CTE parsing
**TODO 2** (Line 503): More robust expression extraction
**TODO 3** (Line 513): Type mapping implementation

#### Implementation

##### Robust CTE Parsing

```python
def _parse_cte_robust(self, cte_node: dict) -> dict:
    """More robust CTE (Common Table Expression) parsing."""
    cte_info = {
        "name": cte_node.get("ctename"),
        "columns": [],
        "query": None,
        "recursive": False,
        "materialized": None,
    }

    # Handle column list
    if "aliascolnames" in cte_node:
        cte_info["columns"] = cte_node["aliascolnames"]

    # Parse query
    if "ctequery" in cte_node:
        cte_info["query"] = self._parse_select_stmt(cte_node["ctequery"])

    # Check if recursive
    if "cterecursive" in cte_node:
        cte_info["recursive"] = cte_node["cterecursive"]

    # Check materialization
    if "ctematerialized" in cte_node:
        if cte_node["ctematerialized"] == 1:
            cte_info["materialized"] = "materialized"
        elif cte_node["ctematerialized"] == 2:
            cte_info["materialized"] = "not_materialized"

    return cte_info
```

##### Robust Expression Extraction

```python
def _extract_expression_robust(self, expr_node: dict) -> str:
    """More robust expression extraction with full type support."""
    if not expr_node:
        return ""

    expr_type = list(expr_node.keys())[0]
    expr_data = expr_node[expr_type]

    handlers = {
        'ColumnRef': lambda: self._extract_column_ref(expr_data),
        'A_Const': lambda: self._extract_constant(expr_data),
        'A_Expr': lambda: self._extract_a_expr(expr_data),
        'FuncCall': lambda: self._extract_func_call(expr_data),
        'BoolExpr': lambda: self._extract_bool_expr(expr_data),
        'CaseExpr': lambda: self._extract_case_expr(expr_data),
        'SubLink': lambda: self._extract_subquery(expr_data),
        'CoalesceExpr': lambda: self._extract_coalesce(expr_data),
        'NullTest': lambda: self._extract_null_test(expr_data),
        'TypeCast': lambda: self._extract_type_cast(expr_data),
    }

    handler = handlers.get(expr_type)
    if handler:
        return handler()

    # Fallback: convert to string
    return str(expr_data)

def _extract_subquery(self, sublink_data: dict) -> str:
    """Extract subquery expression."""
    if "subselect" in sublink_data:
        subquery = self._parse_select_stmt(sublink_data["subselect"])
        return f"({subquery})"
    return "subquery"

def _extract_coalesce(self, coalesce_data: dict) -> str:
    """Extract COALESCE expression."""
    args = []
    if "args" in coalesce_data:
        for arg in coalesce_data["args"]:
            args.append(self._extract_expression_robust(arg))
    return f"COALESCE({', '.join(args)})"

def _extract_null_test(self, null_test_data: dict) -> str:
    """Extract IS NULL / IS NOT NULL test."""
    arg = self._extract_expression_robust(null_test_data.get("arg", {}))
    if null_test_data.get("nulltesttype") == 1:
        return f"{arg} IS NOT NULL"
    return f"{arg} IS NULL"

def _extract_type_cast(self, cast_data: dict) -> str:
    """Extract type cast expression."""
    arg = self._extract_expression_robust(cast_data.get("arg", {}))
    type_name = cast_data.get("typeName", {})
    target_type = self._extract_type_name(type_name)
    return f"{arg}::{target_type}"
```

##### Type Mapping Implementation

```python
def _map_pg_type_to_specql(self, pg_type: str) -> str:
    """Map PostgreSQL types to SpecQL types."""
    type_mapping = {
        # Numeric types
        "integer": "integer",
        "int": "integer",
        "int4": "integer",
        "bigint": "integer",
        "int8": "integer",
        "smallint": "integer",
        "int2": "integer",
        "numeric": "decimal",
        "decimal": "decimal",
        "real": "decimal",
        "double precision": "decimal",
        "float4": "decimal",
        "float8": "decimal",

        # String types
        "text": "text",
        "varchar": "text",
        "character varying": "text",
        "char": "text",
        "character": "text",

        # Boolean
        "boolean": "boolean",
        "bool": "boolean",

        # Date/Time
        "timestamp": "timestamp",
        "timestamptz": "timestamp",
        "timestamp with time zone": "timestamp",
        "timestamp without time zone": "timestamp",
        "date": "date",
        "time": "time",
        "timetz": "time",

        # JSON
        "json": "json",
        "jsonb": "json",

        # UUID
        "uuid": "text",  # SpecQL treats UUIDs as text

        # Arrays
        "integer[]": "list(integer)",
        "text[]": "list(text)",
        "varchar[]": "list(text)",
    }

    # Handle array types
    if pg_type.endswith("[]"):
        base_type = pg_type[:-2]
        mapped_base = type_mapping.get(base_type, "text")
        return f"list({mapped_base})"

    return type_mapping.get(pg_type.lower(), "text")
```

**Test**: No specific tests, but improves SQL parsing reliability

---

### Task 4.2: Rust Parser TODOs (2 hours)

**File**: `src/reverse_engineering/rust_parser.py`

**TODO 4** (Line 225): Enum extraction
**TODO 5** (Line 226): Diesel table extraction
**TODO 6** (Line 227): Diesel derive extraction

#### Implementation

##### Enum Extraction

```python
def extract_enums(self, content: str) -> List[dict]:
    """Extract enum definitions from Rust code."""
    enums = []

    # Pattern for Rust enums
    pattern = r'(?:#\[derive\([^\]]+\)\]\s*)?pub\s+enum\s+(\w+)\s*\{([^}]+)\}'

    for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
        enum_name = match.group(1)
        variants_text = match.group(2)

        # Parse variants
        variants = []
        for line in variants_text.split(','):
            line = line.strip()
            if line and not line.startswith('//'):
                # Handle simple variants and variants with data
                variant_name = line.split('(')[0].split('{')[0].strip()
                if variant_name:
                    variants.append(variant_name)

        enums.append({
            "name": enum_name,
            "values": variants
        })

    return enums
```

##### Diesel Table Extraction

```python
def extract_diesel_tables(self, content: str) -> List[dict]:
    """Extract Diesel table! macros."""
    tables = []

    # Pattern for table! macro
    pattern = r'table!\s*\{\s*(\w+)\s*\(([^)]+)\)\s*\{([^}]+)\}\s*\}'

    for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
        table_name = match.group(1)
        pk_column = match.group(2).strip()
        columns_text = match.group(3)

        # Parse columns
        columns = []
        for line in columns_text.split('\n'):
            line = line.strip()
            if '->' in line:
                # Format: column_name -> Type,
                parts = line.split('->')
                col_name = parts[0].strip()
                col_type = parts[1].strip(' ,')
                columns.append({
                    "name": col_name,
                    "type": col_type,
                    "primary_key": col_name == pk_column
                })

        tables.append({
            "name": table_name,
            "primary_key": pk_column,
            "columns": columns
        })

    return tables
```

##### Diesel Derive Extraction

```python
def extract_diesel_derives(self, content: str) -> List[dict]:
    """Extract Diesel derive macros from structs."""
    derives = []

    # Pattern for structs with Diesel derives
    pattern = r'#\[derive\(([^]]+Queryable[^]]*)\)\]\s*(?:pub\s+)?struct\s+(\w+)'

    for match in re.finditer(pattern, content):
        derive_list = match.group(1)
        struct_name = match.group(2)

        # Parse derives
        derive_traits = [d.strip() for d in derive_list.split(',')]

        diesel_traits = [t for t in derive_traits if 'Queryable' in t or 'Insertable' in t or 'AsChangeset' in t]

        if diesel_traits:
            derives.append({
                "struct": struct_name,
                "traits": diesel_traits
            })

    return derives
```

**Test**: Update `parse_file()` to use these methods

---

### Task 4.3: Rust Action Parser TODOs (1 hour)

**File**: `src/reverse_engineering/rust_action_parser.py`

**TODO 7** (Line 87): Endpoint extraction from AST
**TODO 8** (Line 207): Mapping logic

These are already partially implemented via earlier work. Mark as complete or enhance.

---

### Task 4.4: Documentation & Testing (1 hour)

1. Update all docstrings
2. Add type hints where missing
3. Run full test suite
4. Update Week 8 documentation with 100% completion status

```bash
# Final verification
uv run pytest tests/unit/reverse_engineering/ tests/integration/reverse_engineering/ -v

# Should show: 254 passed
```

---

## 📊 Timeline Summary

| Stage | Duration | Result |
|-------|----------|--------|
| Stage 1: Quick Wins | 1 hour | 248/254 (97.6%) |
| Stage 2: Actix Advanced | 6-8 hours | 251/254 (98.8%) |
| Stage 3: Other Frameworks | 6-8 hours | 254/254 (100%) ✅ |
| Stage 4: Code Polish | 4-6 hours | 254/254 + Quality ✨ |
| **Total** | **17-23 hours** | **100% Complete** |

---

## ✅ Success Criteria

1. ✅ All 254 tests passing (100%)
2. ✅ No skipped tests
3. ✅ No empty test stubs
4. ✅ All TODOs addressed or documented
5. ✅ Framework support complete:
   - TypeScript (Express, Fastify, Next.js)
   - Rust (Actix, Rocket, Axum, Warp, Tide)
   - Python (FastAPI, Flask, Django)
   - Java (Spring Boot)
6. ✅ Documentation updated
7. ✅ Code quality high (type hints, docstrings)

---

## 🎯 Recommended Approach

### Option 1: Sequential (17-23 hours)
Work through Stages 1-4 in order for complete implementation.

### Option 2: Parallel (12-16 hours with 2 devs)
- Dev 1: Stages 1 & 2 (Quick wins + Actix)
- Dev 2: Stage 3 (Other frameworks)
- Together: Stage 4 (Polish)

### Option 3: Pragmatic (1 hour + Documentation)
- Complete Stage 1 only (97.6%)
- Document remaining 6 tests as "Advanced Features - Future Work"
- Ship with high confidence

---

## 📝 Notes

- **Tree-sitter complexity**: Framework-specific extraction requires deep understanding of each framework's patterns
- **Maintenance**: Advanced features will need updates when frameworks change
- **Testing**: Each task should have its own test run to verify before moving on
- **Commits**: Create commits after each stage completion for clean history

---

**Generated**: 2025-11-18
**Author**: Claude Code
**Status**: Ready for Implementation
