use diesel::prelude::*;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::schema::entity91s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity91s)]
pub struct Entity91 {
    pub id: i64,
    pub uuid: Uuid,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub tags: Vec<String>,
    pub status: Entity91Status,
    pub entity00_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity91s)]
pub struct NewEntity91 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub tags: Vec<String>,
    pub status: Entity91Status,
    pub entity00_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity91Status {
    Draft,
    Active,
    Archived,
}
