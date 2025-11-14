use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity92s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity92s)]
pub struct Entity92 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub entity01_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity92s)]
pub struct NewEntity92 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub entity01_id: i64,
}
