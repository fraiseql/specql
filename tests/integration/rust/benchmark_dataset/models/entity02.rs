use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity02s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity02s)]
pub struct Entity02 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity02Status,
    pub entity01_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity02s)]
pub struct NewEntity02 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity02Status,
    pub entity01_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity02Status {
    Draft,
    Active,
    Archived,
    Pending,
    Cancelled,
}
