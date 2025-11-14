use actix_web::{get, post, put, delete, web, HttpResponse, Result};
use axum::{routing::get as axum_get, Router};
use diesel::prelude::*;
use serde::{Deserialize, Serialize};

// Diesel table definition
table! {
    users (id) {
        id -> Integer,
        name -> Text,
        email -> Text,
        created_at -> Timestamp,
    }
}

// Struct with Diesel derives
#[derive(Queryable, Identifiable, Serialize, Deserialize)]
pub struct User {
    pub id: i32,
    pub name: String,
    pub email: String,
    pub created_at: chrono::NaiveDateTime,
}

#[derive(Insertable)]
#[table_name = "users"]
pub struct NewUser<'a> {
    pub name: &'a str,
    pub email: &'a str,
}

// Enum definitions
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum UserStatus {
    Active,
    Inactive,
    Suspended { reason: String },
    Banned(String),
}

#[derive(Debug)]
pub enum HttpMethod {
    GET = 1,
    POST = 2,
    PUT = 3,
    DELETE = 4,
}

// Implementation with CRUD methods
impl User {
    pub fn find_all() -> Result<Vec<User>, diesel::result::Error> {
        let connection = establish_connection();
        users::table.load::<User>(&connection)
    }

    pub fn find_by_id(user_id: i32) -> Result<User, diesel::result::Error> {
        let connection = establish_connection();
        users::table.find(user_id).first(&connection)
    }

    pub fn create(new_user: NewUser) -> Result<User, diesel::result::Error> {
        let connection = establish_connection();
        diesel::insert_into(users::table)
            .values(&new_user)
            .get_result(&connection)
    }

    pub fn update(user_id: i32, updated_user: &NewUser) -> Result<User, diesel::result::Error> {
        let connection = establish_connection();
        diesel::update(users::table.find(user_id))
            .set(updated_user)
            .get_result(&connection)
    }

    pub fn delete(user_id: i32) -> Result<(), diesel::result::Error> {
        let connection = establish_connection();
        diesel::delete(users::table.find(user_id)).execute(&connection)?;
        Ok(())
    }
}

// Actix-web route handlers
#[get("/users")]
async fn get_users() -> Result<HttpResponse> {
    let users = User::find_all().unwrap_or_default();
    Ok(HttpResponse::Ok().json(users))
}

#[post("/users")]
async fn create_user(new_user: web::Json<NewUser>) -> Result<HttpResponse> {
    match User::create(new_user.into_inner()) {
        Ok(user) => Ok(HttpResponse::Created().json(user)),
        Err(_) => Ok(HttpResponse::InternalServerError().finish()),
    }
}

#[get("/users/{id}")]
async fn get_user(path: web::Path<i32>) -> Result<HttpResponse> {
    let user_id = path.into_inner();
    match User::find_by_id(user_id) {
        Ok(user) => Ok(HttpResponse::Ok().json(user)),
        Err(_) => Ok(HttpResponse::NotFound().finish()),
    }
}

#[put("/users/{id}")]
async fn update_user(path: web::Path<i32>, updated_user: web::Json<NewUser>) -> Result<HttpResponse> {
    let user_id = path.into_inner();
    match User::update(user_id, &updated_user) {
        Ok(user) => Ok(HttpResponse::Ok().json(user)),
        Err(_) => Ok(HttpResponse::InternalServerError().finish()),
    }
}

#[delete("/users/{id}")]
async fn delete_user(path: web::Path<i32>) -> Result<HttpResponse> {
    let user_id = path.into_inner();
    match User::delete(user_id) {
        Ok(_) => Ok(HttpResponse::NoContent().finish()),
        Err(_) => Ok(HttpResponse::InternalServerError().finish()),
    }
}

// Axum route handlers
async fn health_check() -> &'static str {
    "OK"
}

#[axum_get("/health")]
async fn axum_health() -> &'static str {
    "Axum OK"
}

// Helper function (would normally be implemented)
fn establish_connection() -> diesel::PgConnection {
    unimplemented!()
}