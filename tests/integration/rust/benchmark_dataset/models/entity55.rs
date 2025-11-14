use diesel::prelude::*;
use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::schema::entity55s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity55s)]
pub struct Entity55 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub metadata: Value,
    pub status: Entity55Status,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity55s)]
pub struct NewEntity55 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub metadata: Value,
    pub status: Entity55Status,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity55Status {
    Draft,
    Active,
    Archived,
}
