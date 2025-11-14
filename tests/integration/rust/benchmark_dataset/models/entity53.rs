use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity53s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity53s)]
pub struct Entity53 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity53Status,
    pub entity02_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity53s)]
pub struct NewEntity53 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity53Status,
    pub entity02_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity53Status {
    Draft,
    Active,
    Archived,
}
