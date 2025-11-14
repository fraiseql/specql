use diesel::prelude::*;
use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::schema::entity11s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity11s)]
pub struct Entity11 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub metadata: Value,
    pub status: Entity11Status,
    pub entity00_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity11s)]
pub struct NewEntity11 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub metadata: Value,
    pub status: Entity11Status,
    pub entity00_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity11Status {
    Draft,
    Active,
    Archived,
}
