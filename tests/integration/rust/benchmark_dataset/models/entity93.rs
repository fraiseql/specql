use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity93s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity93s)]
pub struct Entity93 {
    pub id: i64,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity93Status,
    pub entity02_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity93s)]
pub struct NewEntity93 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity93Status,
    pub entity02_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity93Status {
    Draft,
    Active,
    Archived,
}
