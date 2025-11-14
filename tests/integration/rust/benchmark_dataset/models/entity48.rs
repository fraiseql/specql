use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity48s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity48s)]
pub struct Entity48 {
    pub id: i64,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub entity07_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity48s)]
pub struct NewEntity48 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub entity07_id: i64,
}
