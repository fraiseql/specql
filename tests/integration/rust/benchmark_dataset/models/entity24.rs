use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity24s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity24s)]
pub struct Entity24 {
    pub id: i64,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub entity03_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity24s)]
pub struct NewEntity24 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub entity03_id: i64,
}
