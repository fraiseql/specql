use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity09s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity09s)]
pub struct Entity09 {
    pub id: i64,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity09Status,
    pub entity08_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity09s)]
pub struct NewEntity09 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity09Status,
    pub entity08_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity09Status {
    Draft,
    Active,
    Archived,
}
