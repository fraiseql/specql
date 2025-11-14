use diesel::prelude::*;
use serde::{Deserialize, Serialize};

use crate::schema::entity40s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = entity40s)]
pub struct Entity40 {
    pub id: i64,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = entity40s)]
pub struct NewEntity40 {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub active: bool,
}
