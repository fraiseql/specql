use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity06s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity06s)]
pub struct Entity06 {
    pub id: i64,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity06Status,
    pub entity05_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity06s)]
pub struct NewEntity06 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity06Status,
    pub entity05_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity06Status {
    Draft,
    Active,
    Archived,
    Pending,
    Cancelled,
}
