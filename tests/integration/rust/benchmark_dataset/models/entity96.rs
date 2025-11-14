use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity96s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity96s)]
pub struct Entity96 {
    pub id: i64,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub entity05_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity96s)]
pub struct NewEntity96 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub entity05_id: i64,
}
