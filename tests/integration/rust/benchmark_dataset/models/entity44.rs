use diesel::prelude::*;
use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::schema::entity44s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity44s)]
pub struct Entity44 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub metadata: Value,
    pub entity03_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity44s)]
pub struct NewEntity44 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub metadata: Value,
    pub entity03_id: i64,
}
