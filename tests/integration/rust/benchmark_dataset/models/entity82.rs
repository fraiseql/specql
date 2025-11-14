use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity82s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity82s)]
pub struct Entity82 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity82Status,
    pub entity01_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity82s)]
pub struct NewEntity82 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity82Status,
    pub entity01_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity82Status {
    Draft,
    Active,
    Archived,
    Pending,
    Cancelled,
}
