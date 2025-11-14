use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::simples;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = simples)]
pub struct Simple {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub price: i32,
    pub active: bool,
    pub status: SimpleStatus,
    pub category_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = simples)]
pub struct NewSimple {
    pub name: String,
    pub description: Option<String>,
    pub price: i32,
    pub active: bool,
    pub status: SimpleStatus,
    pub category_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SimpleStatus {
    Draft,
    Active,
    Archived,
}