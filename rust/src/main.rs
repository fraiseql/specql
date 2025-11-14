use std::env;
use std::fs;
use syn::{ItemStruct, Fields, Field, Type};
use quote::ToTokens;
use serde::{Serialize, Deserialize};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct RustField {
    pub name: String,
    pub field_type: String,
    pub is_optional: bool,
    pub attributes: Vec<String>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct RustStruct {
    pub name: String,
    pub fields: Vec<RustField>,
    pub attributes: Vec<String>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct DieselTable {
    pub name: String,
    pub primary_key: Vec<String>,
    pub columns: Vec<DieselColumn>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct DieselColumn {
    pub name: String,
    pub sql_type: String,
    pub is_nullable: bool,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct DieselDerive {
    pub struct_name: String,
    pub derives: Vec<String>,
    pub associations: Vec<String>,
}

fn extract_struct_info(struct_item: &ItemStruct) -> Result<RustStruct, String> {
    let name = struct_item.ident.to_string();

    let mut fields = Vec::new();
    let mut attributes = Vec::new();

    // Extract struct attributes
    for attr in &struct_item.attrs {
        attributes.push(attr.to_token_stream().to_string());
    }

    // Extract fields
    match &struct_item.fields {
        Fields::Named(named_fields) => {
            for field in &named_fields.named {
                match extract_field_info(field) {
                    Ok(field_info) => fields.push(field_info),
                    Err(e) => return Err(format!("Field error: {}", e)),
                }
            }
        }
        Fields::Unnamed(_) => return Err("Tuple structs not supported".to_string()),
        Fields::Unit => {} // Unit structs have no fields
    }

    Ok(RustStruct {
        name,
        fields,
        attributes,
    })
}

fn extract_field_info(field: &Field) -> Result<RustField, String> {
    let name = match &field.ident {
        Some(ident) => ident.to_string(),
        None => return Err("Unnamed field".to_string()),
    };

    let (field_type, is_optional) = extract_type_info(&field.ty)?;

    let mut attributes = Vec::new();
    for attr in &field.attrs {
        attributes.push(attr.to_token_stream().to_string());
    }

    Ok(RustField {
        name,
        field_type,
        is_optional,
        attributes,
    })
}

fn extract_type_info(ty: &Type) -> Result<(String, bool), String> {
    match ty {
        Type::Path(type_path) => {
            let path = &type_path.path;
            if path.segments.len() == 1 {
                let segment = &path.segments[0];
                let ident = segment.ident.to_string();

                // Check for Option<T>
                if ident == "Option" {
                    if let syn::PathArguments::AngleBracketed(args) = &segment.arguments {
                        if args.args.len() == 1 {
                            if let syn::GenericArgument::Type(inner_type) = &args.args[0] {
                                let (inner_type_str, _) = extract_type_info(inner_type)?;
                                return Ok((inner_type_str, true));
                            }
                        }
                    }
                }

                Ok((ident, false))
            } else {
                // Handle multi-segment paths like std::collections::HashMap
                let full_path = path.segments
                    .iter()
                    .map(|seg| seg.ident.to_string())
                    .collect::<Vec<_>>()
                    .join("::");
                Ok((full_path, false))
            }
        }
        Type::Array(_) => Ok(("Array".to_string(), false)),
        Type::Slice(_) => Ok(("Slice".to_string(), false)),
        Type::Ptr(_) => Ok(("Ptr".to_string(), false)),
        Type::Reference(_) => Ok(("Reference".to_string(), false)),
        Type::Tuple(_) => Ok(("Tuple".to_string(), false)),
        _ => Ok(("Unknown".to_string(), false)),
    }
}

fn extract_diesel_derives(struct_item: &ItemStruct) -> Option<DieselDerive> {
    let name = struct_item.ident.to_string();
    let mut derives = Vec::new();
    let mut associations = Vec::new();

    // Parse attributes by converting to string and searching
    for attr in &struct_item.attrs {
        let attr_str = attr.to_token_stream().to_string();

        // Check for derive macros
        if attr_str.contains("# [derive") || attr_str.contains("#[derive") {
            // Extract derive names
            if attr_str.contains("Queryable") {
                derives.push("Queryable".to_string());
            }
            if attr_str.contains("Insertable") {
                derives.push("Insertable".to_string());
            }
            if attr_str.contains("AsChangeset") {
                derives.push("AsChangeset".to_string());
            }
            if attr_str.contains("Associations") {
                derives.push("Associations".to_string());
            }
            if attr_str.contains("Identifiable") {
                derives.push("Identifiable".to_string());
            }
        }

        // Check for table_name
        if attr_str.contains("# [table_name") || attr_str.contains("#[table_name") {
            // Extract table name from = "..." pattern
            if let Some(start) = attr_str.find("= \"") {
                if let Some(end) = attr_str[start + 3..].find('"') {
                    let table_name = attr_str[start + 3..start + 3 + end].to_string();
                    associations.push(table_name);
                }
            }
        }
    }

    if derives.is_empty() && associations.is_empty() {
        None
    } else {
        Some(DieselDerive {
            struct_name: name,
            derives,
            associations,
        })
    }
}

fn extract_diesel_table(macro_item: &syn::ItemMacro) -> Option<DieselTable> {
    // Check if this is a table! macro
    if let Some(path) = &macro_item.mac.path.segments.first() {
        if path.ident == "table" {
            // Try to parse the macro content
            // This is a very simplified parser for basic Diesel table! macros
            let tokens = macro_item.mac.tokens.to_string();

            // Basic parsing of table! { name (primary_key) { columns... } }
            if let Some(table_info) = parse_diesel_table_tokens(&tokens) {
                return Some(table_info);
            }
        }
    }
    None
}

fn parse_diesel_table_tokens(tokens: &str) -> Option<DieselTable> {
    // Parse Diesel table! macro format: table_name (primary_key) { column -> Type, ... }

    let content = tokens.trim();

    // Find table name (first word)
    let table_name_end = content.find(char::is_whitespace)?;
    let table_name = content[..table_name_end].to_string();

    // Find primary key in parentheses
    let pk_start = content.find('(')?;
    let pk_end = content.find(')')?;
    if pk_end <= pk_start {
        return None;
    }

    let pk_content = &content[pk_start + 1..pk_end];
    let primary_key: Vec<String> = pk_content
        .split(',')
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .collect();

    // Find column definitions between braces
    let brace_start = content[pk_end..].find('{')?;
    let brace_end = content[pk_end + brace_start..].find('}')?;
    let columns_content = &content[pk_end + brace_start + 1..pk_end + brace_start + brace_end];

    // Parse columns
    let mut columns = Vec::new();
    for column_def in columns_content.split(',') {
        let column_def = column_def.trim();
        if column_def.is_empty() || column_def == "}" {
            continue;
        }

        if let Some((col_name, sql_type, is_nullable)) = parse_column_def(column_def) {
            columns.push(DieselColumn {
                name: col_name,
                sql_type,
                is_nullable,
            });
        }
    }

    Some(DieselTable {
        name: table_name,
        primary_key,
        columns,
    })
}

fn parse_column_def(def: &str) -> Option<(String, String, bool)> {
    // Parse "column_name -> Type" or "column_name -> Nullable<Type>"
    let parts: Vec<&str> = def.split("->").map(|s| s.trim()).collect();
    if parts.len() == 2 {
        let col_name = parts[0].to_string();
        let type_part = parts[1];

        // Check for Nullable<Type> (may have spaces)
        let (sql_type, is_nullable) = if type_part.contains("Nullable") {
            // Extract inner type from Nullable<...>
            if let Some(start) = type_part.find('<') {
                if let Some(end) = type_part.rfind('>') {
                    let inner_type = &type_part[start + 1..end];
                    (inner_type.trim().to_string(), true)
                } else {
                    (type_part.to_string(), false)
                }
            } else {
                (type_part.to_string(), false)
            }
        } else {
            (type_part.to_string(), false)
        };

        Some((col_name, sql_type, is_nullable))
    } else {
        None
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();

    if args.len() != 2 {
        eprintln!("Usage: {} <rust_file>", args[0]);
        std::process::exit(1);
    }

    let file_path = &args[1];
    let source_code = fs::read_to_string(file_path)?;

    match syn::parse_file(&source_code) {
        Ok(syntax) => {
            let mut structs = Vec::new();
            let mut diesel_tables = Vec::new();
            let mut diesel_derives = Vec::new();

            for item in syntax.items {
                match item {
                    syn::Item::Struct(struct_item) => {
                        match extract_struct_info(&struct_item) {
                            Ok(rust_struct) => structs.push(rust_struct),
                            Err(e) => {
                                eprintln!("Failed to parse struct: {}", e);
                                std::process::exit(1);
                            }
                        }
                        // Extract Diesel derives for this struct
                        if let Some(derive_info) = extract_diesel_derives(&struct_item) {
                            diesel_derives.push(derive_info);
                        }
                    }
                    syn::Item::Macro(macro_item) => {
                        if let Some(table) = extract_diesel_table(&macro_item) {
                            diesel_tables.push(table);
                        }
                    }
                    _ => {} // Ignore other items
                }
            }

            // Output structs, diesel_tables, and diesel_derives
            let output = serde_json::json!({
                "structs": structs,
                "diesel_tables": diesel_tables,
                "diesel_derives": diesel_derives
            });
            println!("{}", serde_json::to_string(&output)?);
            Ok(())
        }
        Err(e) => {
            eprintln!("Parse error: {}", e);
            std::process::exit(1);
        }
    }
}