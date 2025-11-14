use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity08s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity08s)]
pub struct Entity08 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub entity07_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity08s)]
pub struct NewEntity08 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub entity07_id: i64,
}
