use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity05s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity05s)]
pub struct Entity05 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity05Status,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity05s)]
pub struct NewEntity05 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity05Status,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity05Status {
    Draft,
    Active,
    Archived,
}
