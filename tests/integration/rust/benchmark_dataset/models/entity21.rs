use diesel::prelude::*;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::schema::entity21s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity21s)]
pub struct Entity21 {
    pub id: i64,
    pub uuid: Uuid,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity21Status,
    pub entity00_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity21s)]
pub struct NewEntity21 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub status: Entity21Status,
    pub entity00_id: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Entity21Status {
    Draft,
    Active,
    Archived,
}
