use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity73s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity73s)]
pub struct Entity73 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity73Status,
    pub entity02_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity73s)]
pub struct NewEntity73 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity73Status,
    pub entity02_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity73Status {
    Draft,
    Active,
    Archived,
}
