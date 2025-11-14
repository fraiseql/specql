use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity27s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity27s)]
pub struct Entity27 {
    pub id: i64,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity27Status,
    pub entity06_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity27s)]
pub struct NewEntity27 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity27Status,
    pub entity06_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity27Status {
    Draft,
    Active,
    Archived,
}
