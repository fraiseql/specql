"""Generate large test dataset for performance testing"""

from pathlib import Path


def generate_large_dataset(output_dir: Path, num_models: int = 100):
    """
    Generate a large dataset of Rust Diesel models for performance testing.

    Args:
        output_dir: Directory to create the dataset in
        num_models: Number of models to generate
    """
    models_dir = output_dir / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    # Generate individual model files
    for i in range(num_models):
        model_name = f"Entity{i:02d}"
        generate_model_file(models_dir / f"{model_name.lower()}.rs", model_name, i)

    # Generate schema.rs
    generate_schema_file(output_dir / "schema.rs", num_models)


def generate_model_file(file_path: Path, model_name: str, index: int):
    """Generate a single model file with advanced types"""
    # Vary the model structure based on index
    has_description = index % 3 != 0
    has_status = index % 4 != 0
    has_reference = index % 5 != 0
    has_uuid = index % 7 == 0  # Every 7th model has UUID
    has_json = index % 11 == 0  # Every 11th model has JSON
    has_array = index % 13 == 0  # Every 13th model has array
    has_lifetimes = False  # Disable lifetimes for now - they require reference fields
    has_audit = index % 19 == 0  # Every 19th model has audit fields

    # Build imports
    imports = """use diesel::prelude::*;
use serde::{Deserialize, Serialize};"""

    if has_uuid or has_audit:
        imports += """
use uuid::Uuid;"""

    if has_json:
        imports += """
use serde_json::Value;"""

    if has_audit:
        imports += """
use chrono;"""

    content = f"""{imports}

use crate::schema::{model_name.lower()}s;

#[derive(Debug, Clone, Queryable, Insertable, Serialize, Deserialize)]
#[diesel(table_name = {model_name.lower()}s)]
pub struct {model_name}"""

    if has_lifetimes:
        content += "<'a>"

    content += """ {
    pub id: i64,"""

    if has_uuid:
        content += """
    pub uuid: Uuid,"""

    content += """
    pub name: String,"""

    if has_description:
        content += """
    pub description: Option<String>,"""

    content += """
    pub value: i32,
    pub active: bool,"""

    if has_array:
        content += """
    pub tags: Vec<String>,"""

    if has_json:
        content += """
    pub metadata: Value,"""

    if has_status:
        content += f"""
    pub status: {model_name}Status,"""

    if has_reference:
        ref_model = f"Entity{(index - 1) % 10:02d}"
        content += f"""
    pub {ref_model.lower()}_id: i64,"""

    if has_audit:
        content += """
    pub created_at: chrono::NaiveDateTime,
    pub updated_at: chrono::NaiveDateTime,
    pub created_by: Option<Uuid>,
    pub updated_by: Option<Uuid>,"""

    content += f"""
}}

#[derive(Debug, Clone, Insertable)]
#[diesel(table_name = {model_name.lower()}s)]
pub struct New{model_name} {{
    pub name: String,"""

    if has_description:
        content += """
    pub description: Option<String>,"""

    content += """
    pub value: i32,
    pub active: bool,"""

    if has_array:
        content += """
    pub tags: Vec<String>,"""

    if has_json:
        content += """
    pub metadata: Value,"""

    if has_status:
        content += f"""
    pub status: {model_name}Status,"""

    if has_reference:
        ref_model = f"Entity{(index - 1) % 10:02d}"
        content += f"""
    pub {ref_model.lower()}_id: i64,"""

    if has_audit:
        content += """
    pub created_by: Option<Uuid>,
    pub updated_by: Option<Uuid>,"""

    content += """
}
"""

    if has_status:
        content += f"""
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum {model_name}Status {{
    Draft,
    Active,
    Archived,"""

        if index % 2 == 0:
            content += """
    Pending,
    Cancelled,"""

        content += """
}
"""

    with open(file_path, "w") as f:
        f.write(content)


def generate_schema_file(schema_path: Path, num_models: int):
    """Generate the schema.rs file with all table definitions"""
    content = """diesel::table! {
    simples (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        price -> Int4,
        active -> Bool,
        status -> Text,
        category_id -> Int8,
    }
}

"""

    # Generate table definitions for all models
    for i in range(num_models):
        model_name = f"Entity{i:02d}"
        table_name = model_name.lower() + "s"

        # Determine which advanced types this model has
        has_description = i % 3 != 0
        has_status = i % 4 != 0
        has_reference = i % 5 != 0
        has_uuid = i % 7 == 0
        has_json = i % 11 == 0
        has_array = i % 13 == 0
        has_audit = i % 19 == 0

        content += f"""diesel::table! {{
    {table_name} (id) {{
        id -> Int8,"""

        if has_uuid:
            content += """
        uuid -> Uuid,"""

        content += """
        name -> Text,"""

        if has_description:
            content += """
        description -> Nullable<Text>,"""

        content += """
        value -> Int4,
        active -> Bool,"""

        if has_array:
            content += """
        tags -> Array<Text>,"""

        if has_json:
            content += """
        metadata -> Jsonb,"""

        if has_status:
            content += """
        status -> Text,"""

        if has_reference:
            ref_model = f"Entity{(i - 1) % 10:02d}"
            content += f"""
        {ref_model.lower()}_id -> Int8,"""

        if has_audit:
            content += """
        created_at -> Timestamp,
        updated_at -> Timestamp,
        created_by -> Nullable<Uuid>,
        updated_by -> Nullable<Uuid>,"""

        content += """
    }
}

"""

    # Generate joinable statements
    for i in range(num_models):
        if i % 5 != 0:  # Only for models that have references
            model_name = f"Entity{i:02d}"
            ref_model = f"Entity{(i - 1) % 10:02d}"
            content += f"""diesel::joinable!({model_name.lower()}s -> {ref_model.lower()}s ({ref_model.lower()}_id));

"""

    # Generate allow_tables_to_appear_in_same_query
    content += """diesel::allow_tables_to_appear_in_same_query!(
"""

    for i in range(num_models):
        model_name = f"Entity{i:02d}"
        table_name = model_name.lower() + "s"
        content += f"""    {table_name},"""

    content += """
    simples,
);
"""

    with open(schema_path, "w") as f:
        f.write(content)


if __name__ == "__main__":
    # Allow running as a script
    import sys

    if len(sys.argv) > 1:
        num_models = int(sys.argv[1])
    else:
        num_models = 100

    # Generate to the benchmark_dataset directory
    output_dir = Path(__file__).parent / "benchmark_dataset"
    generate_large_dataset(output_dir, num_models)
    print(f"Generated {num_models} models in {output_dir}")
