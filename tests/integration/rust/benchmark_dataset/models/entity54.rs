use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity54s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity54s)]
pub struct Entity54 {
    pub id: i64,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity54Status,
    pub entity03_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity54s)]
pub struct NewEntity54 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity54Status,
    pub entity03_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity54Status {
    Draft,
    Active,
    Archived,
    Pending,
    Cancelled,
}
