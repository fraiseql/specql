use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity90s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity90s)]
pub struct Entity90 {
    pub id: i64,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity90Status,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity90s)]
pub struct NewEntity90 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity90Status,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity90Status {
    Draft,
    Active,
    Archived,
    Pending,
    Cancelled,
}
