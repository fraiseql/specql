"""
Rust Generator Orchestrator

Coordinates the complete Rust code generation pipeline.
"""

from pathlib import Path
from typing import List
from src.core.ast_models import Entity
from src.generators.rust.diesel_table_generator import DieselTableGenerator
from src.generators.rust.model_generator import RustModelGenerator
from src.generators.rust.query_generator import RustQueryGenerator
from src.generators.rust.handler_generator import RustHandlerGenerator


class RustGeneratorOrchestrator:
    """
    Orchestrates complete Rust backend code generation

    Coordinates all Rust generators to create a complete, compilable
    Rust project with Diesel ORM, Actix Web handlers, and proper module structure.

    Generated structure:
        src/
        ├── schema.rs          # Diesel table definitions
        ├── models.rs          # Queryable/Insertable/AsChangeset structs
        ├── queries.rs         # CRUD query builders
        ├── handlers/          # HTTP handlers (optional)
        │   └── contact.rs
        └── routes.rs          # Route configuration (optional)
        Cargo.toml            # Dependencies
        main.rs               # Application entry point
    """

    def __init__(self):
        self.table_generator = DieselTableGenerator()
        self.model_generator = RustModelGenerator()
        self.query_generator = RustQueryGenerator()
        self.handler_generator = RustHandlerGenerator()

    def generate(
        self,
        entity_files: List[Path],
        output_dir: Path,
        with_handlers: bool = False,
        with_routes: bool = False,
        **options,
    ) -> None:
        """
        Generate complete Rust backend from SpecQL entities

        Args:
            entity_files: List of paths to SpecQL YAML files
            output_dir: Directory to write generated code
            with_handlers: Generate Actix Web handlers
            with_routes: Generate route configuration
            **options: Additional generation options
        """
        # Parse entities
        entities = self._parse_entities(entity_files)

        # Create output directory structure
        output_dir.mkdir(parents=True, exist_ok=True)
        src_dir = output_dir / "src"
        src_dir.mkdir(exist_ok=True)

        # Generate core files
        self._generate_schema_file(entities, src_dir)
        self._generate_models_file(entities, src_dir)
        self._generate_queries_file(entities, src_dir)

        # Generate optional files
        if with_handlers:
            self._generate_handlers(entities, src_dir)

        if with_routes:
            self._generate_routes(entities, src_dir)

        # Generate supporting files
        self._generate_cargo_toml(output_dir)
        self._generate_main_rs(src_dir)
        self._generate_lib_rs(src_dir)

    def _parse_entities(self, entity_files: List[Path]) -> List[Entity]:
        """Parse SpecQL entity files"""
        from src.core.specql_parser import SpecQLParser
        from src.cli.generate import convert_entity_definition_to_entity

        parser = SpecQLParser()
        entities = []

        for entity_file in entity_files:
            yaml_content = entity_file.read_text()
            entity_def = parser.parse(yaml_content)
            entity = convert_entity_definition_to_entity(entity_def)
            entities.append(entity)

        return entities

    def _generate_schema_file(self, entities: List[Entity], src_dir: Path) -> None:
        """Generate schema.rs with Diesel table definitions"""
        schema_content = self.table_generator.generate_schema_file(entities)
        (src_dir / "schema.rs").write_text(schema_content)

    def _generate_models_file(self, entities: List[Entity], src_dir: Path) -> None:
        """Generate models.rs with Diesel model structs"""
        # For now, generate models for the first entity
        # TODO: Support multiple entities in one file or separate files
        if entities:
            models_content = self.model_generator.generate_all_models(entities[0])
            (src_dir / "models.rs").write_text(models_content)

    def _generate_queries_file(self, entities: List[Entity], src_dir: Path) -> None:
        """Generate queries.rs with CRUD query builders"""
        # For now, generate queries for the first entity
        if entities:
            queries_content = self.query_generator.generate_queries_file(entities[0])
            (src_dir / "queries.rs").write_text(queries_content)

    def _generate_handlers(self, entities: List[Entity], src_dir: Path) -> None:
        """Generate HTTP handlers"""
        handlers_dir = src_dir / "handlers"
        handlers_dir.mkdir(exist_ok=True)

        for entity in entities:
            snake_name = entity.name.lower()
            handler_content = self.handler_generator.generate_handlers_file(entity)
            (handlers_dir / f"{snake_name}.rs").write_text(handler_content)

    def _generate_routes(self, entities: List[Entity], src_dir: Path) -> None:
        """Generate route configuration"""
        routes_content = self._generate_routes_file_content(entities)
        (src_dir / "routes.rs").write_text(routes_content)

    def _generate_routes_file_content(self, entities: List[Entity]) -> str:
        """Generate complete routes.rs file"""
        parts = [
            "// Generated by SpecQL",
            "// DO NOT EDIT MANUALLY",
            "",
            "// Route configuration for all entities",
            "",
            "use actix_web::web;",
        ]

        # Import handlers
        for entity in entities:
            snake_name = entity.name.lower()
            parts.append(f"use super::handlers::{snake_name}::*;")

        parts.append("")

        # Generate route configuration functions
        for entity in entities:
            route_config = self.handler_generator.generate_route_config(entity)
            parts.append(route_config)
            parts.append("")

        # Generate main route configuration
        parts.append("/// Configure all routes for the application")
        parts.append("pub fn configure_all_routes(cfg: &mut web::ServiceConfig) {")

        for entity in entities:
            snake_name = entity.name.lower()
            parts.append(f"    configure_{snake_name}_routes(cfg);")

        parts.append("}")

        return "\n".join(parts)

    def _generate_cargo_toml(self, output_dir: Path) -> None:
        """Generate Cargo.toml with required dependencies"""
        cargo_content = """[package]
name = "specql-backend"
version = "0.1.0"
edition = "2021"

[dependencies]
actix-web = "4.0"
actix-rt = "2.7"
diesel = { version = "2.0", features = ["postgres", "r2d2", "chrono", "uuid", "serde_json"] }
bigdecimal = "0.3"
chrono = { version = "0.4", features = ["serde"] }
uuid = { version = "1.0", features = ["serde", "v4"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
r2d2 = "0.8"
dotenvy = "0.15"
"""
        (output_dir / "Cargo.toml").write_text(cargo_content)

    def _generate_main_rs(self, src_dir: Path) -> None:
        """Generate main.rs application entry point"""
        main_content = """// Generated by SpecQL
// DO NOT EDIT MANUALLY

use actix_web::{web, App, HttpServer};
use diesel::r2d2::{self, ConnectionManager};
use diesel::PgConnection;
use dotenvy::dotenv;
use std::env;

mod schema;
mod models;
mod queries;
mod handlers;
mod routes;

pub type DbPool = r2d2::Pool<ConnectionManager<PgConnection>>;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    dotenv().ok();

    let database_url = env::var("DATABASE_URL")
        .expect("DATABASE_URL must be set");

    let manager = ConnectionManager::<PgConnection>::new(database_url);
    let pool: DbPool = r2d2::Pool::builder()
        .build(manager)
        .expect("Failed to create pool.");

    HttpServer::new(move || {
        App::new()
            .app_data(web::Data::new(pool.clone()))
            .configure(routes::configure_all_routes)
    })
    .bind("127.0.0.1:8080")?
    .run()
    .await
}
"""
        (src_dir / "main.rs").write_text(main_content)

    def _generate_lib_rs(self, src_dir: Path) -> None:
        """Generate lib.rs module declarations"""
        lib_content = """// Generated by SpecQL
// DO NOT EDIT MANUALLY

pub mod schema;
pub mod models;
pub mod queries;
pub mod handlers;
pub mod routes;
"""
        (src_dir / "lib.rs").write_text(lib_content)
