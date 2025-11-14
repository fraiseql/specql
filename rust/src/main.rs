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

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ImplMethod {
    pub name: String,
    pub visibility: String,
    pub parameters: Vec<MethodParam>,
    pub return_type: String,
    pub is_async: bool,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct MethodParam {
    pub name: String,
    pub param_type: String,
    pub is_mut: bool,
    pub is_ref: bool,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct ImplBlock {
    pub type_name: String,
    pub methods: Vec<ImplMethod>,
    pub trait_impl: Option<String>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct RouteHandler {
    pub method: String, // GET, POST, PUT, DELETE, etc.
    pub path: String,
    pub function_name: String,
    pub is_async: bool,
    pub return_type: String,
    pub parameters: Vec<MethodParam>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct RustEnum {
    pub name: String,
    pub variants: Vec<RustEnumVariant>,
    pub attributes: Vec<String>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct RustEnumVariant {
    pub name: String,
    pub fields: Option<Vec<RustField>>, // Some for tuple/struct variants, None for unit variants
    pub discriminant: Option<String>, // For explicit discriminants like Variant = 1
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

fn extract_impl_blocks(file: &syn::File) -> Vec<ImplBlock> {
    let mut impl_blocks = Vec::new();

    for item in &file.items {
        if let syn::Item::Impl(impl_item) = item {
            let type_name = extract_impl_type_name(impl_item);
            let methods = extract_impl_methods(impl_item);
            let trait_impl = extract_trait_name(impl_item);

            if !methods.is_empty() {
                impl_blocks.push(ImplBlock {
                    type_name,
                    methods,
                    trait_impl,
                });
            }
        }
    }

    impl_blocks
}

fn extract_impl_type_name(impl_item: &syn::ItemImpl) -> String {
    match &*impl_item.self_ty {
        syn::Type::Path(type_path) => {
            if let Some(segment) = type_path.path.segments.last() {
                segment.ident.to_string()
            } else {
                "Unknown".to_string()
            }
        }
        _ => "Unknown".to_string(),
    }
}

fn extract_trait_name(impl_item: &syn::ItemImpl) -> Option<String> {
    impl_item.trait_.as_ref().map(|(_, trait_path, _)| {
        trait_path.segments.iter()
            .map(|seg| seg.ident.to_string())
            .collect::<Vec<_>>()
            .join("::")
    })
}

fn extract_impl_methods(impl_item: &syn::ItemImpl) -> Vec<ImplMethod> {
    let mut methods = Vec::new();

    for item in &impl_item.items {
        if let syn::ImplItem::Fn(method) = item {
            if let Some(impl_method) = extract_method_info(method) {
                methods.push(impl_method);
            }
        }
    }

    methods
}

fn extract_method_info(method: &syn::ImplItemFn) -> Option<ImplMethod> {
    let name = method.sig.ident.to_string();
    let visibility = extract_visibility(&method.vis);
    let parameters = extract_method_params(&method.sig.inputs);
    let return_type = extract_return_type(&method.sig.output);
    let is_async = method.sig.asyncness.is_some();

    Some(ImplMethod {
        name,
        visibility,
        parameters,
        return_type,
        is_async,
    })
}

fn extract_visibility(vis: &syn::Visibility) -> String {
    match vis {
        syn::Visibility::Public(_) => "pub".to_string(),
        syn::Visibility::Restricted(restricted) => {
            format!("pub({})", restricted.path.segments.iter().map(|seg| seg.ident.to_string()).collect::<Vec<_>>().join("::"))
        }
        syn::Visibility::Inherited => "private".to_string(),
    }
}

fn extract_method_params(inputs: &syn::punctuated::Punctuated<syn::FnArg, syn::Token![,]>) -> Vec<MethodParam> {
    let mut params = Vec::new();

    for arg in inputs {
        match arg {
            syn::FnArg::Receiver(receiver) => {
                // Handle &self, &mut self, self
                let (param_type, is_mut, is_ref) = if receiver.reference.is_some() {
                    if receiver.mutability.is_some() {
                        ("&mut self".to_string(), true, true)
                    } else {
                        ("&self".to_string(), false, true)
                    }
                } else if receiver.mutability.is_some() {
                    ("mut self".to_string(), true, false)
                } else {
                    ("self".to_string(), false, false)
                };

                params.push(MethodParam {
                    name: "self".to_string(),
                    param_type,
                    is_mut,
                    is_ref,
                });
            }
            syn::FnArg::Typed(pat_type) => {
                if let syn::Pat::Ident(pat_ident) = &*pat_type.pat {
                    let name = pat_ident.ident.to_string();
                    let (param_type, is_mut, is_ref) = extract_param_type_info(&pat_type.ty);

                    params.push(MethodParam {
                        name,
                        param_type,
                        is_mut,
                        is_ref,
                    });
                }
            }
        }
    }

    params
}

fn extract_param_type_info(ty: &syn::Type) -> (String, bool, bool) {
    match ty {
        syn::Type::Reference(type_ref) => {
            let inner_type = extract_type_string(&type_ref.elem);
            let is_mut = type_ref.mutability.is_some();
            (format!("&{}", if is_mut { "mut " } else { "" }) + &inner_type, is_mut, true)
        }
        _ => (extract_type_string(ty), false, false),
    }
}

fn extract_type_string(ty: &syn::Type) -> String {
    match ty {
        syn::Type::Path(type_path) => {
            let mut result = String::new();
            for (i, segment) in type_path.path.segments.iter().enumerate() {
                if i > 0 {
                    result.push_str("::");
                }
                result.push_str(&segment.ident.to_string());

                // Handle generic arguments
                match &segment.arguments {
                    syn::PathArguments::AngleBracketed(args) => {
                        result.push('<');
                        for (j, arg) in args.args.iter().enumerate() {
                            if j > 0 {
                                result.push_str(", ");
                            }
                            match arg {
                                syn::GenericArgument::Type(inner_ty) => {
                                    result.push_str(&extract_type_string(inner_ty));
                                }
                                _ => result.push_str("..."),
                            }
                        }
                        result.push('>');
                    }
                    syn::PathArguments::Parenthesized(_args) => {
                        result.push('(');
                        // For function types, just indicate it's a function
                        result.push_str("...)");
                    }
                    _ => {} // None or other types
                }
            }
            result
        }
        syn::Type::Tuple(tuple) => {
            if tuple.elems.is_empty() {
                "()".to_string() // Unit type
            } else {
                "Tuple".to_string()
            }
        }
        syn::Type::Slice(_) => "Slice".to_string(),
        syn::Type::Array(_) => "Array".to_string(),
        syn::Type::Reference(type_ref) => {
            let mut result = String::new();
            result.push('&');
            if type_ref.mutability.is_some() {
                result.push_str("mut ");
            }
            result.push_str(&extract_type_string(&type_ref.elem));
            result
        }
        _ => "Unknown".to_string(),
    }
}

fn extract_route_handlers(file: &syn::File) -> Vec<RouteHandler> {
    let mut routes = Vec::new();

    for item in &file.items {
        if let syn::Item::Fn(fn_item) = item {
            // Check for route attributes like #[get("/path")], #[post("/path")], etc.
            for attr in &fn_item.attrs {
                if let Some(route_info) = extract_route_info(attr) {
                    let method = route_info.0;
                    let path = route_info.1;

                    let function_name = fn_item.sig.ident.to_string();
                    let is_async = fn_item.sig.asyncness.is_some();
                    let return_type = extract_return_type(&fn_item.sig.output);
                    let parameters = extract_method_params(&fn_item.sig.inputs);

                    routes.push(RouteHandler {
                        method,
                        path,
                        function_name,
                        is_async,
                        return_type,
                        parameters,
                    });
                    break; // Only take the first route attribute
                }
            }
        }
    }

    routes
}

fn extract_enum_info(enum_item: &syn::ItemEnum) -> Result<RustEnum, String> {
    let name = enum_item.ident.to_string();

    let mut attributes = Vec::new();
    for attr in &enum_item.attrs {
        attributes.push(attr.to_token_stream().to_string());
    }

    let mut variants = Vec::new();
    for variant in &enum_item.variants {
        let variant_info = extract_enum_variant_info(variant)?;
        variants.push(variant_info);
    }

    Ok(RustEnum {
        name,
        variants,
        attributes,
    })
}

fn extract_enum_variant_info(variant: &syn::Variant) -> Result<RustEnumVariant, String> {
    let name = variant.ident.to_string();

    let fields = match &variant.fields {
        syn::Fields::Unit => None,
        syn::Fields::Unnamed(fields) => {
            let mut field_list = Vec::new();
            for (i, field) in fields.unnamed.iter().enumerate() {
                let field_name = format!("field_{}", i); // Unnamed fields get indexed names
                let (field_type, _) = extract_type_info(&field.ty)?;
                let rust_field = RustField {
                    name: field_name,
                    field_type,
                    is_optional: false,
                    attributes: Vec::new(),
                };
                field_list.push(rust_field);
            }
            Some(field_list)
        }
        syn::Fields::Named(fields) => {
            let mut field_list = Vec::new();
            for field in &fields.named {
                let rust_field = extract_field_info(field)?;
                field_list.push(rust_field);
            }
            Some(field_list)
        }
    };

    let discriminant = variant.discriminant.as_ref().map(|(_, expr)| {
        expr.to_token_stream().to_string()
    });

    Ok(RustEnumVariant {
        name,
        fields,
        discriminant,
    })
}

fn extract_route_info(attr: &syn::Attribute) -> Option<(String, String)> {
    // Check if this is a route attribute like #[get("/path")] or #[route(method, "/path")]
    let attr_str = attr.to_token_stream().to_string();

    // Actix-web style: #[get("/path")], #[post("/path")], etc.
    let actix_methods = ["get", "post", "put", "delete", "patch", "head", "options"];
    for method in &actix_methods {
        let pattern = format!("# [{} (", method);
        if attr_str.starts_with(&pattern) {
            // Extract the path from #[method("/path")]
            if let Some(start) = attr_str.find('(') {
                if let Some(end) = attr_str.find(')') {
                    let path_part = &attr_str[start + 1..end];
                    let path = path_part.trim_matches('"').to_string();
                    return Some((method.to_uppercase(), path));
                }
            }
        }
    }

    // Axum style: #[route(GET, "/path")] or #[route(POST, "/users", create_user)]
    // First check for #[route(...)] with method specification
    if attr_str.starts_with("# [route (") {
        // Parse #[route(GET, "/path")] or #[route(POST, "/users", create_user)]
        if let Some(start) = attr_str.find('(') {
            if let Some(end) = attr_str.find(')') {
                let args_part = &attr_str[start + 1..end];
                let args: Vec<&str> = args_part.split(',').map(|s| s.trim()).collect();
                if args.len() >= 2 {
                    let method = args[0].trim_matches('"').to_string();
                    let path = args[1].trim_matches('"').to_string();
                    return Some((method, path));
                }
            }
        }
    }

    // Axum also supports direct method macros like #[get("/path")]
    for method in &actix_methods {
        let axum_pattern = format!("# [axum :: {} (", method);
        if attr_str.starts_with(&axum_pattern) {
            // Extract the path from #[axum::method("/path")]
            if let Some(start) = attr_str.find('(') {
                if let Some(end) = attr_str.find(')') {
                    let path_part = &attr_str[start + 1..end];
                    let path = path_part.trim_matches('"').to_string();
                    return Some((method.to_uppercase(), path));
                }
            }
        }
    }

    None
}

fn extract_return_type(output: &syn::ReturnType) -> String {
    match output {
        syn::ReturnType::Default => "()".to_string(),
        syn::ReturnType::Type(_, ty) => extract_type_string(ty),
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
            let mut enums = Vec::new();
            let mut diesel_tables = Vec::new();
            let mut diesel_derives = Vec::new();
            let impl_blocks = extract_impl_blocks(&syntax);
            let route_handlers = extract_route_handlers(&syntax);

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
                    syn::Item::Enum(enum_item) => {
                        match extract_enum_info(&enum_item) {
                            Ok(rust_enum) => enums.push(rust_enum),
                            Err(e) => {
                                eprintln!("Failed to parse enum: {}", e);
                                std::process::exit(1);
                            }
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

            // Output structs, enums, diesel_tables, diesel_derives, impl_blocks, and route_handlers
            let output = serde_json::json!({
                "structs": structs,
                "enums": enums,
                "diesel_tables": diesel_tables,
                "diesel_derives": diesel_derives,
                "impl_blocks": impl_blocks,
                "route_handlers": route_handlers
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