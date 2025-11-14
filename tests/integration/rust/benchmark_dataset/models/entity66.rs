use diesel::prelude::*;
use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::schema::entity66s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity66s)]
pub struct Entity66 {
    pub id: i64,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub metadata: Value,
    pub status: Entity66Status,
    pub entity05_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity66s)]
pub struct NewEntity66 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub metadata: Value,
    pub status: Entity66Status,
    pub entity05_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity66Status {
    Draft,
    Active,
    Archived,
    Pending,
    Cancelled,
}
