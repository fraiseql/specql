use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity32s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity32s)]
pub struct Entity32 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub entity01_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity32s)]
pub struct NewEntity32 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub entity01_id: i64,
}
