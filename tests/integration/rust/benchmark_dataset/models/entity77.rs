use diesel::prelude::*;
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use serde_json::Value;

use crate::schema::entity77s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity77s)]
pub struct Entity77 {
    pub id: i64,
    pub uuid: Uuid,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub metadata: Value,
    pub status: Entity77Status,
    pub entity06_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity77s)]
pub struct NewEntity77 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub metadata: Value,
    pub status: Entity77Status,
    pub entity06_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity77Status {
    Draft,
    Active,
    Archived,
}
