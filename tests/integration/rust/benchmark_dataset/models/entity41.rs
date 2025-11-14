use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity41s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity41s)]
pub struct Entity41 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity41Status,
    pub entity00_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity41s)]
pub struct NewEntity41 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity41Status,
    pub entity00_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity41Status {
    Draft,
    Active,
    Archived,
}
