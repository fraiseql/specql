use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity89s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity89s)]
pub struct Entity89 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity89Status,
    pub entity08_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity89s)]
pub struct NewEntity89 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity89Status,
    pub entity08_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity89Status {
    Draft,
    Active,
    Archived,
}
