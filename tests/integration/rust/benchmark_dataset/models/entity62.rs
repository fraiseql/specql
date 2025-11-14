use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity62s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity62s)]
pub struct Entity62 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity62Status,
    pub entity01_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity62s)]
pub struct NewEntity62 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity62Status,
    pub entity01_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity62Status {
    Draft,
    Active,
    Archived,
    Pending,
    Cancelled,
}
