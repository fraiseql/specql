use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity94s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity94s)]
pub struct Entity94 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity94Status,
    pub entity03_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity94s)]
pub struct NewEntity94 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity94Status,
    pub entity03_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity94Status {
    Draft,
    Active,
    Archived,
    Pending,
    Cancelled,
}
