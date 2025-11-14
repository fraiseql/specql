use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity15s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity15s)]
pub struct Entity15 {
    pub id: i64,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity15Status,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity15s)]
pub struct NewEntity15 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity15Status,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity15Status {
    Draft,
    Active,
    Archived,
}
