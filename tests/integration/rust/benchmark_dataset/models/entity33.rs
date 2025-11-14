use diesel::prelude::*;
use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::schema::entity33s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity33s)]
pub struct Entity33 {
    pub id: i64,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub metadata: Value,
    pub status: Entity33Status,
    pub entity02_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity33s)]
pub struct NewEntity33 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub metadata: Value,
    pub status: Entity33Status,
    pub entity02_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity33Status {
    Draft,
    Active,
    Archived,
}
