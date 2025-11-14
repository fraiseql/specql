use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity51s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity51s)]
pub struct Entity51 {
    pub id: i64,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity51Status,
    pub entity00_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity51s)]
pub struct NewEntity51 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity51Status,
    pub entity00_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity51Status {
    Draft,
    Active,
    Archived,
}
