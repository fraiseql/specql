use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity25s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity25s)]
pub struct Entity25 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity25Status,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity25s)]
pub struct NewEntity25 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity25Status,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity25Status {
    Draft,
    Active,
    Archived,
}
