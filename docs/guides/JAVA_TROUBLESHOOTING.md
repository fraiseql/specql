# Java Integration Troubleshooting Guide

## Common Issues and Solutions

### Issue: Import Errors in Tests

**Symptoms**: Tests fail with "Import could not be resolved" errors

**Cause**: Module path issues or missing dependencies

**Solution**:
```bash
# Check that all required modules are installed
uv sync

# Run tests with proper Python path
PYTHONPATH=/home/lionel/code/specql uv run pytest tests/integration/java/
```

### Issue: Round-trip Test Failures

**Symptoms**: Entity fields don't match after YAML serialization/deserialization

**Cause**: YAML serializer or parser bugs

**Debug**:
```python
# Check YAML output
from src.core.yaml_serializer import YAMLSerializer
from src.parsers.java.spring_boot_parser import SpringBootParser

parser = SpringBootParser()
entity = parser.parse_entity_file("path/to/entity.java")
serializer = YAMLSerializer()
yaml_content = serializer.serialize(entity)
print(yaml_content)
```

### Issue: Performance Issues

**Symptoms**: Parsing takes longer than expected

**Cause**: Large codebases or inefficient parsing

**Solution**:
- Break large projects into smaller modules
- Use parallel processing for multiple files
- Profile with `cProfile` to identify bottlenecks

### Issue: Missing Annotations in Generated Code

**Symptoms**: Generated Java files missing JPA annotations

**Cause**: Generator bugs or incomplete templates

**Check**:
- Verify entity generator templates
- Check that all required annotations are included
- Compare with original source files

### Issue: Relationship Mapping Errors

**Symptoms**: Foreign key relationships not working correctly

**Cause**: Incorrect reference parsing or generation

**Debug**:
```python
# Check parsed relationships
entities = parser.parse_project("project/path")
for entity in entities:
    for field in entity.fields:
        if field.type.value == "reference":
            print(f"{entity.name}.{field.name} -> {field.references}")
```

## Getting Help

1. Check existing tests in `tests/integration/java/`
2. Review the migration guide
3. File an issue on GitHub with:
   - Error messages
   - Sample code that fails
   - Expected vs actual behavior