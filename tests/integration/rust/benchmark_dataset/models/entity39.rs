use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity39s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity39s)]
pub struct Entity39 {
    pub id: i64,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub tags: Vec<String>,
    pub status: Entity39Status,
    pub entity08_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity39s)]
pub struct NewEntity39 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub tags: Vec<String>,
    pub status: Entity39Status,
    pub entity08_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity39Status {
    Draft,
    Active,
    Archived,
}
