use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity52s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity52s)]
pub struct Entity52 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub tags: Vec<String>,
    pub entity01_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity52s)]
pub struct NewEntity52 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub tags: Vec<String>,
    pub entity01_id: i64,
}
