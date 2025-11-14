use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity12s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity12s)]
pub struct Entity12 {
    pub id: i64,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub entity01_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity12s)]
pub struct NewEntity12 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub entity01_id: i64,
}
