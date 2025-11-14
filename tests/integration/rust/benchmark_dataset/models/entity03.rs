use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity03s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity03s)]
pub struct Entity03 {
    pub id: i64,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity03Status,
    pub entity02_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity03s)]
pub struct NewEntity03 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity03Status,
    pub entity02_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity03Status {
    Draft,
    Active,
    Archived,
}
