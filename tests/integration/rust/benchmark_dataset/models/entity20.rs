use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity20s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity20s)]
pub struct Entity20 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity20s)]
pub struct NewEntity20 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
}
