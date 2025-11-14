use diesel::prelude::*;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::schema::entity84s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity84s)]
pub struct Entity84 {
    pub id: i64,
    pub uuid: Uuid,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub entity03_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity84s)]
pub struct NewEntity84 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub entity03_id: i64,
}
