use diesel::prelude::*;
use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::schema::entity88s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity88s)]
pub struct Entity88 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub metadata: Value,
    pub entity07_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity88s)]
pub struct NewEntity88 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub metadata: Value,
    pub entity07_id: i64,
}
