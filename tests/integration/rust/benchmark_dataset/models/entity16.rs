use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity16s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity16s)]
pub struct Entity16 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub entity05_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity16s)]
pub struct NewEntity16 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub entity05_id: i64,
}
