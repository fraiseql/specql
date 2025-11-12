from src.pattern_library.api import PatternLibrary

def test_pattern_library_initialization():
    """Test PatternLibrary initialization"""
    library = PatternLibrary(db_path=":memory:")

    # Should initialize schema
    assert library.db is not None
    assert library.get_all_patterns() == []

def test_add_pattern():
    """Test adding a pattern to library"""
    library = PatternLibrary(db_path=":memory:")

    pattern_id = library.add_pattern(
        name="declare",
        category="primitive",
        abstract_syntax={
            "type": "declare",
            "fields": ["variable_name", "variable_type", "default_value"]
        },
        description="Declare a variable"
    )

    assert pattern_id > 0

    # Verify retrieval
    pattern = library.get_pattern("declare")
    assert pattern is not None
    assert pattern["pattern_name"] == "declare"
    assert pattern["pattern_category"] == "primitive"

def test_add_language():
    """Test adding a target language"""
    library = PatternLibrary(db_path=":memory:")

    lang_id = library.add_language(
        name="postgresql",
        ecosystem="postgresql",
        paradigm="declarative",
        version="14+"
    )

    assert lang_id > 0

    languages = library.get_all_languages()
    assert len(languages) == 1
    assert languages[0]["language_name"] == "postgresql"

def test_add_pattern_implementation():
    """Test adding pattern implementation for a language"""
    library = PatternLibrary(db_path=":memory:")

    # Add pattern
    pattern_id = library.add_pattern(
        name="declare",
        category="primitive",
        abstract_syntax={}
    )

    # Add language
    lang_id = library.add_language(
        name="postgresql",
        ecosystem="postgresql",
        paradigm="declarative"
    )

    # Add implementation
    impl_id = library.add_implementation(
        pattern_name="declare",
        language_name="postgresql",
        template="""{{ variable_name }} {{ variable_type }}{% if default_value %} := {{ default_value }}{% endif %};"""
    )

    assert impl_id > 0

    # Retrieve implementation
    impl = library.get_implementation("declare", "postgresql")
    assert impl is not None
    assert "{{ variable_name }}" in impl["implementation_template"]

def test_compile_pattern():
    """Test compiling a pattern to target language"""
    library = PatternLibrary(db_path=":memory:")

    # Setup
    library.add_pattern(name="declare", category="primitive", abstract_syntax={})
    library.add_language(name="postgresql", ecosystem="postgresql", paradigm="declarative")
    library.add_implementation(
        pattern_name="declare",
        language_name="postgresql",
        template="""{{ variable_name }} {{ variable_type }}{% if default_value %} := {{ default_value }}{% endif %};"""
    )

    # Compile
    result = library.compile_pattern(
        pattern_name="declare",
        language_name="postgresql",
        context={
            "variable_name": "total",
            "variable_type": "NUMERIC",
            "default_value": "0"
        }
    )

    assert result == "total NUMERIC := 0;"