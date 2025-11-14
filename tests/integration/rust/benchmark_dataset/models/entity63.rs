use diesel::prelude::*;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::schema::entity63s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity63s)]
pub struct Entity63 {
    pub id: i64,
    pub uuid: Uuid,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity63Status,
    pub entity02_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity63s)]
pub struct NewEntity63 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity63Status,
    pub entity02_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity63Status {
    Draft,
    Active,
    Archived,
}
