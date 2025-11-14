# Week 10 Expansion: Complete Spring Boot Pattern Recognition

**Date**: 2025-11-14
**Duration**: 3-4 days
**Status**: 📋 Planned
**Objective**: Fix and complete Spring Boot pattern recognition implementation

**Prerequisites**: Week 10 partial implementation (commit 72b5495)

**Output**: Working Spring Boot parser with all tests passing

---

## 🎯 Executive Summary

Week 10 has foundational infrastructure in place but method extraction is failing. This expansion plan addresses the specific issues preventing test success and completes the implementation.

**Current State**:
- ✅ Component detection working (@RestController, @Service, @Configuration)
- ✅ Mock infrastructure created (MockMethodDeclaration, MockParameter)
- ❌ Method extraction failing (regex pattern issue)
- ❌ 0/5 tests passing
- ❌ Repository interface detection missing

**Target State**:
- ✅ All 5 Spring Boot integration tests passing
- ✅ Method extraction working for controllers, services, configurations
- ✅ Repository interface detection implemented
- ✅ 20+ unit tests for Spring Boot parsing

---

## 📅 Daily Breakdown

### Day 1: Fix Method Extraction (6 hours)

**Morning: Debug and Fix Regex Pattern (3 hours)**

**Problem**: Current regex `r'((?:@\w+(?:\([^)]*\))?\s+)*(?:public|private|protected)\s+(?:\w+(?:<[^>]+>)?)\s+\w+\s*\([^)]*\)\s*(?:throws\s+[\w\s,]+)?\s*\{[^}]*\})'` fails on nested braces.

**Root Cause**: `\{[^}]*\}` only matches single-level braces, but method bodies have nested braces.

**Solution Approach**:
1. **Use brace counting** instead of regex for method body extraction
2. Extract method signature separately from body
3. Parse signature components individually

**Implementation Steps**:

1. **Update `_extract_body_declarations` in jdt_bridge.py** (1 hour)
   ```python
   def _extract_methods_with_brace_counting(self, class_body):
       """Extract methods by counting braces"""
       methods = []
       i = 0
       while i < len(class_body):
           # Find method signature
           sig_match = re.search(
               r'((?:@\w+(?:\([^)]*\))?\s+)*)(public|private|protected)\s+'
               r'(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)',
               class_body[i:]
           )
           if not sig_match:
               break

           # Find opening brace
           sig_end = i + sig_match.end()
           brace_start = class_body.find('{', sig_end)
           if brace_start == -1:
               i = sig_end
               continue

           # Count braces to find method end
           brace_count = 1
           j = brace_start + 1
           while j < len(class_body) and brace_count > 0:
               if class_body[j] == '{':
                   brace_count += 1
               elif class_body[j] == '}':
                   brace_count -= 1
               j += 1

           method_text = class_body[i + sig_match.start():j]
           methods.append(MockMethodDeclaration(method_text, class_body))
           i = j

       return methods
   ```

2. **Test method extraction** (1 hour)
   - Write unit test for brace counting logic
   - Test with nested braces, anonymous classes
   - Verify all 5 controller methods extracted

3. **Update MockMethodDeclaration parsing** (1 hour)
   - Improve annotation extraction
   - Handle @GetMapping("/{id}") path parameters
   - Extract @PathVariable, @RequestBody annotations

**Afternoon: Enhance Method Parsing (3 hours)**

4. **Add comprehensive annotation support** (1.5 hours)
   - @Transactional
   - @Cacheable
   - @Async
   - @Bean (for @Configuration classes)
   - @Scheduled

5. **Fix parameter parsing** (1.5 hours)
   - Handle generics: `List<User>`, `Map<String, Object>`
   - Parse parameter annotations: `@PathVariable Long id`
   - Support varargs: `String... args`

**Success Criteria**:
- [ ] Extract all 5 methods from UserController test
- [ ] Handle nested braces correctly
- [ ] Parse all Spring annotations
- [ ] test_parse_spring_boot_controller PASSING

---

### Day 2: Repository & Service Support (6 hours)

**Morning: Repository Interface Detection (3 hours)**

**Current Issue**: Repository interfaces not detected (test expects 'repository' component type)

1. **Implement `_is_repository_interface` in spring_visitor.py** (2 hours)
   ```python
   def _is_repository_interface(self, type_decl) -> bool:
       """Check if type is a Spring Data repository"""
       # Check if it's an interface
       if not self._is_interface(type_decl):
           return False

       # Check if extends JpaRepository, CrudRepository, etc.
       if hasattr(type_decl, 'superInterfaceTypes'):
           for super_type in type_decl.superInterfaceTypes():
               type_name = super_type.toString()
               if any(repo in type_name for repo in [
                   'JpaRepository', 'CrudRepository',
                   'PagingAndSortingRepository', 'Repository'
               ]):
                   return True

       # For mock: parse source for "extends"
       if hasattr(type_decl, 'source_code'):
           return bool(re.search(
               r'extends\s+(Jpa|Crud|PagingAndSorting)?Repository',
               type_decl.source_code
           ))

       return False

   def _is_interface(self, type_decl) -> bool:
       """Check if type declaration is an interface"""
       # Real JDT: type_decl.isInterface()
       if hasattr(type_decl, 'isInterface'):
           return type_decl.isInterface()

       # Mock: check source code
       if hasattr(type_decl, 'source_code'):
           return bool(re.search(
               r'\binterface\s+' + type_decl.class_name,
               type_decl.source_code
           ))

       return False
   ```

2. **Add MockTypeDeclaration.isInterface()** (0.5 hour)
   ```python
   def isInterface(self):
       """Check if this is an interface"""
       return bool(re.search(
           r'\binterface\s+' + self.class_name,
           self.source_code
       ))
   ```

3. **Test repository detection** (0.5 hour)
   - Verify ProductRepository detected
   - Check component_type == 'repository'

**Afternoon: Service & Configuration (3 hours)**

4. **Fix service method extraction** (1.5 hours)
   - Ensure all public methods extracted from @Service
   - Handle @Transactional methods
   - Test with ProductService example

5. **Fix configuration @Bean methods** (1.5 hours)
   - Extract @Bean annotated methods
   - Parse bean method return types
   - Test with SecurityConfig example

**Success Criteria**:
- [ ] test_parse_spring_boot_repository PASSING
- [ ] test_parse_spring_boot_service PASSING
- [ ] test_parse_spring_boot_configuration PASSING
- [ ] 3/5 tests passing

---

### Day 3: Multi-Component & Integration (6 hours)

**Morning: Multi-Component Parsing (3 hours)**

1. **Fix directory parsing** (2 hours)
   ```python
   def parse_directory(self, directory: str, config: SpringParseConfig = None):
       """Parse all Java files in directory"""
       if config is None:
           config = SpringParseConfig()

       results = []
       java_files = []

       # Find all Java files
       for root, dirs, files in os.walk(directory):
           if not config.recursive:
               dirs.clear()  # Don't recurse

           for file in files:
               if file.endswith('.java'):
                   file_path = os.path.join(root, file)
                   # Check exclude patterns
                   if not self._should_exclude(file_path, config):
                       java_files.append(file_path)

       # Parse each file
       for file_path in java_files:
           result = self.parse_file(file_path)
           results.append(result)

       return results
   ```

2. **Test multi-component parsing** (1 hour)
   - Create temp directory with 3 files
   - Verify all 3 components detected
   - Check component types correct

**Afternoon: Unit Tests & Edge Cases (3 hours)**

3. **Write comprehensive unit tests** (2 hours)
   - Test method extraction edge cases
   - Test repository patterns
   - Test configuration beans
   - Test error handling

4. **Add Spring Data query method detection** (1 hour)
   ```python
   def _extract_repository_query_methods(self, type_decl):
       """Extract Spring Data query methods from repository interface"""
       methods = []

       # For interfaces, look for method signatures (no body)
       method_pattern = r'(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)\s*;'

       for match in re.finditer(method_pattern, class_body):
           return_type, method_name, params = match.groups()

           # Check if it matches Spring Data patterns
           if self._is_repository_method(method_name):
               methods.append(SpringMethod(
                   name=method_name,
                   return_type=return_type,
                   parameters=self._parse_params(params),
                   annotations=['SpringDataQuery']
               ))

       return methods
   ```

**Success Criteria**:
- [ ] test_parse_directory_with_multiple_components PASSING
- [ ] 5/5 integration tests passing
- [ ] 20+ unit tests passing

---

### Day 4: Polish & Documentation (4 hours)

**Morning: Code Quality (2 hours)**

1. **Refactor and clean up** (1 hour)
   - Remove dead code
   - Add docstrings
   - Improve error messages

2. **Performance optimization** (1 hour)
   - Cache compiled regexes
   - Optimize brace counting
   - Profile parser performance

**Afternoon: Documentation (2 hours)**

3. **Write examples** (1 hour)
   - Add Spring Boot examples directory
   - Document controller patterns
   - Document service patterns
   - Document repository patterns

4. **Update README** (1 hour)
   - Document `specql reverse spring` command
   - Add usage examples
   - Add troubleshooting guide

**Success Criteria**:
- [ ] All code documented
- [ ] Examples working
- [ ] Performance acceptable (<1s per file)

---

## 🧪 Testing Strategy

### Unit Tests (20+ tests)

**jdt_bridge.py**:
- `test_mock_method_declaration_simple`
- `test_mock_method_declaration_with_annotations`
- `test_mock_method_declaration_with_generics`
- `test_mock_method_declaration_nested_braces`
- `test_brace_counting_logic`
- `test_extract_methods_from_class_body`

**spring_visitor.py**:
- `test_is_spring_component_controller`
- `test_is_spring_component_service`
- `test_is_spring_component_repository`
- `test_is_repository_interface`
- `test_extract_method_with_http_mapping`
- `test_extract_method_with_path_variable`
- `test_extract_method_with_request_body`
- `test_extract_repository_query_method`

**spring_parser.py**:
- `test_parse_file_controller`
- `test_parse_file_service`
- `test_parse_file_repository`
- `test_parse_directory`
- `test_parse_directory_with_exclusions`

### Integration Tests (5 tests - EXISTING)

All in `test_spring_boot_parser.py`:
- `test_parse_spring_boot_controller` - Currently FAILING
- `test_parse_spring_boot_service` - Currently FAILING
- `test_parse_spring_boot_repository` - Currently FAILING
- `test_parse_spring_boot_configuration` - Currently FAILING
- `test_parse_directory_with_multiple_components` - Currently FAILING

**Target**: 5/5 PASSING

---

## 🔧 Implementation Files

### Modified Files

1. **src/reverse_engineering/java/jdt_bridge.py** (~200 lines added)
   - Fix `_extract_body_declarations()` - brace counting
   - Fix `MockMethodDeclaration._parse_method()` - better annotation parsing
   - Add `MockTypeDeclaration.isInterface()`
   - Add `MockTypeDeclaration.superInterfaceTypes()`

2. **src/reverse_engineering/java/spring_visitor.py** (~150 lines added)
   - Fix `_is_repository_interface()` - complete implementation
   - Add `_is_interface()` helper
   - Add `_extract_repository_query_methods()`
   - Improve `_extract_method()` annotation detection

3. **src/reverse_engineering/java/spring_parser.py** (~50 lines added)
   - Fix `parse_directory()` - proper file discovery
   - Add `_should_exclude()` helper
   - Improve error handling

### New Files

4. **tests/unit/reverse_engineering/java/test_mock_method_parsing.py** (NEW - 200 lines)
   - Unit tests for MockMethodDeclaration
   - Unit tests for brace counting
   - Edge case tests

5. **tests/unit/reverse_engineering/java/test_spring_visitor.py** (NEW - 250 lines)
   - Unit tests for component detection
   - Unit tests for method extraction
   - Unit tests for repository detection

6. **examples/java/spring-boot-services/** (NEW - directory)
   - `UserController.java` - REST controller example
   - `UserService.java` - Service example
   - `UserRepository.java` - Repository interface example
   - `SecurityConfig.java` - Configuration example

---

## ✅ Success Criteria

**Must Have (Week 10 Complete)**:
- [ ] All 5 integration tests passing (0/5 → 5/5)
- [ ] 20+ unit tests passing
- [ ] Method extraction working with nested braces
- [ ] Repository interface detection working
- [ ] Controller, Service, Configuration all supported

**Nice to Have**:
- [ ] Spring Data query method parsing
- [ ] Performance <1s per file
- [ ] Comprehensive examples

**Metrics**:
- Test Coverage: >90% for new Spring Boot code
- Performance: <1 second to parse typical Spring Boot file
- Error Handling: Graceful degradation on parse errors

---

## 🐛 Known Issues & Fixes

### Issue 1: Nested Braces in Method Bodies
**Problem**: Regex `\{[^}]*\}` fails on nested braces
**Fix**: Implement brace counting algorithm (Day 1)
**Priority**: HIGH

### Issue 2: Repository Interfaces Not Detected
**Problem**: `_is_repository_interface()` stub doesn't check extends clause
**Fix**: Parse interface supertype (Day 2)
**Priority**: HIGH

### Issue 3: Configuration @Bean Methods Not Extracted
**Problem**: Methods without HTTP mappings filtered out
**Fix**: Include all methods for configuration component type (Day 2)
**Priority**: MEDIUM

### Issue 4: Directory Parsing Missing Files
**Problem**: `parse_directory()` not implemented
**Fix**: Walk directory tree and filter Java files (Day 3)
**Priority**: MEDIUM

---

## 📊 Progress Tracking

### Day-by-Day Targets

**Day 1 End**:
- Brace counting implemented
- Method extraction working
- 1/5 tests passing (controller)

**Day 2 End**:
- Repository detection working
- Service and configuration working
- 4/5 tests passing

**Day 3 End**:
- Directory parsing working
- All integration tests passing (5/5)
- 15+ unit tests passing

**Day 4 End**:
- All unit tests passing (20+)
- Documentation complete
- Examples working

---

## 🔗 Related Files

- **Current Implementation**: commit 72b5495
- **Previous**: [Week 09](./WEEK_09.md) - Java AST Parser & JPA Extraction
- **Next**: [Week 11](./WEEK_11.md) - Java Code Generation
- **Roadmap**: [REPRIORITIZED_ROADMAP_2025-11-13.md](./REPRIORITIZED_ROADMAP_2025-11-13.md)

---

## 📝 Notes

**Why This Failed Initially**:
- Regex for method bodies too simple (didn't handle nesting)
- Repository detection not implemented
- Component type filtering too strict
- Missing comprehensive tests

**Key Learnings**:
- Don't use regex for brace-matching - use counting
- Test with real Spring Boot code early
- Mock implementation needs same features as real JDT
- Unit tests catch edge cases integration tests miss

**Estimated Effort**:
- Day 1 (Method Extraction): 6 hours
- Day 2 (Repository/Service): 6 hours
- Day 3 (Integration): 6 hours
- Day 4 (Polish): 4 hours
- **Total**: 22 hours (~3-4 working days)

---

**Status**: 📋 Ready to Execute
**Risk Level**: Low (infrastructure exists, just need bug fixes)
**Confidence**: High (specific fixes identified)
