use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity86s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity86s)]
pub struct Entity86 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity86Status,
    pub entity05_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity86s)]
pub struct NewEntity86 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity86Status,
    pub entity05_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity86Status {
    Draft,
    Active,
    Archived,
    Pending,
    Cancelled,
}
