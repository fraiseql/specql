use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity50s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity50s)]
pub struct Entity50 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity50Status,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity50s)]
pub struct NewEntity50 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity50Status,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity50Status {
    Draft,
    Active,
    Archived,
    Pending,
    Cancelled,
}
