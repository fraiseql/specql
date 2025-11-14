use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity65s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity65s)]
pub struct Entity65 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub tags: Vec<String>,
    pub status: Entity65Status,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity65s)]
pub struct NewEntity65 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub tags: Vec<String>,
    pub status: Entity65Status,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity65Status {
    Draft,
    Active,
    Archived,
}
