use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity45s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity45s)]
pub struct Entity45 {
    pub id: i64,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity45Status,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity45s)]
pub struct NewEntity45 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity45Status,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity45Status {
    Draft,
    Active,
    Archived,
}
