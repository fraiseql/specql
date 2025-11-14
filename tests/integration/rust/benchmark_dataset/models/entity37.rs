use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity37s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity37s)]
pub struct Entity37 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity37Status,
    pub entity06_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity37s)]
pub struct NewEntity37 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub status: Entity37Status,
    pub entity06_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity37Status {
    Draft,
    Active,
    Archived,
}
