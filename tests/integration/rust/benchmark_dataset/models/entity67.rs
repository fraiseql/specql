use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity67s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity67s)]
pub struct Entity67 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity67Status,
    pub entity06_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity67s)]
pub struct NewEntity67 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity67Status,
    pub entity06_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity67Status {
    Draft,
    Active,
    Archived,
}
