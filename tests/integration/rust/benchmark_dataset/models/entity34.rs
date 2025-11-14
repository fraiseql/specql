use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity34s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity34s)]
pub struct Entity34 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity34Status,
    pub entity03_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity34s)]
pub struct NewEntity34 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity34Status,
    pub entity03_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity34Status {
    Draft,
    Active,
    Archived,
    Pending,
    Cancelled,
}
