"""
Tree-sitter Performance Tests

Compare tree-sitter vs regex performance for Rust parsing.
"""

import os
import tempfile
import time

from src.reverse_engineering.rust_action_parser import RustActionParser


def test_tree_sitter_vs_regex_performance():
    """Compare tree-sitter vs regex performance"""

    # Create a complex Rust file with multiple macros and structures
    complex_rust_code = (
        """
use diesel::prelude::*;
use rocket::serde::{Deserialize, Serialize};
use std::collections::HashMap;

diesel::table! {
    contacts (id) {
        id -> Integer,
        email -> Varchar,
        name -> Varchar,
        phone -> Nullable<Varchar>,
        status -> Varchar,
        created_at -> Timestamp,
        updated_at -> Timestamp,
    }
}

diesel::table! {
    companies (id) {
        id -> Integer,
        name -> Varchar,
        domain -> Varchar,
        address -> Nullable<Text>,
        created_at -> Timestamp,
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, Queryable, Insertable)]
#[diesel(table_name = contacts)]
pub struct Contact {
    pub id: i32,
    pub email: String,
    pub name: String,
    pub phone: Option<String>,
    pub status: String,
    pub created_at: chrono::NaiveDateTime,
    pub updated_at: chrono::NaiveDateTime,
}

#[derive(Debug, Clone, Serialize, Deserialize, Queryable, Insertable)]
#[diesel(table_name = companies)]
pub struct Company {
    pub id: i32,
    pub name: String,
    pub domain: String,
    pub address: Option<String>,
    pub created_at: chrono::NaiveDateTime,
}

pub async fn create_contact(
    db: web::Data<Database>,
    contact: web::Json<ContactDTO>
) -> Result<HttpResponse, Error> {
    let new_contact = Contact {
        id: 0,
        email: contact.email.clone(),
        name: contact.name.clone(),
        phone: contact.phone.clone(),
        status: "active".to_string(),
        created_at: chrono::Utc::now().naive_utc(),
        updated_at: chrono::Utc::now().naive_utc(),
    };

    diesel::insert_into(contacts::table)
        .values(&new_contact)
        .execute(&mut db.get().unwrap())
        .expect("Error saving new contact");

    Ok(HttpResponse::Created().json(new_contact))
}

pub async fn get_contacts(
    db: web::Data<Database>
) -> Result<HttpResponse, Error> {
    let results = contacts::table
        .load::<Contact>(&mut db.get().unwrap())
        .expect("Error loading contacts");

    Ok(HttpResponse::Ok().json(results))
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ContactDTO {
    pub email: String,
    pub name: String,
    pub phone: Option<String>,
}
"""
        * 5
    )  # Repeat 5 times to make it larger

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".rs", delete=False) as f:
        f.write(complex_rust_code)
        temp_file = f.name

    try:
        # Tree-sitter
        ts_parser = RustActionParser(use_tree_sitter=True)
        start = time.time()
        ts_result = ts_parser.parse_file(temp_file)
        ts_time = time.time() - start

        # Regex (fallback)
        regex_parser = RustActionParser(use_tree_sitter=False)
        start = time.time()
        regex_result = regex_parser.parse_file(temp_file)
        regex_time = time.time() - start

        print(f"Tree-sitter: {ts_time:.3f}s")
        print(f"Regex: {regex_time:.3f}s")
        print(
            f"Tree-sitter result: {len(ts_result.functions)} functions, {len(ts_result.structs)} structs"
        )
        print(
            f"Regex result: {len(regex_result.functions)} functions, {len(regex_result.structs)} structs"
        )

        # Tree-sitter should parse successfully and find content
        # Regex fallback currently returns empty results (not implemented)
        assert ts_result.parser_used == "tree-sitter"
        assert len(ts_result.functions) > 0, "Tree-sitter should find functions"
        assert len(ts_result.structs) > 0, "Tree-sitter should find structs"

        # Performance should be reasonable (< 1 second for this test file)
        assert ts_time < 1.0, f"Tree-sitter parsing should be fast ({ts_time:.3f}s)"

    finally:
        os.unlink(temp_file)
