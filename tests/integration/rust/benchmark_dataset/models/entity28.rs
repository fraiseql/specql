use diesel::prelude::*;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::schema::entity28s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity28s)]
pub struct Entity28 {
    pub id: i64,
    pub uuid: Uuid,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub entity07_id: i64,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity28s)]
pub struct NewEntity28 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
    pub entity07_id: i64,
}
