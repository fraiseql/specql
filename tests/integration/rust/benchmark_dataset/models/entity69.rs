use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity69s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity69s)]
pub struct Entity69 {
    pub id: i64,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity69Status,
    pub entity08_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity69s)]
pub struct NewEntity69 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity69Status,
    pub entity08_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity69Status {
    Draft,
    Active,
    Archived,
}
