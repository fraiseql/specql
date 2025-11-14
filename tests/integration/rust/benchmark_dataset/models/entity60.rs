use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity60s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity60s)]
pub struct Entity60 {
    pub id: i64,
    pub name: String,
    pub value: i32,
    pub active: bool,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity60s)]
pub struct NewEntity60 {
    pub name: String,
    pub value: i32,
    pub active: bool,
}
