use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity13s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity13s)]
pub struct Entity13 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub tags: Vec<String>,
    pub status: Entity13Status,
    pub entity02_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity13s)]
pub struct NewEntity13 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub tags: Vec<String>,
    pub status: Entity13Status,
    pub entity02_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity13Status {
    Draft,
    Active,
    Archived,
}
