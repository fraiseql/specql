use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity18s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity18s)]
pub struct Entity18 {
    pub id: i64,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity18Status,
    pub entity07_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity18s)]
pub struct NewEntity18 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity18Status,
    pub entity07_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity18Status {
    Draft,
    Active,
    Archived,
    Pending,
    Cancelled,
}
