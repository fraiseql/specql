"""
Rust Handler Generator

Generates Actix Web HTTP handlers for REST API endpoints.
"""

from src.core.ast_models import Entity
from src.generators.naming_utils import to_snake_case, to_pascal_case


class RustHandlerGenerator:
    """
    Generates Actix Web HTTP handlers

    Creates RESTful API handlers that call the query functions
    and handle HTTP requests/responses appropriately.

    Example output:
        pub async fn get_contact(
            pool: web::Data<DbPool>,
            contact_id: web::Path<Uuid>
        ) -> Result<HttpResponse> {
            let mut conn = pool.get().expect("couldn't get db connection from pool");

            let contact = web::block(move || {
                ContactQueries::find_by_id(&mut conn, *contact_id)
            })
            .await?
            .map_err(|_| HttpResponse::NotFound().finish())?;

            Ok(HttpResponse::Ok().json(contact))
        }
    """

    def generate_get_handler(self, entity: Entity) -> str:
        """Generate GET /:id handler"""
        struct_name = to_pascal_case(entity.name)
        snake_name = to_snake_case(entity.name)

        return f"""/// GET /{snake_name}s/{{id}}
/// Get a single {snake_name} by ID
pub async fn get_{snake_name}(
    pool: web::Data<DbPool>,
    {snake_name}_id: web::Path<Uuid>
) -> Result<HttpResponse> {{
    let mut conn = pool.get().expect("couldn't get db connection from pool");

    let {snake_name} = web::block(move || {{
        {struct_name}Queries::find_by_id(&mut conn, *{snake_name}_id)
    }})
    .await?
    .map_err(|_| HttpResponse::NotFound().finish())?;

    Ok(HttpResponse::Ok().json({snake_name}))
}}"""

    def generate_list_handler(self, entity: Entity) -> str:
        """Generate GET / handler"""
        struct_name = to_pascal_case(entity.name)
        snake_name = to_snake_case(entity.name)

        return f"""/// GET /{snake_name}s
/// List all active {snake_name}s
pub async fn list_{snake_name}s(
    pool: web::Data<DbPool>
) -> Result<HttpResponse> {{
    let mut conn = pool.get().expect("couldn't get db connection from pool");

    let {snake_name}s = web::block(move || {{
        {struct_name}Queries::list_active(&mut conn)
    }})
    .await?
    .map_err(|_| HttpResponse::InternalServerError().finish())?;

    Ok(HttpResponse::Ok().json({snake_name}s))
}}"""

    def generate_create_handler(self, entity: Entity) -> str:
        """Generate POST / handler"""
        struct_name = to_pascal_case(entity.name)
        snake_name = to_snake_case(entity.name)
        new_struct = f"New{struct_name}"

        return f"""/// POST /{snake_name}s
/// Create a new {snake_name}
pub async fn create_{snake_name}(
    pool: web::Data<DbPool>,
    new_{snake_name}: web::Json<{new_struct}>
) -> Result<HttpResponse> {{
    let mut conn = pool.get().expect("couldn't get db connection from pool");

    let {snake_name} = web::block(move || {{
        {struct_name}Queries::create(&mut conn, new_{snake_name}.into_inner())
    }})
    .await?
    .map_err(|_| HttpResponse::InternalServerError().finish())?;

    Ok(HttpResponse::Created().json({snake_name}))
}}"""

    def generate_update_handler(self, entity: Entity) -> str:
        """Generate PUT /:id handler"""
        struct_name = to_pascal_case(entity.name)
        snake_name = to_snake_case(entity.name)
        update_struct = f"Update{struct_name}"

        return f"""/// PUT /{snake_name}s/{{id}}
/// Update a {snake_name} by ID
pub async fn update_{snake_name}(
    pool: web::Data<DbPool>,
    {snake_name}_id: web::Path<Uuid>,
    update_data: web::Json<{update_struct}>
) -> Result<HttpResponse> {{
    let mut conn = pool.get().expect("couldn't get db connection from pool");

    let {snake_name} = web::block(move || {{
        {struct_name}Queries::update(&mut conn, *{snake_name}_id, update_data.into_inner())
    }})
    .await?
    .map_err(|_| HttpResponse::NotFound().finish())?;

    Ok(HttpResponse::Ok().json({snake_name}))
}}"""

    def generate_delete_handler(self, entity: Entity) -> str:
        """Generate DELETE /:id handler"""
        struct_name = to_pascal_case(entity.name)
        snake_name = to_snake_case(entity.name)

        return f"""/// DELETE /{snake_name}s/{{id}}
/// Soft delete a {snake_name} by ID
pub async fn delete_{snake_name}(
    pool: web::Data<DbPool>,
    {snake_name}_id: web::Path<Uuid>
) -> Result<HttpResponse> {{
    let mut conn = pool.get().expect("couldn't get db connection from pool");

    let _ = web::block(move || {{
        {struct_name}Queries::soft_delete(&mut conn, *{snake_name}_id)
    }})
    .await?
    .map_err(|_| HttpResponse::NotFound().finish())?;

    Ok(HttpResponse::NoContent().finish())
}}"""

    def generate_imports(self, entity: Entity) -> str:
        """Generate required imports for handlers"""
        struct_name = to_pascal_case(entity.name)

        imports = [
            "use actix_web::{web, HttpResponse, Result};",
            "use diesel::r2d2::{self, ConnectionManager};",
            "use diesel::PgConnection;",
            "use uuid::Uuid;",
            f"use super::super::models::{{{struct_name}, New{struct_name}, Update{struct_name}}};",
            f"use super::super::queries::{struct_name}Queries;",
        ]

        return "\n".join(imports)

    def generate_handlers_file(self, entity: Entity) -> str:
        """Generate complete handlers.rs file"""
        struct_name = to_pascal_case(entity.name)
        to_snake_case(entity.name)

        parts = [
            "// Generated by SpecQL",
            "// DO NOT EDIT MANUALLY",
            "",
            f"// HTTP handlers for {struct_name} entity",
            "",
            self.generate_imports(entity),
            "",
            "/// Database connection pool type alias",
            "pub type DbPool = r2d2::Pool<ConnectionManager<PgConnection>>;",
            "",
            self.generate_get_handler(entity),
            "",
            self.generate_list_handler(entity),
            "",
            self.generate_create_handler(entity),
            "",
            self.generate_update_handler(entity),
            "",
            self.generate_delete_handler(entity),
        ]

        return "\n".join(parts)

    def generate_route_config(self, entity: Entity) -> str:
        """Generate route configuration function"""
        snake_name = to_snake_case(entity.name)

        return f"""/// Configure routes for {snake_name} endpoints
pub fn configure_{snake_name}_routes(cfg: &mut web::ServiceConfig) {{
    cfg.service(
        web::scope("/{snake_name}s")
            .route("", web::get().to(list_{snake_name}s))
            .route("", web::post().to(create_{snake_name}))
            .route("/{{{snake_name}_id}}", web::get().to(get_{snake_name}))
            .route("/{{{snake_name}_id}}", web::put().to(update_{snake_name}))
            .route("/{{{snake_name}_id}}", web::delete().to(delete_{snake_name}))
    );
}}"""

    def generate_route_imports(self, entity: Entity) -> str:
        """Generate imports for route configuration"""
        snake_name = to_snake_case(entity.name)

        return f"""use actix_web::web;
use super::handlers::{snake_name}::{{get_{snake_name}, list_{snake_name}s, create_{snake_name}, update_{snake_name}, delete_{snake_name}}};"""

    def generate_routes_file(self, entity: Entity) -> str:
        """Generate complete routes.rs file"""
        snake_name = to_snake_case(entity.name)

        parts = [
            "// Generated by SpecQL",
            "// DO NOT EDIT MANUALLY",
            "",
            f"// Route configuration for {snake_name} endpoints",
            "",
            self.generate_route_imports(entity),
            "",
            self.generate_route_config(entity),
        ]

        return "\n".join(parts)
