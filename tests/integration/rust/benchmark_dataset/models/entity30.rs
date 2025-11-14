use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity30s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity30s)]
pub struct Entity30 {
    pub id: i64,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity30Status,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity30s)]
pub struct NewEntity30 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity30Status,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity30Status {
    Draft,
    Active,
    Archived,
    Pending,
    Cancelled,
}
