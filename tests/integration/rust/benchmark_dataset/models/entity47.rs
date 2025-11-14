use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity47s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity47s)]
pub struct Entity47 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity47Status,
    pub entity06_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity47s)]
pub struct NewEntity47 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity47Status,
    pub entity06_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity47Status {
    Draft,
    Active,
    Archived,
}
