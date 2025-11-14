use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity10s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity10s)]
pub struct Entity10 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity10Status,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity10s)]
pub struct NewEntity10 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity10Status,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity10Status {
    Draft,
    Active,
    Archived,
    Pending,
    Cancelled,
}
