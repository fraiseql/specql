use diesel::prelude::*;
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use serde_json::Value;
use chrono;

use crate::schema::entity00s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity00s)]
pub struct Entity00 {
    pub id: i64,
    pub uuid: Uuid,
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub tags: Vec<String>,
    pub metadata: Value,
    pub created_at: chrono::NaiveDateTime,
    pub updated_at: chrono::NaiveDateTime,
    pub created_by: Option<Uuid>,
    pub updated_by: Option<Uuid>,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity00s)]
pub struct NewEntity00 {
    pub name: String,
    pub value: i32,
    pub active: bool,
    pub tags: Vec<String>,
    pub metadata: Value,
    pub created_by: Option<Uuid>,
    pub updated_by: Option<Uuid>,
}
