use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity87s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity87s)]
pub struct Entity87 {
    pub id: i64,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity87Status,
    pub entity06_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity87s)]
pub struct NewEntity87 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity87Status,
    pub entity06_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity87Status {
    Draft,
    Active,
    Archived,
}
