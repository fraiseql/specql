use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity74s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity74s)]
pub struct Entity74 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity74Status,
    pub entity03_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity74s)]
pub struct NewEntity74 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity74Status,
    pub entity03_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity74Status {
    Draft,
    Active,
    Archived,
    Pending,
    Cancelled,
}
