use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity17s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity17s)]
pub struct Entity17 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity17Status,
    pub entity06_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity17s)]
pub struct NewEntity17 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity17Status,
    pub entity06_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity17Status {
    Draft,
    Active,
    Archived,
}
