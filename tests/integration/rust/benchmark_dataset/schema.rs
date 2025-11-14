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

diesel::table! {
    entity00s (id) {
        id -> Int8,
        uuid -> Uuid,
        name -> Text,
        value -> Int4,
        active -> Bool,
        tags -> Array<Text>,
        metadata -> Jsonb,
        created_at -> Timestamp,
        updated_at -> Timestamp,
        created_by -> Nullable<Uuid>,
        updated_by -> Nullable<Uuid>,
    }
}

diesel::table! {
    entity01s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity00_id -> Int8,
    }
}

diesel::table! {
    entity02s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity01_id -> Int8,
    }
}

diesel::table! {
    entity03s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity02_id -> Int8,
    }
}

diesel::table! {
    entity04s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        entity03_id -> Int8,
    }
}

diesel::table! {
    entity05s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
    }
}

diesel::table! {
    entity06s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity05_id -> Int8,
    }
}

diesel::table! {
    entity07s (id) {
        id -> Int8,
        uuid -> Uuid,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity06_id -> Int8,
    }
}

diesel::table! {
    entity08s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        entity07_id -> Int8,
    }
}

diesel::table! {
    entity09s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity08_id -> Int8,
    }
}

diesel::table! {
    entity10s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
    }
}

diesel::table! {
    entity11s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        metadata -> Jsonb,
        status -> Text,
        entity00_id -> Int8,
    }
}

diesel::table! {
    entity12s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
        entity01_id -> Int8,
    }
}

diesel::table! {
    entity13s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        tags -> Array<Text>,
        status -> Text,
        entity02_id -> Int8,
    }
}

diesel::table! {
    entity14s (id) {
        id -> Int8,
        uuid -> Uuid,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity03_id -> Int8,
    }
}

diesel::table! {
    entity15s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
        status -> Text,
    }
}

diesel::table! {
    entity16s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        entity05_id -> Int8,
    }
}

diesel::table! {
    entity17s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity06_id -> Int8,
    }
}

diesel::table! {
    entity18s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity07_id -> Int8,
    }
}

diesel::table! {
    entity19s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity08_id -> Int8,
        created_at -> Timestamp,
        updated_at -> Timestamp,
        created_by -> Nullable<Uuid>,
        updated_by -> Nullable<Uuid>,
    }
}

diesel::table! {
    entity20s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
    }
}

diesel::table! {
    entity21s (id) {
        id -> Int8,
        uuid -> Uuid,
        name -> Text,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity00_id -> Int8,
    }
}

diesel::table! {
    entity22s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        metadata -> Jsonb,
        status -> Text,
        entity01_id -> Int8,
    }
}

diesel::table! {
    entity23s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity02_id -> Int8,
    }
}

diesel::table! {
    entity24s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
        entity03_id -> Int8,
    }
}

diesel::table! {
    entity25s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
    }
}

diesel::table! {
    entity26s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        tags -> Array<Text>,
        status -> Text,
        entity05_id -> Int8,
    }
}

diesel::table! {
    entity27s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity06_id -> Int8,
    }
}

diesel::table! {
    entity28s (id) {
        id -> Int8,
        uuid -> Uuid,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        entity07_id -> Int8,
    }
}

diesel::table! {
    entity29s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity08_id -> Int8,
    }
}

diesel::table! {
    entity30s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
        status -> Text,
    }
}

diesel::table! {
    entity31s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity00_id -> Int8,
    }
}

diesel::table! {
    entity32s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        entity01_id -> Int8,
    }
}

diesel::table! {
    entity33s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
        metadata -> Jsonb,
        status -> Text,
        entity02_id -> Int8,
    }
}

diesel::table! {
    entity34s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity03_id -> Int8,
    }
}

diesel::table! {
    entity35s (id) {
        id -> Int8,
        uuid -> Uuid,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
    }
}

diesel::table! {
    entity36s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
        entity05_id -> Int8,
    }
}

diesel::table! {
    entity37s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity06_id -> Int8,
    }
}

diesel::table! {
    entity38s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity07_id -> Int8,
        created_at -> Timestamp,
        updated_at -> Timestamp,
        created_by -> Nullable<Uuid>,
        updated_by -> Nullable<Uuid>,
    }
}

diesel::table! {
    entity39s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
        tags -> Array<Text>,
        status -> Text,
        entity08_id -> Int8,
    }
}

diesel::table! {
    entity40s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
    }
}

diesel::table! {
    entity41s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity00_id -> Int8,
    }
}

diesel::table! {
    entity42s (id) {
        id -> Int8,
        uuid -> Uuid,
        name -> Text,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity01_id -> Int8,
    }
}

diesel::table! {
    entity43s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity02_id -> Int8,
    }
}

diesel::table! {
    entity44s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        metadata -> Jsonb,
        entity03_id -> Int8,
    }
}

diesel::table! {
    entity45s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
        status -> Text,
    }
}

diesel::table! {
    entity46s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity05_id -> Int8,
    }
}

diesel::table! {
    entity47s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity06_id -> Int8,
    }
}

diesel::table! {
    entity48s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
        entity07_id -> Int8,
    }
}

diesel::table! {
    entity49s (id) {
        id -> Int8,
        uuid -> Uuid,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity08_id -> Int8,
    }
}

diesel::table! {
    entity50s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
    }
}

diesel::table! {
    entity51s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity00_id -> Int8,
    }
}

diesel::table! {
    entity52s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        tags -> Array<Text>,
        entity01_id -> Int8,
    }
}

diesel::table! {
    entity53s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity02_id -> Int8,
    }
}

diesel::table! {
    entity54s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity03_id -> Int8,
    }
}

diesel::table! {
    entity55s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        metadata -> Jsonb,
        status -> Text,
    }
}

diesel::table! {
    entity56s (id) {
        id -> Int8,
        uuid -> Uuid,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        entity05_id -> Int8,
    }
}

diesel::table! {
    entity57s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity06_id -> Int8,
        created_at -> Timestamp,
        updated_at -> Timestamp,
        created_by -> Nullable<Uuid>,
        updated_by -> Nullable<Uuid>,
    }
}

diesel::table! {
    entity58s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity07_id -> Int8,
    }
}

diesel::table! {
    entity59s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity08_id -> Int8,
    }
}

diesel::table! {
    entity60s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
    }
}

diesel::table! {
    entity61s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity00_id -> Int8,
    }
}

diesel::table! {
    entity62s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity01_id -> Int8,
    }
}

diesel::table! {
    entity63s (id) {
        id -> Int8,
        uuid -> Uuid,
        name -> Text,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity02_id -> Int8,
    }
}

diesel::table! {
    entity64s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        entity03_id -> Int8,
    }
}

diesel::table! {
    entity65s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        tags -> Array<Text>,
        status -> Text,
    }
}

diesel::table! {
    entity66s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
        metadata -> Jsonb,
        status -> Text,
        entity05_id -> Int8,
    }
}

diesel::table! {
    entity67s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity06_id -> Int8,
    }
}

diesel::table! {
    entity68s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        entity07_id -> Int8,
    }
}

diesel::table! {
    entity69s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity08_id -> Int8,
    }
}

diesel::table! {
    entity70s (id) {
        id -> Int8,
        uuid -> Uuid,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
    }
}

diesel::table! {
    entity71s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity00_id -> Int8,
    }
}

diesel::table! {
    entity72s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
        entity01_id -> Int8,
    }
}

diesel::table! {
    entity73s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity02_id -> Int8,
    }
}

diesel::table! {
    entity74s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity03_id -> Int8,
    }
}

diesel::table! {
    entity75s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
        status -> Text,
    }
}

diesel::table! {
    entity76s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        entity05_id -> Int8,
        created_at -> Timestamp,
        updated_at -> Timestamp,
        created_by -> Nullable<Uuid>,
        updated_by -> Nullable<Uuid>,
    }
}

diesel::table! {
    entity77s (id) {
        id -> Int8,
        uuid -> Uuid,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        metadata -> Jsonb,
        status -> Text,
        entity06_id -> Int8,
    }
}

diesel::table! {
    entity78s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
        tags -> Array<Text>,
        status -> Text,
        entity07_id -> Int8,
    }
}

diesel::table! {
    entity79s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity08_id -> Int8,
    }
}

diesel::table! {
    entity80s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
    }
}

diesel::table! {
    entity81s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity00_id -> Int8,
    }
}

diesel::table! {
    entity82s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity01_id -> Int8,
    }
}

diesel::table! {
    entity83s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity02_id -> Int8,
    }
}

diesel::table! {
    entity84s (id) {
        id -> Int8,
        uuid -> Uuid,
        name -> Text,
        value -> Int4,
        active -> Bool,
        entity03_id -> Int8,
    }
}

diesel::table! {
    entity85s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
    }
}

diesel::table! {
    entity86s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity05_id -> Int8,
    }
}

diesel::table! {
    entity87s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity06_id -> Int8,
    }
}

diesel::table! {
    entity88s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        metadata -> Jsonb,
        entity07_id -> Int8,
    }
}

diesel::table! {
    entity89s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity08_id -> Int8,
    }
}

diesel::table! {
    entity90s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
        status -> Text,
    }
}

diesel::table! {
    entity91s (id) {
        id -> Int8,
        uuid -> Uuid,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        tags -> Array<Text>,
        status -> Text,
        entity00_id -> Int8,
    }
}

diesel::table! {
    entity92s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        entity01_id -> Int8,
    }
}

diesel::table! {
    entity93s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity02_id -> Int8,
    }
}

diesel::table! {
    entity94s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity03_id -> Int8,
    }
}

diesel::table! {
    entity95s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        created_at -> Timestamp,
        updated_at -> Timestamp,
        created_by -> Nullable<Uuid>,
        updated_by -> Nullable<Uuid>,
    }
}

diesel::table! {
    entity96s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
        entity05_id -> Int8,
    }
}

diesel::table! {
    entity97s (id) {
        id -> Int8,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity06_id -> Int8,
    }
}

diesel::table! {
    entity98s (id) {
        id -> Int8,
        uuid -> Uuid,
        name -> Text,
        description -> Nullable<Text>,
        value -> Int4,
        active -> Bool,
        status -> Text,
        entity07_id -> Int8,
    }
}

diesel::table! {
    entity99s (id) {
        id -> Int8,
        name -> Text,
        value -> Int4,
        active -> Bool,
        metadata -> Jsonb,
        status -> Text,
        entity08_id -> Int8,
    }
}

diesel::joinable!(entity01s -> entity00s (entity00_id));

diesel::joinable!(entity02s -> entity01s (entity01_id));

diesel::joinable!(entity03s -> entity02s (entity02_id));

diesel::joinable!(entity04s -> entity03s (entity03_id));

diesel::joinable!(entity06s -> entity05s (entity05_id));

diesel::joinable!(entity07s -> entity06s (entity06_id));

diesel::joinable!(entity08s -> entity07s (entity07_id));

diesel::joinable!(entity09s -> entity08s (entity08_id));

diesel::joinable!(entity11s -> entity00s (entity00_id));

diesel::joinable!(entity12s -> entity01s (entity01_id));

diesel::joinable!(entity13s -> entity02s (entity02_id));

diesel::joinable!(entity14s -> entity03s (entity03_id));

diesel::joinable!(entity16s -> entity05s (entity05_id));

diesel::joinable!(entity17s -> entity06s (entity06_id));

diesel::joinable!(entity18s -> entity07s (entity07_id));

diesel::joinable!(entity19s -> entity08s (entity08_id));

diesel::joinable!(entity21s -> entity00s (entity00_id));

diesel::joinable!(entity22s -> entity01s (entity01_id));

diesel::joinable!(entity23s -> entity02s (entity02_id));

diesel::joinable!(entity24s -> entity03s (entity03_id));

diesel::joinable!(entity26s -> entity05s (entity05_id));

diesel::joinable!(entity27s -> entity06s (entity06_id));

diesel::joinable!(entity28s -> entity07s (entity07_id));

diesel::joinable!(entity29s -> entity08s (entity08_id));

diesel::joinable!(entity31s -> entity00s (entity00_id));

diesel::joinable!(entity32s -> entity01s (entity01_id));

diesel::joinable!(entity33s -> entity02s (entity02_id));

diesel::joinable!(entity34s -> entity03s (entity03_id));

diesel::joinable!(entity36s -> entity05s (entity05_id));

diesel::joinable!(entity37s -> entity06s (entity06_id));

diesel::joinable!(entity38s -> entity07s (entity07_id));

diesel::joinable!(entity39s -> entity08s (entity08_id));

diesel::joinable!(entity41s -> entity00s (entity00_id));

diesel::joinable!(entity42s -> entity01s (entity01_id));

diesel::joinable!(entity43s -> entity02s (entity02_id));

diesel::joinable!(entity44s -> entity03s (entity03_id));

diesel::joinable!(entity46s -> entity05s (entity05_id));

diesel::joinable!(entity47s -> entity06s (entity06_id));

diesel::joinable!(entity48s -> entity07s (entity07_id));

diesel::joinable!(entity49s -> entity08s (entity08_id));

diesel::joinable!(entity51s -> entity00s (entity00_id));

diesel::joinable!(entity52s -> entity01s (entity01_id));

diesel::joinable!(entity53s -> entity02s (entity02_id));

diesel::joinable!(entity54s -> entity03s (entity03_id));

diesel::joinable!(entity56s -> entity05s (entity05_id));

diesel::joinable!(entity57s -> entity06s (entity06_id));

diesel::joinable!(entity58s -> entity07s (entity07_id));

diesel::joinable!(entity59s -> entity08s (entity08_id));

diesel::joinable!(entity61s -> entity00s (entity00_id));

diesel::joinable!(entity62s -> entity01s (entity01_id));

diesel::joinable!(entity63s -> entity02s (entity02_id));

diesel::joinable!(entity64s -> entity03s (entity03_id));

diesel::joinable!(entity66s -> entity05s (entity05_id));

diesel::joinable!(entity67s -> entity06s (entity06_id));

diesel::joinable!(entity68s -> entity07s (entity07_id));

diesel::joinable!(entity69s -> entity08s (entity08_id));

diesel::joinable!(entity71s -> entity00s (entity00_id));

diesel::joinable!(entity72s -> entity01s (entity01_id));

diesel::joinable!(entity73s -> entity02s (entity02_id));

diesel::joinable!(entity74s -> entity03s (entity03_id));

diesel::joinable!(entity76s -> entity05s (entity05_id));

diesel::joinable!(entity77s -> entity06s (entity06_id));

diesel::joinable!(entity78s -> entity07s (entity07_id));

diesel::joinable!(entity79s -> entity08s (entity08_id));

diesel::joinable!(entity81s -> entity00s (entity00_id));

diesel::joinable!(entity82s -> entity01s (entity01_id));

diesel::joinable!(entity83s -> entity02s (entity02_id));

diesel::joinable!(entity84s -> entity03s (entity03_id));

diesel::joinable!(entity86s -> entity05s (entity05_id));

diesel::joinable!(entity87s -> entity06s (entity06_id));

diesel::joinable!(entity88s -> entity07s (entity07_id));

diesel::joinable!(entity89s -> entity08s (entity08_id));

diesel::joinable!(entity91s -> entity00s (entity00_id));

diesel::joinable!(entity92s -> entity01s (entity01_id));

diesel::joinable!(entity93s -> entity02s (entity02_id));

diesel::joinable!(entity94s -> entity03s (entity03_id));

diesel::joinable!(entity96s -> entity05s (entity05_id));

diesel::joinable!(entity97s -> entity06s (entity06_id));

diesel::joinable!(entity98s -> entity07s (entity07_id));

diesel::joinable!(entity99s -> entity08s (entity08_id));

diesel::allow_tables_to_appear_in_same_query!(
    entity00s,    entity01s,    entity02s,    entity03s,    entity04s,    entity05s,    entity06s,    entity07s,    entity08s,    entity09s,    entity10s,    entity11s,    entity12s,    entity13s,    entity14s,    entity15s,    entity16s,    entity17s,    entity18s,    entity19s,    entity20s,    entity21s,    entity22s,    entity23s,    entity24s,    entity25s,    entity26s,    entity27s,    entity28s,    entity29s,    entity30s,    entity31s,    entity32s,    entity33s,    entity34s,    entity35s,    entity36s,    entity37s,    entity38s,    entity39s,    entity40s,    entity41s,    entity42s,    entity43s,    entity44s,    entity45s,    entity46s,    entity47s,    entity48s,    entity49s,    entity50s,    entity51s,    entity52s,    entity53s,    entity54s,    entity55s,    entity56s,    entity57s,    entity58s,    entity59s,    entity60s,    entity61s,    entity62s,    entity63s,    entity64s,    entity65s,    entity66s,    entity67s,    entity68s,    entity69s,    entity70s,    entity71s,    entity72s,    entity73s,    entity74s,    entity75s,    entity76s,    entity77s,    entity78s,    entity79s,    entity80s,    entity81s,    entity82s,    entity83s,    entity84s,    entity85s,    entity86s,    entity87s,    entity88s,    entity89s,    entity90s,    entity91s,    entity92s,    entity93s,    entity94s,    entity95s,    entity96s,    entity97s,    entity98s,    entity99s,
    simples,
);
