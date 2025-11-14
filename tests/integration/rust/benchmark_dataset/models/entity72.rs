use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity72s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity72s)]
pub struct Entity72 {
    pub id: i64,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub entity01_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity72s)]
pub struct NewEntity72 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub entity01_id: i64,
}
