use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity46s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity46s)]
pub struct Entity46 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity46Status,
    pub entity05_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity46s)]
pub struct NewEntity46 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity46Status,
    pub entity05_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity46Status {
    Draft,
    Active,
    Archived,
    Pending,
    Cancelled,
}
