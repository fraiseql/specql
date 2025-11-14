use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity80s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity80s)]
pub struct Entity80 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity80s)]
pub struct NewEntity80 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
}
