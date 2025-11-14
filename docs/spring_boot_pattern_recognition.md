# Spring Boot Pattern Recognition

This document describes the Spring Boot pattern recognition capabilities added in Week 10 of the SpecQL implementation plan.

## Overview

The Spring Boot pattern recognition system can automatically analyze Spring Boot applications and convert them to SpecQL actions. It recognizes:

- **Controllers** (`@RestController`, `@Controller`) with HTTP endpoints
- **Services** (`@Service`) with business logic methods
- **Repositories** (Spring Data interfaces) with data access methods
- **Configuration** classes (`@Configuration`) with `@Bean` methods

## Supported Annotations

### Controller Annotations
- `@RestController` - REST API controllers
- `@Controller` - Web MVC controllers
- `@RequestMapping` - Base path mapping
- `@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping`, `@PatchMapping` - HTTP method mappings
- `@PathVariable` - URL path parameters
- `@RequestBody` - Request body parameters

### Service Annotations
- `@Service` - Service components
- `@Transactional` - Transaction boundaries
- `@Async` - Asynchronous methods
- `@Cacheable` - Caching annotations

### Repository Patterns
- Interfaces extending `JpaRepository`, `CrudRepository`, etc.
- Method patterns: `findBy*`, `save`, `deleteBy*`, `existsBy*`, `countBy*`

### Configuration Annotations
- `@Configuration` - Configuration classes
- `@Bean` - Bean definition methods

## Usage

### Command Line

```bash
# Parse a single Spring Boot file
specql reverse spring /path/to/Controller.java

# Parse a directory of Spring Boot files
specql reverse spring /path/to/spring/project

# Parse with custom configuration
specql reverse spring /path/to/project --config spring_config.yaml
```

### Programmatic API

```python
from src.reverse_engineering.java.spring_parser import SpringParser, SpringParseConfig

# Create parser
parser = SpringParser()

# Parse single file
result = parser.parse_file("UserController.java")
print(f"Found {len(result.components)} components")
print(f"Generated {len(result.actions)} actions")

# Parse directory
config = SpringParseConfig(
    include_patterns=["*.java"],
    exclude_patterns=["**/test/**", "**/*Test.java"]
)
results = parser.parse_directory("/path/to/spring/project", config)

# Get all actions
all_actions = {}
for result in results:
    if result.actions:
        all_actions[result.file_path] = result.actions
```

## Generated Actions

### Controller Actions

Spring MVC controllers are converted to SpecQL actions that map HTTP endpoints to database operations:

```java
@RestController
@RequestMapping("/api/users")
public class UserController {
    @GetMapping
    public List<User> getAllUsers() { ... }

    @PostMapping
    public User createUser(@RequestBody User user) { ... }

    @GetMapping("/{id}")
    public User getUserById(@PathVariable Long id) { ... }
}
```

Generates actions:
- `get_api_users` - SELECT from users table
- `post_api_users` - INSERT into users table
- `get_api_users_{id}` - SELECT with WHERE id = ?

### Service Actions

Service methods become internal actions:

```java
@Service
public class UserService {
    @Transactional
    public User createUser(User user) {
        return userRepository.save(user);
    }
}
```

Generates action:
- `userservice_createuser` - Calls createUser function

### Repository Actions

Repository methods are mapped to database operations:

```java
public interface UserRepository extends JpaRepository<User, Long> {
    List<User> findByEmail(String email);
    User save(User user);
    void deleteById(Long id);
}
```

Generates actions:
- `userrepository_findbyemail` - SELECT with WHERE email = ?
- `userrepository_save` - INSERT/UPDATE user
- `userrepository_deletebyid` - DELETE with WHERE id = ?

## Configuration

Create a `spring_config.yaml` file to customize parsing:

```yaml
include_patterns:
  - "*.java"
exclude_patterns:
  - "**/test/**"
  - "**/*Test.java"
  - "**/generated/**"
min_confidence: 0.8
recursive: true
```

## Examples

### Complete Spring Boot Application

See `tests/integration/java/test_spring_boot_parser.py` for complete examples of parsing real Spring Boot code.

### Generated SpecQL Actions

The parser generates SpecQL action definitions that can be used to create database functions and API endpoints.

## Performance

- **Small projects** (3-5 files): < 1 second
- **Medium projects** (10-15 files): < 3 seconds
- **Large projects**: Scales linearly with number of files

## Limitations

- Requires Java AST parsing (uses Eclipse JDT)
- Only supports Spring Boot stereotype annotations
- Complex custom queries may need manual refinement
- Does not parse application.properties/application.yml files (yet)

## Future Enhancements

- Support for more Spring annotations (`@Scheduled`, `@EventListener`, etc.)
- Configuration file parsing (application.properties, application.yml)
- Spring Security integration
- Custom repository method parsing
- Integration with Spring Cloud components