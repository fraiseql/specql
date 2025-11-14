use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity68s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity68s)]
pub struct Entity68 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub entity07_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity68s)]
pub struct NewEntity68 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub entity07_id: i64,
}
