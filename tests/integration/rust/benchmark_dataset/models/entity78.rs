use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity78s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity78s)]
pub struct Entity78 {
    pub id: i64,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub tags: Vec<String>,
    pub status: Entity78Status,
    pub entity07_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity78s)]
pub struct NewEntity78 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub tags: Vec<String>,
    pub status: Entity78Status,
    pub entity07_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity78Status {
    Draft,
    Active,
    Archived,
    Pending,
    Cancelled,
}
