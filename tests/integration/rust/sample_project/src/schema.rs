diesel::table! {
    products (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        price -> Int4,
        active -> Bool,
        status -> Text,  // Stored as TEXT in DB
        category_id -> Int8,
        created_at -> Timestamp,
        updated_at -> Timestamp,
        deleted_at -> Nullable<Timestamp>,
    }
}

diesel::table! {
    categories (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        created_at -> Timestamp,
        updated_at -> Timestamp,
        deleted_at -> Nullable<Timestamp>,
    }
}

diesel::table! {
    customers (id) {
        id -> Int8,
        first_name -> Text,
        last_name -> Text,
        email -> Text,
        phone -> Nullable<Text>,
        address -> Jsonb,
        created_at -> Timestamp,
        updated_at -> Timestamp,
        deleted_at -> Nullable<Timestamp>,
    }
}

diesel::table! {
    orders (id) {
        id -> Int8,
        customer_id -> Int8,
        status -> Text,
        total_amount -> Int4,
        shipped_at -> Nullable<Timestamp>,
        created_at -> Timestamp,
        updated_at -> Timestamp,
        deleted_at -> Nullable<Timestamp>,
    }
}

diesel::table! {
    order_items (id) {
        id -> Int8,
        order_id -> Int8,
        product_id -> Int8,
        quantity -> Int4,
        unit_price -> Int4,
        created_at -> Timestamp,
        updated_at -> Timestamp,
        deleted_at -> Nullable<Timestamp>,
    }
}

diesel::joinable!(products -> categories (category_id));
diesel::joinable!(orders -> customers (customer_id));
diesel::joinable!(order_items -> orders (order_id));
diesel::joinable!(order_items -> products (product_id));

diesel::table! {
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

diesel::joinable!(simples -> categories (category_id));

diesel::allow_tables_to_appear_in_same_query!(
    products,
    categories,
    customers,
    orders,
    order_items,
    simples,
);