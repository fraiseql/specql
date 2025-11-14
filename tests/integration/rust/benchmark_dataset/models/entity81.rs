use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity81s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity81s)]
pub struct Entity81 {
    pub id: i64,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity81Status,
    pub entity00_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity81s)]
pub struct NewEntity81 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity81Status,
    pub entity00_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity81Status {
    Draft,
    Active,
    Archived,
}
