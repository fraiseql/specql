use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity31s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity31s)]
pub struct Entity31 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity31Status,
    pub entity00_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity31s)]
pub struct NewEntity31 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity31Status,
    pub entity00_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity31Status {
    Draft,
    Active,
    Archived,
}
