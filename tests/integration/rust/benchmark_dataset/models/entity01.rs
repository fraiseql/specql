use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity01s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity01s)]
pub struct Entity01 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity01Status,
    pub entity00_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity01s)]
pub struct NewEntity01 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity01Status,
    pub entity00_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity01Status {
    Draft,
    Active,
    Archived,
}
