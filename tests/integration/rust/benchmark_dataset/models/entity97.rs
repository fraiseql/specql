use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity97s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity97s)]
pub struct Entity97 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity97Status,
    pub entity06_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity97s)]
pub struct NewEntity97 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity97Status,
    pub entity06_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity97Status {
    Draft,
    Active,
    Archived,
}
