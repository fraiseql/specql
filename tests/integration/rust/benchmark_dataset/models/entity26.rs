use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity26s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity26s)]
pub struct Entity26 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub tags: Vec<String>,
    pub status: Entity26Status,
    pub entity05_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity26s)]
pub struct NewEntity26 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub tags: Vec<String>,
    pub status: Entity26Status,
    pub entity05_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity26Status {
    Draft,
    Active,
    Archived,
    Pending,
    Cancelled,
}
