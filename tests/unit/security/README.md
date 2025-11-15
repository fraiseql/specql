# Security Test Suite

Comprehensive security tests for the SpecQL code generator framework.

## Overview

This test suite provides dedicated security testing coverage for:

1. **SQL Injection** - Tests for SQL injection vulnerabilities
2. **Path Traversal** - Tests for file system path traversal attacks
3. **Command Injection** - Tests for shell command injection vulnerabilities
4. **Expression Fuzzing** - Fuzz testing for the expression compiler
5. **Malformed Input** - Tests for handling large files, deep nesting, and malformed data

## Test Files

### `test_sql_injection.py`

Comprehensive SQL injection tests covering:

- **Basic SQL Injection**: UNION SELECT, DROP TABLE, DELETE FROM, UPDATE, INSERT
- **Advanced SQL Injection**: EXEC functions, extended stored procedures (xp_*), stacked queries
- **Encoded Injection**: Null bytes, newlines, backslashes
- **Subquery Injection**: Malicious subqueries with UNION and dangerous operations
- **Function Call Injection**: Unsafe function calls and malicious arguments
- **Quote Escaping**: Single and double quote injection attempts
- **Field Validation**: Unknown field rejection
- **Operator Validation**: Safe vs unsafe operator handling
- **Case Sensitivity Bypass**: Mixed case SQL keyword attempts
- **Edge Cases**: Whitespace variations, empty inputs, extremely long expressions

**Key Security Features Tested**:
- Expression compiler's `DANGEROUS_PATTERNS` detection
- Safe operator and function whitelisting
- Field name validation
- Quote escaping and string literal handling
- Subquery validation

### `test_path_traversal.py`

Path traversal security tests covering:

- **File Path Traversal**: Parent directory traversal (`../../../etc/passwd`)
- **Absolute Path Handling**: Attempts to access sensitive system files
- **Symlink Traversal**: Symlinks pointing outside base directory
- **Windows Path Traversal**: Windows-specific patterns (`..\\..\\`)
- **URL Encoded Traversal**: URL-encoded path separators
- **YAML Path Injection**: Entity names, schema names, field names with path traversal
- **Output Path Traversal**: Malicious output directory paths
- **Safe Path Handling**: Verification that safe paths work correctly
- **Edge Cases**: Null bytes, very long paths, special characters, Unicode paths

**Key Security Features Tested**:
- File operation path validation
- YAML parsing security
- Output directory handling
- Path normalization and resolution

### `test_command_injection.py`

Command injection tests covering:

- **Shell Metacharacters**: Semicolons, pipes, ampersands, backticks, `$()`
- **Redirection Injection**: Input/output redirection (`>`, `<`, `>>`)
- **Entity Name Injection**: Shell metacharacters in entity names
- **Schema Name Injection**: Command injection through schema names
- **Field Name Injection**: Malicious field names
- **Action Name Injection**: Shell metacharacters in action names
- **Filename Injection**: Malicious filenames with shell metacharacters
- **Environment Variable Injection**: `$HOME`, `${PATH}`, etc.
- **Template Injection**: Command injection through template rendering
- **Edge Cases**: Escaped characters, quoted strings, Unicode, null bytes

**Key Security Features Tested**:
- Input sanitization
- Shell metacharacter filtering
- Template rendering security
- Filename validation

### `test_expression_fuzzing.py`

Fuzz testing for the expression compiler:

- **Random String Fuzzing**: ASCII, printable, and Unicode strings
- **Operator Fuzzing**: Random operator combinations and stacking
- **Parentheses Fuzzing**: Random, nested, and unbalanced parentheses
- **Function Fuzzing**: Random function calls, nesting, and arguments
- **String Literal Fuzzing**: Special characters, quotes, very long strings
- **Complex Expression Fuzzing**: Mixed functions and operators
- **Subquery Fuzzing**: Random and nested subqueries
- **Whitespace Fuzzing**: Random and excessive whitespace
- **Edge Case Fuzzing**: Empty inputs, maximum length, special numbers
- **Crash Resistance**: 100+ random test cases to detect crashes

**Key Security Features Tested**:
- Parser robustness
- No crashes on malformed input
- Graceful error handling
- Memory safety

### `test_malformed_input.py`

Malformed input and resource exhaustion tests:

- **Large File Security**: Very large YAML files (DoS prevention)
- **Large Field Count**: Entities with thousands of fields
- **Very Long Values**: Extremely long field names and string values
- **Deep Nesting**: Deeply nested parentheses, functions, YAML structures, subqueries
- **Malformed YAML**: Invalid syntax, incomplete documents, duplicate keys
- **Invalid Data Structures**: Invalid field types, unknown steps, circular references
- **Resource Exhaustion**: Memory bombs with fields/actions, exponential expansion
- **Edge Cases**: Empty fields, Unicode, special YAML values, multiline strings
- **Crash Resistance**: Random bytes, truncated UTF-8, mixed line endings

**Key Security Features Tested**:
- DoS prevention
- Recursion limits
- Memory limits
- Parser error handling
- Invalid input rejection

## Running the Tests

### Run all security tests:
```bash
pytest tests/unit/security/ -v
```

### Run specific test files:
```bash
# SQL injection tests
pytest tests/unit/security/test_sql_injection.py -v

# Path traversal tests
pytest tests/unit/security/test_path_traversal.py -v

# Command injection tests
pytest tests/unit/security/test_command_injection.py -v

# Fuzzing tests
pytest tests/unit/security/test_expression_fuzzing.py -v

# Malformed input tests
pytest tests/unit/security/test_malformed_input.py -v
```

### Run with coverage:
```bash
pytest tests/unit/security/ --cov=src --cov-report=html
```

### Run specific test classes:
```bash
# Run only basic SQL injection tests
pytest tests/unit/security/test_sql_injection.py::TestBasicSQLInjection -v

# Run only fuzzing crash resistance tests
pytest tests/unit/security/test_expression_fuzzing.py::TestCrashResistance -v
```

## Test Patterns

### Expected Behavior

1. **Security violations should raise `SecurityError`**:
   ```python
   with pytest.raises(SecurityError, match="dangerous SQL pattern"):
       compiler.compile("status = 'lead'; DROP TABLE users--", entity)
   ```

2. **Invalid input should raise appropriate exceptions**:
   ```python
   with pytest.raises((ValueError, KeyError, AttributeError)):
       compiler.compile(malformed_expression, entity)
   ```

3. **Safe inputs should work correctly**:
   ```python
   result = compiler.compile("status = 'lead' AND score > 50", entity)
   assert "v_status = 'lead'" in result
   ```

### Test Organization

Each test file is organized into classes by attack vector:

- `TestBasicSQLInjection` - Common SQL injection patterns
- `TestAdvancedSQLInjection` - Sophisticated attacks
- `TestEdgeCases` - Boundary conditions and corner cases

## Security Principles Tested

1. **Defense in Depth**: Multiple layers of validation
2. **Fail Secure**: Reject unknown/dangerous inputs by default
3. **Input Validation**: Whitelist approach for operators, functions, fields
4. **Output Encoding**: Proper SQL escaping and quoting
5. **Resource Limits**: Protection against DoS via large inputs or deep recursion
6. **Path Validation**: Prevent directory traversal and unauthorized file access
7. **Command Injection Prevention**: No shell metacharacters in executed commands

## Adding New Security Tests

When adding new security tests:

1. **Identify the attack vector**: What kind of injection or vulnerability?
2. **Create test cases**: Both valid and malicious inputs
3. **Verify safe rejection**: Malicious inputs should be blocked
4. **Verify safe acceptance**: Valid inputs should work correctly
5. **Test edge cases**: Boundary conditions, unusual but valid inputs
6. **Document the threat**: Comment what attack you're testing against

Example:
```python
def test_new_injection_vector(self, compiler, test_entity):
    """Block XYZ injection attempts via ABC vector

    This tests protection against attackers using ABC to inject XYZ,
    which could lead to [security impact].
    """
    malicious_inputs = [
        "example malicious input 1",
        "example malicious input 2",
    ]

    for malicious_input in malicious_inputs:
        with pytest.raises(SecurityError):
            compiler.compile(malicious_input, test_entity)
```

## Security Test Metrics

Target coverage:

- **SQL Injection**: 95%+ coverage of expression compiler paths
- **Path Traversal**: 90%+ coverage of file operations
- **Command Injection**: 85%+ coverage of CLI operations
- **Fuzzing**: 1000+ random test cases without crashes
- **Malformed Input**: Handle 100+ edge cases gracefully

## Integration with CI/CD

These tests should be:

1. **Run on every commit**: Part of the standard test suite
2. **Required for PR approval**: All security tests must pass
3. **Monitored for new failures**: Any new security test failures are critical
4. **Regularly updated**: Add tests for newly discovered attack vectors

## References

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **CWE Top 25**: https://cwe.mitre.org/top25/
- **SQL Injection**: https://owasp.org/www-community/attacks/SQL_Injection
- **Path Traversal**: https://owasp.org/www-community/attacks/Path_Traversal
- **Command Injection**: https://owasp.org/www-community/attacks/Command_Injection

## Maintenance

- **Review quarterly**: Ensure tests cover latest attack techniques
- **Update after incidents**: Add tests for any discovered vulnerabilities
- **Benchmark performance**: Ensure security tests don't slow down CI significantly
- **Document exceptions**: Any intentional security test skips must be documented

---

**Last Updated**: 2025-11-15
**Test Count**: 100+ security test cases
**Coverage**: SQL Injection, Path Traversal, Command Injection, Fuzzing, Malformed Input
