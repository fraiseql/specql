# SpecQL Development Workflows

## Development Workflow

![Development Workflow](diagrams/development_workflow.png)

<details>
<summary>View Mermaid source</summary>

```mermaid
graph TB
    Start[Start New Feature]

    Start --> Define[Define Entity in YAML]
    Define --> Validate[specql validate]

    Validate --> Error{Valid?}
    Error -->|No| Fix[Fix YAML]
    Fix --> Validate
    Error -->|Yes| Generate[specql generate]

    Generate --> Review[Review Generated Code]
    Review --> Test[Test Locally]
    Test --> Commit[Commit Changes]
    Commit --> Deploy[Deploy to Production]

    style Define fill:#e1f5ff
    style Generate fill:#fff4e1
    style Deploy fill:#e8f5e9
```

</details>

### Workflow Steps

1. **Define Entity**: Write your data model in YAML format
2. **Validate**: Use `specql validate` to check syntax and semantics
3. **Fix Issues**: Address any validation errors
4. **Generate Code**: Run `specql generate` to create multi-language code
5. **Review**: Examine generated code for correctness
6. **Test**: Test locally with your application
7. **Commit**: Commit both YAML and generated code
8. **Deploy**: Deploy to production

## Migration Workflow

![Migration Workflow](diagrams/migration_workflow.png)

<details>
<summary>View Mermaid source</summary>

```mermaid
graph LR
    subgraph "Current State"
        Legacy[Legacy Database/Code]
    end

    subgraph "Reverse Engineering"
        RE[specql reverse]
        YAML[SpecQL YAML]
    end

    subgraph "Enhancement"
        Edit[Edit YAML]
        Add[Add Business Logic]
    end

    subgraph "Generation"
        Gen[specql generate]
        New[New Multi-Language Code]
    end

    subgraph "Migration"
        Test[Test & Validate]
        Deploy[Deploy New System]
    end

    Legacy --> RE
    RE --> YAML
    YAML --> Edit
    Edit --> Add
    Add --> Gen
    Gen --> New
    New --> Test
    Test --> Deploy

    style Legacy fill:#ffebee
    style YAML fill:#fff4e1
    style New fill:#e8f5e9
```

</details>

### Migration Steps

1. **Reverse Engineer**: Convert existing database/code to SpecQL YAML
2. **Edit YAML**: Clean up and enhance the generated YAML
3. **Add Business Logic**: Include actions, validations, and complex logic
4. **Generate New Code**: Create modern multi-language implementation
5. **Test**: Thoroughly test the new system
6. **Deploy**: Migrate to the new SpecQL-generated system

## Reverse Engineering Options

### From Database
```bash
# PostgreSQL (currently supported)
specql reverse --connection "postgresql://user:pass@localhost/db" --schema crm --output entities/

# MySQL, SQL Server, etc. (planned for future versions)
# specql reverse mysql --connection "mysql://user:pass@localhost/db" --output entities/
```

### From Code
```bash
# Python, Java, TypeScript reverse engineering (planned for v0.6.0)
# specql reverse python models/ --output entities/
# specql reverse java src/main/java/ --output entities/
# specql reverse typescript src/ --output entities/
```

**Current Status**: Database reverse engineering from PostgreSQL is available. Code reverse engineering from Python/Java/TypeScript is planned for v0.6.0.

## Best Practices

### Development
- **Validate Early**: Always run `specql validate` before generating
- **Version Control**: Commit both YAML specifications and generated code
- **Code Reviews**: Review generated code changes like any other code
- **Testing**: Test generated code thoroughly before deployment

### Migration
- **Incremental Migration**: Migrate one entity at a time
- **Data Validation**: Ensure data integrity during migration
- **Rollback Plan**: Have a rollback strategy for failed migrations
- **Performance Testing**: Test performance of new system under load

### Team Collaboration
- **YAML Standards**: Establish team conventions for YAML structure
- **Code Generation**: Set up CI/CD to automatically regenerate code
- **Documentation**: Keep entity documentation up to date
- **Training**: Train team members on SpecQL workflows