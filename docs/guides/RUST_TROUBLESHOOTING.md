# Rust Troubleshooting Guide

This guide helps resolve common issues when using SpecQL with Rust projects.

## Installation Issues

### Rust Parser Binary Not Found

**Error:**
```
ImportError: Rust parser binary not found at /path/to/specql/rust/target/release/specql_rust_parser
```

**Solutions:**

1. **Build the Rust parser:**
   ```bash
   cd rust
   cargo build --release
   ```

2. **Check binary location:**
   ```bash
   ls -la rust/target/release/specql_rust_parser
   ```

3. **Reinstall SpecQL:**
   ```bash
   pip install -e . --force-reinstall
   ```

### PyO3 Compatibility Issues

**Error:**
```
error: the configured Python interpreter version (3.13) is newer than PyO3's maximum supported version (3.12)
```

**Solution:** The current implementation uses subprocess instead of PyO3, so this should not occur. If you see this error, ensure you're using the subprocess-based parser.

## Parsing Errors

### Unsupported Struct Syntax

**Error:**
```
Failed to parse struct: Tuple structs not supported
```

**Problem:** SpecQL currently only supports named structs, not tuple structs.

**Solutions:**

1. **Convert tuple struct to named struct:**
   ```rust
   // ❌ Not supported
   pub struct Point(i32, i32);

   // ✅ Supported
   pub struct Point {
       pub x: i32,
       pub y: i32,
   }
   ```

### Complex Generic Types

**Error:**
```
Warning: Unknown type mapping for ComplexType<Inner<T>>
```

**Problem:** Very complex generic types may not be fully parsed.

**Solutions:**

1. **Simplify type aliases:**
   ```rust
   // Instead of complex generics
   pub field: HashMap<String, Vec<Option<CustomType>>>

   // Use type aliases
   type CustomMap = HashMap<String, Vec<Option<CustomType>>>;
   pub field: CustomMap;
   ```

2. **Use serde_json::Value for complex data:**
   ```rust
   pub field: serde_json::Value;
   ```

### Macro-Heavy Code

**Error:**
```
Parse error: Failed to parse file
```

**Problem:** Code with complex macros or procedural macros may not parse correctly.

**Solutions:**

1. **Extract structs to separate files:**
   ```
   src/
     models/
       user.rs      # Simple structs only
       macros.rs    # Complex macros here
   ```

2. **Use `#[cfg_attr]` carefully:**
   Avoid complex conditional compilation in struct definitions.

## Type Mapping Issues

### Unexpected SQL Types

**Problem:** A Rust type maps to an unexpected SQL type.

**Check the mapping table:**
```rust
// These map as expected:
pub struct Example {
    pub id: i32,        // -> integer
    pub data: Vec<u8>,  // -> jsonb (byte array)
    pub tags: Vec<String>, // -> jsonb (string array)
}
```

**Custom mapping:** Extend the type mapper for project-specific types.

### Nullable Field Issues

**Problem:** `Option<T>` fields are not marked as nullable in the database.

**Check:** This is handled automatically. `Option<String>` becomes a nullable text field.

**Debug:** Check the generated SpecQL YAML for `nullable: true` on the field.

## Performance Issues

### Slow Parsing

**Symptoms:**
- Parsing takes more than 0.1 seconds for typical files
- High CPU usage during parsing

**Solutions:**

1. **Split large files:**
   ```bash
   # Instead of one 1000-line file
   # Split into logical modules
   models/
     user.rs
     product.rs
     order.rs
   ```

2. **Remove unused code:**
   Comment out or remove structs not needed for schema generation.

3. **Check Rust compiler version:**
   ```bash
   rustc --version  # Should be 1.70+
   ```

### Memory Usage

**Problem:** High memory usage with large codebases.

**Solutions:**

1. **Process files individually:**
   ```bash
   specql reverse rust models/user.rs
   specql reverse rust models/product.rs
   # Then combine the YAML files
   ```

2. **Use `--dry-run` for analysis:**
   ```bash
   specql reverse rust src/ --dry-run
   ```

## Relationship Detection

### Foreign Keys Not Detected

**Problem:** Foreign key relationships are not automatically detected.

**Current support:**
- Field naming conventions: `user_id` → references `User`
- Diesel `#[belongs_to(...)]` attributes (basic support)

**Manual specification:** Add relationships in the SpecQL YAML:
```yaml
entities:
  Post:
    fields:
      user_id:
        type: integer
        references: User
```

### Belongs To Parsing Issues

**Problem:** `#[belongs_to(User)]` attributes are not parsed correctly.

**Check syntax:**
```rust
// ✅ Correct
#[belongs_to(User)]
pub user_id: i32,

// ✅ With custom foreign key
#[belongs_to(Category, foreign_key = "category_id")]
pub category_id: Option<i32>,

// ❌ Incorrect (quotes around entity name)
#[belongs_to("User")]
pub user_id: i32,
```

## Code Generation Issues

### Generated Code Won't Compile

**Problem:** Generated Rust code has compilation errors.

**Check:**

1. **Dependencies:** Ensure all required crates are in `Cargo.toml`
2. **Import paths:** Check that generated imports match your project structure
3. **Type compatibility:** Verify that generated types match your expectations

**Regenerate:** Clean and regenerate:
```bash
rm -rf generated/
specql generate --input schema.yaml --language rust
```

## Integration Issues

### CLI Commands Not Working

**Problem:** `specql reverse rust` commands fail.

**Check:**

1. **Python path:** Ensure SpecQL is properly installed
2. **File permissions:** Check read access to Rust files
3. **Working directory:** Run from project root

**Debug:**
```bash
python -c "from src.reverse_engineering.rust_parser import RustParser; print('Import works')"
```

### IDE Integration

**Problem:** IDE shows import errors for generated code.

**Solutions:**

1. **Add to .gitignore:** Exclude generated files from version control
2. **IDE settings:** Configure IDE to ignore generated directories
3. **Separate crate:** Put generated code in a separate Cargo workspace member

## Advanced Troubleshooting

### Debug Logging

Enable debug logging:
```bash
export RUST_LOG=debug
specql reverse rust models/ --verbose
```

### Manual Testing

Test components individually:
```python
from src.reverse_engineering.rust_parser import RustParser

parser = RustParser()
structs = parser.parse_file("test.rs")
print(f"Found {len(structs)} structs")
```

### Parser Binary Issues

**Check binary:**
```bash
# Test the Rust binary directly
./rust/target/release/specql_rust_parser --help

# Check if it can parse a simple file
echo 'pub struct Test { pub id: i32 }' > test.rs
./rust/target/release/specql_rust_parser test.rs
```

### Version Compatibility

**Check versions:**
```bash
python --version      # 3.11+
rustc --version       # 1.70+
cargo --version       # 1.70+
```

## Common Workarounds

### Complex Diesel Schemas

For complex Diesel schemas with macros, use manual SpecQL definitions:

```yaml
# schema.yaml
entities:
  User:
    fields:
      id: integer
      name: text
      email: text
    # Add manual relationships and constraints
```

### Legacy Code

For code with unsupported syntax:

1. Create wrapper structs for SpecQL parsing
2. Use `#[cfg(specql)]` attributes to conditionally compile
3. Maintain separate "schema structs" for SpecQL

### Large Codebases

For very large Rust projects:

1. **Selective parsing:** Only parse model files
2. **Incremental updates:** Update schema files incrementally
3. **Caching:** Cache parsed results where possible

## Getting Help

### Information to Provide

When reporting issues, include:

1. **SpecQL version:** `specql --version`
2. **Rust version:** `rustc --version`
3. **Python version:** `python --version`
4. **Error messages:** Full error output
5. **Sample code:** Minimal Rust code that reproduces the issue
6. **Expected vs actual:** What you expected vs what happened

### Test Cases

Run the test suite:
```bash
# Unit tests
pytest tests/unit/reverse_engineering/rust/

# Integration tests
pytest tests/integration/rust/

# Performance tests
python tests/performance/test_rust_parsing_performance.py
```

### Community Support

- **GitHub Issues:** Report bugs and request features
- **Documentation:** Check for updates in the migration guide
- **Examples:** Review working examples in the test suite