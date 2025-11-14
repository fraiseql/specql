use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity36s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity36s)]
pub struct Entity36 {
    pub id: i64,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub entity05_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity36s)]
pub struct NewEntity36 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub entity05_id: i64,
}
