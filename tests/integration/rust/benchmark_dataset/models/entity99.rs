use diesel::prelude::*;
use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::schema::entity99s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity99s)]
pub struct Entity99 {
    pub id: i64,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub metadata: Value,
    pub status: Entity99Status,
    pub entity08_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity99s)]
pub struct NewEntity99 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub metadata: Value,
    pub status: Entity99Status,
    pub entity08_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity99Status {
    Draft,
    Active,
    Archived,
}
