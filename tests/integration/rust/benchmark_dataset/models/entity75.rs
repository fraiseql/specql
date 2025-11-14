use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity75s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity75s)]
pub struct Entity75 {
    pub id: i64,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity75Status,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity75s)]
pub struct NewEntity75 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity75Status,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity75Status {
    Draft,
    Active,
    Archived,
}
