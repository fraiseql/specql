-- Pattern Library Database Schema
-- Multi-language code generation system

-- Table 1: Patterns (Universal primitives)
CREATE TABLE patterns (
    pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_name TEXT NOT NULL UNIQUE,
    pattern_category TEXT NOT NULL, -- primitive, control_flow, query, data_transform
    abstract_syntax TEXT NOT NULL, -- JSON schema for pattern structure
    description TEXT,
    complexity_score INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Table 2: Languages (Target languages)
CREATE TABLE languages (
    language_id INTEGER PRIMARY KEY AUTOINCREMENT,
    language_name TEXT NOT NULL UNIQUE,
    ecosystem TEXT, -- postgresql, python, typescript, ruby
    paradigm TEXT, -- declarative, imperative, functional
    version TEXT, -- e.g., "14+", "3.11+", "5.0+"
    supported BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Table 3: Pattern Implementations (Language-specific code)
CREATE TABLE pattern_implementations (
    implementation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id INTEGER NOT NULL,
    language_id INTEGER NOT NULL,
    implementation_template TEXT NOT NULL, -- Jinja2 template
    supported BOOLEAN DEFAULT TRUE,
    performance_notes TEXT,
    version TEXT DEFAULT '1.0.0',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pattern_id) REFERENCES patterns(pattern_id),
    FOREIGN KEY (language_id) REFERENCES languages(language_id),
    UNIQUE(pattern_id, language_id)
);

-- Table 4: Universal Types (SpecQL type system)
CREATE TABLE universal_types (
    type_id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name TEXT NOT NULL UNIQUE,
    type_category TEXT NOT NULL, -- scalar, composite, collection
    description TEXT,
    json_schema TEXT -- JSON schema definition
);

-- Table 5: Type Mappings (SpecQL types → Language types)
CREATE TABLE type_mappings (
    mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
    universal_type_id INTEGER NOT NULL,
    language_id INTEGER NOT NULL,
    language_type TEXT NOT NULL,
    import_statement TEXT, -- e.g., "from decimal import Decimal"
    validation_rules TEXT, -- JSON with validation logic
    FOREIGN KEY (universal_type_id) REFERENCES universal_types(type_id),
    FOREIGN KEY (language_id) REFERENCES languages(language_id),
    UNIQUE(universal_type_id, language_id)
);

-- Table 6: Expression Patterns (Operators, functions)
CREATE TABLE expression_patterns (
    expression_id INTEGER PRIMARY KEY AUTOINCREMENT,
    expression_name TEXT NOT NULL UNIQUE,
    expression_category TEXT NOT NULL, -- operator, function, aggregate
    arity INTEGER, -- number of arguments
    description TEXT
);

-- Table 7: Expression Implementations (Language-specific operators)
CREATE TABLE expression_implementations (
    expr_implementation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    expression_id INTEGER NOT NULL,
    language_id INTEGER NOT NULL,
    implementation_syntax TEXT NOT NULL,
    example TEXT,
    FOREIGN KEY (expression_id) REFERENCES expression_patterns(expression_id),
    FOREIGN KEY (language_id) REFERENCES languages(language_id),
    UNIQUE(expression_id, language_id)
);

-- Table 8: Language Capabilities (Feature support matrix)
CREATE TABLE language_capabilities (
    capability_id INTEGER PRIMARY KEY AUTOINCREMENT,
    language_id INTEGER NOT NULL,
    capability_name TEXT NOT NULL,
    supported BOOLEAN DEFAULT TRUE,
    workaround_notes TEXT,
    FOREIGN KEY (language_id) REFERENCES languages(language_id),
    UNIQUE(language_id, capability_name)
);

-- Table 9: Pattern Dependencies (Pattern relationships)
CREATE TABLE pattern_dependencies (
    dependency_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id INTEGER NOT NULL,
    depends_on_pattern_id INTEGER NOT NULL,
    dependency_type TEXT NOT NULL, -- requires, suggests, conflicts_with
    FOREIGN KEY (pattern_id) REFERENCES patterns(pattern_id),
    FOREIGN KEY (depends_on_pattern_id) REFERENCES patterns(pattern_id),
    UNIQUE(pattern_id, depends_on_pattern_id)
);

-- ===== TIER 2: Domain Patterns =====

-- Table 10: Domain Patterns (Reusable business logic patterns)
CREATE TABLE domain_patterns (
    domain_pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_name TEXT NOT NULL UNIQUE,
    pattern_category TEXT NOT NULL, -- state_machine, workflow, hierarchy, audit, validation
    description TEXT,
    parameters TEXT NOT NULL, -- JSON schema for pattern parameters
    implementation TEXT NOT NULL, -- JSON with pattern logic in Tier 1 primitives
    usage_count INTEGER DEFAULT 0,
    popularity_score REAL DEFAULT 0.0,
    tags TEXT, -- Comma-separated tags
    icon TEXT, -- Emoji or icon name
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Table 11: Entity Templates (Business entity templates)
CREATE TABLE entity_templates (
    entity_template_id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain_pattern_id INTEGER, -- Optional: based on domain pattern
    template_name TEXT NOT NULL UNIQUE,
    template_namespace TEXT NOT NULL, -- e.g., 'crm', 'ecommerce', 'healthcare'
    description TEXT,
    default_fields TEXT NOT NULL, -- JSON: Fields included in template
    default_patterns TEXT NOT NULL, -- JSON: Domain patterns applied
    default_actions TEXT NOT NULL, -- JSON: Pre-built actions
    configuration_options TEXT, -- JSON: Customization options
    icon TEXT,
    tags TEXT,
    usage_count INTEGER DEFAULT 0,
    popularity_score REAL DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (domain_pattern_id) REFERENCES domain_patterns(domain_pattern_id)
);

-- Table 12: Entity Template Dependencies
CREATE TABLE entity_template_dependencies (
    dependency_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_template_id INTEGER NOT NULL,
    depends_on_template_id INTEGER,
    depends_on_pattern_id INTEGER,
    dependency_type TEXT NOT NULL, -- requires, suggests, conflicts_with
    FOREIGN KEY (entity_template_id) REFERENCES entity_templates(entity_template_id),
    FOREIGN KEY (depends_on_template_id) REFERENCES entity_templates(entity_template_id),
    FOREIGN KEY (depends_on_pattern_id) REFERENCES domain_patterns(domain_pattern_id)
);

-- Table 13: Pattern Instantiations (Track usage)
CREATE TABLE pattern_instantiations (
    instantiation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_name TEXT NOT NULL,
    domain_pattern_id INTEGER,
    entity_template_id INTEGER,
    parameters TEXT, -- JSON parameters used
    instantiated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (domain_pattern_id) REFERENCES domain_patterns(domain_pattern_id),
    FOREIGN KEY (entity_template_id) REFERENCES entity_templates(entity_template_id)
);

-- Indexes
CREATE INDEX idx_patterns_category ON patterns(pattern_category);
CREATE INDEX idx_implementations_pattern ON pattern_implementations(pattern_id);
CREATE INDEX idx_implementations_language ON pattern_implementations(language_id);
CREATE INDEX idx_type_mappings_type ON type_mappings(universal_type_id);
CREATE INDEX idx_type_mappings_language ON type_mappings(language_id);

-- Domain Pattern Indexes
CREATE INDEX idx_domain_patterns_category ON domain_patterns(pattern_category);
CREATE INDEX idx_domain_patterns_popularity ON domain_patterns(popularity_score DESC);

-- Entity Template Indexes
CREATE INDEX idx_entity_templates_namespace ON entity_templates(template_namespace);
CREATE INDEX idx_entity_templates_popularity ON entity_templates(popularity_score DESC);