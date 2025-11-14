use diesel::prelude::*;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::schema::entity42s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity42s)]
pub struct Entity42 {
    pub id: i64,
    pub uuid: Uuid,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity42Status,
    pub entity01_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity42s)]
pub struct NewEntity42 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity42Status,
    pub entity01_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity42Status {
    Draft,
    Active,
    Archived,
    Pending,
    Cancelled,
}
