"""
Tree-sitter Rust AST Parser Tests

Test tree-sitter based Rust parsing for complex macros and structures.
"""

from reverse_engineering.tree_sitter_rust_parser import TreeSitterRustParser


class TestTreeSitterRustParser:
    """Test tree-sitter Rust AST parsing"""

    def test_parse_diesel_table_macro(self):
        """Test parsing Diesel table! macro"""
        code = """
        diesel::table! {
            contacts (id) {
                id -> Integer,
                email -> Varchar,
                status -> Varchar,
                created_at -> Timestamp,
            }
        }
        """

        parser = TreeSitterRustParser()
        ast = parser.parse(code)

        assert ast is not None
        assert parser.extract_table_name(ast) == "contacts"
        assert len(parser.extract_columns(ast)) == 4
        assert "email" in [col.name for col in parser.extract_columns(ast)]

    def test_extract_function_signatures(self):
        """Test extracting function signatures from AST"""
        code = """
        pub async fn create_contact(
            db: web::Data<Database>,
            contact: web::Json<ContactDTO>
        ) -> Result<HttpResponse, Error> {
            // Implementation
            Ok(HttpResponse::Created().json(contact))
        }
        """

        parser = TreeSitterRustParser()
        ast = parser.parse(code)

        functions = parser.extract_functions(ast)

        assert len(functions) == 1
        assert functions[0].name == "create_contact"
        assert functions[0].is_public
        assert functions[0].is_async
        assert len(functions[0].parameters) == 2

    def test_extract_derive_macros(self):
        """Test extracting derive macros from structs"""
        code = """
        #[derive(Debug, Clone, Serialize, Deserialize)]
        #[diesel(table_name = contacts)]
        pub struct Contact {
            pub id: i32,
            pub email: String,
            pub status: String,
        }
        """

        parser = TreeSitterRustParser()
        ast = parser.parse(code)

        structs = parser.extract_structs(ast)

        assert len(structs) == 1
        assert "Serialize" in structs[0].derives
        assert "Deserialize" in structs[0].derives
        assert structs[0].attributes.get("table_name") == "contacts"

    def test_extract_actix_routes_from_ast(self):
        """Extract Actix-web routes via AST traversal."""
        code = """
        use actix_web::{get, post, web, HttpResponse};

        #[get("/users/{id}")]
        pub async fn get_user(id: web::Path<i32>) -> HttpResponse {
            HttpResponse::Ok().finish()
        }

        #[post("/users")]
        async fn create_user(body: web::Json<User>) -> HttpResponse {
            HttpResponse::Created().finish()
        }
        """

        parser = TreeSitterRustParser()
        ast = parser.parse(code)
        routes = parser.extract_routes(ast)

        assert len(routes) == 2

    def test_extract_rocket_routes_from_ast(self):
        """Extract Rocket routes via AST traversal."""
        code = """
        use rocket::serde::{Deserialize, json::Json};

        #[get("/users/<id>")]
        pub fn get_user(id: i32) -> Json<User> {
            Json(User { id, name: "test".to_string() })
        }

        #[post("/users", data = "<user>")]
        pub fn create_user(user: Json<User>) -> Json<User> {
            user
        }
        """

        parser = TreeSitterRustParser()
        ast = parser.parse(code)
        routes = parser.extract_routes(ast)

        assert len(routes) == 2
        assert routes[0].method == "GET"
        assert routes[0].path == "/users/<id>"
        assert routes[0].handler == "get_user"
        assert routes[0].framework == "rocket"
        assert not routes[0].is_async

        assert routes[1].method == "POST"
        assert routes[1].path == "/users"
        assert routes[1].handler == "create_user"
        assert routes[1].framework == "rocket"
        assert not routes[1].is_async

    # def test_extract_axum_routes_from_ast(self):
    #     """Extract Axum routes via AST traversal."""
    #     # TODO: Implement Axum route extraction (complex method chaining)
    #     pass

    def test_extract_impl_blocks_from_ast(self):
        """Extract impl blocks via AST traversal."""
        code = """
        struct User {
            id: i32,
            name: String,
        }

        impl User {
            fn new(id: i32, name: String) -> Self {
                User { id, name }
            }

            fn get_id(&self) -> i32 {
                self.id
            }
        }
        """

        parser = TreeSitterRustParser()
        ast = parser.parse(code)
        impl_blocks = parser.extract_impl_blocks(ast)

        assert len(impl_blocks) == 1
        assert impl_blocks[0].target_type == "User"
        assert len(impl_blocks[0].methods) == 2
        assert impl_blocks[0].methods[0].name == "new"
        assert impl_blocks[0].methods[1].name == "get_id"

    def test_extract_trait_impl_blocks_from_ast(self):
        """Extract trait implementation blocks."""
        code = """
        trait Display {
            fn display(&self) -> String;
        }

        impl Display for User {
            fn display(&self) -> String {
                format!("User: {}", self.name)
            }
        }
        """

        parser = TreeSitterRustParser()
        ast = parser.parse(code)
        impl_blocks = parser.extract_impl_blocks(ast)

        assert len(impl_blocks) == 1
        assert impl_blocks[0].target_type == "User"
        assert impl_blocks[0].trait_name == "Display"
        assert len(impl_blocks[0].methods) == 1
        assert impl_blocks[0].methods[0].name == "display"

    def test_extract_routes_with_comments(self):
        """Handle routes with comments."""
        code = """
        // User endpoint
        #[get("/users/{id}")]  // Get user by ID
        pub async fn get_user(id: i32) -> HttpResponse {
            HttpResponse::Ok().finish()
        }
        """

        parser = TreeSitterRustParser()
        ast = parser.parse(code)
        routes = parser.extract_routes(ast)

        assert len(routes) == 1

    def test_rust_action_parser_integration(self):
        """Test RustActionParser integration with tree-sitter"""
        from reverse_engineering.rust_action_parser import RustActionParser

        code = """
        pub async fn create_contact() -> Result<(), Error> {
            Ok(())
        }

        #[derive(Serialize)]
        pub struct Contact {
            pub id: i32,
        }
        """

        # Test with tree-sitter enabled
        parser = RustActionParser(use_tree_sitter=True)

        # Create a temporary file for testing
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            result = parser.parse_file(temp_file)
            assert result.parser_used == "tree-sitter"
            assert len(result.functions) == 1
            assert len(result.structs) == 1
        finally:
            import os

            os.unlink(temp_file)

    def test_rust_parser_performance_comparison(self):
        """Benchmark tree-sitter vs regex performance."""
        import time

        from reverse_engineering.rust_parser import RustParser

        # Create a moderately complex Rust file for testing
        code = """
        use actix_web::{get, post, web, HttpResponse, Result};
        use serde::{Deserialize, Serialize};

        #[derive(Serialize, Deserialize)]
        pub struct User {
            pub id: i32,
            pub name: String,
            pub email: String,
        }

        #[get("/users/{id}")]
        pub async fn get_user(path: web::Path<i32>) -> Result<HttpResponse> {
            Ok(HttpResponse::Ok().json(User {
                id: *path,
                name: "Test".to_string(),
                email: "test@example.com".to_string(),
            }))
        }

        #[post("/users")]
        pub async fn create_user(user: web::Json<User>) -> Result<HttpResponse> {
            Ok(HttpResponse::Created().json(user))
        }

        impl User {
            pub fn new(id: i32, name: String, email: String) -> Self {
                User { id, name, email }
            }

            pub fn get_id(&self) -> i32 {
                self.id
            }

            pub fn get_name(&self) -> String {
                self.name.clone()
            }
        }
        """

        parser = RustParser()

        # Benchmark tree-sitter parsing
        start_time = time.time()
        iterations = 10
        structs = []
        routes = []
        impl_blocks = []

        for _ in range(iterations):
            ast = parser.ts_parser.parse(code)
            if ast:
                structs = parser.ts_parser.extract_structs(ast)
                routes = parser.ts_parser.extract_routes(ast)
                impl_blocks = parser.ts_parser.extract_impl_blocks(ast)
        tree_sitter_time = (time.time() - start_time) / iterations

        # Verify tree-sitter extracted the expected data
        assert len(structs) == 1
        assert len(routes) == 2
        assert len(impl_blocks) == 1

        # Tree-sitter should be reasonably fast (< 0.1s per parse)
        assert tree_sitter_time < 0.1, f"Tree-sitter too slow: {tree_sitter_time:.3f}s"

        print(f"Tree-sitter parsing time: {tree_sitter_time:.4f}s per file")
