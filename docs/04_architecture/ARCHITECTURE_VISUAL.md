# SpecQL Architecture

## High-Level Overview

![SpecQL High-Level Architecture](diagrams/high_level_overview.png)

<details>
<summary>View Mermaid source</summary>

```mermaid
graph TB
    subgraph "Input"
        YAML[YAML Specification]
    end

    subgraph "Core Processing"
        Parser[SpecQL Parser]
        Validator[Semantic Validator]
        AST[Universal AST]
    end

    subgraph "Code Generators"
        PG[PostgreSQL Generator]
        Java[Java Generator]
        Rust[Rust Generator]
        TS[TypeScript Generator]
    end

    subgraph "Output"
        SQL[SQL Schema + Functions]
        SpringBoot[Spring Boot Code]
        Diesel[Diesel Code]
        Prisma[Prisma Schema]
    end

    subgraph "Integrations"
        FraiseQL[FraiseQL GraphQL]
        Tests[Test Generation]
        CICD[CI/CD Workflows]
        IaC[Infrastructure Code]
    end

    YAML --> Parser
    Parser --> Validator
    Validator --> AST

    AST --> PG
    AST --> Java
    AST --> Rust
    AST --> TS

    PG --> SQL
    Java --> SpringBoot
    Rust --> Diesel
    TS --> Prisma

    SQL --> FraiseQL
    AST --> Tests
    AST --> CICD
    AST --> IaC

    style YAML fill:#e1f5ff
    style AST fill:#fff4e1
    style SQL fill:#e8f5e9
    style SpringBoot fill:#e8f5e9
    style Diesel fill:#e8f5e9
    style Prisma fill:#e8f5e9
```

</details>

## Code Generation Flow

![Code Generation Flow](diagrams/code_generation_flow.png)

<details>
<summary>View Mermaid source</summary>

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Parser
    participant Validator
    participant AST
    participant Generator
    participant FileSystem

    User->>CLI: specql generate entity.yaml
    CLI->>Parser: parse(entity.yaml)
    Parser->>Validator: validate AST

    alt Validation Error
        Validator-->>User: ❌ Detailed error message
    else Valid
        Validator->>AST: build universal AST
        AST->>Generator: generate(target_language)
        Generator->>FileSystem: write generated files
        FileSystem-->>User: ✅ Generated code
    end
```

</details>

## Reverse Engineering Flow

![Reverse Engineering Flow](diagrams/reverse_engineering_flow.png)

<details>
<summary>View Mermaid source</summary>

```mermaid
graph LR
    subgraph "Existing Code"
        PG_Schema[PostgreSQL Schema]
        Python_Code[Python Models]
        Java_Code[Java Entities]
        Rust_Code[Rust Structs]
        TS_Code[TypeScript Types]
    end

    subgraph "Language Parsers"
        PG_Parser[PostgreSQL Parser]
        Py_Parser[Python AST Parser]
        Java_Parser[Java Parser]
        Rust_Parser[Rust Parser]
        TS_Parser[TypeScript Parser]
    end

    subgraph "Output"
        YAML_Out[SpecQL YAML]
    end

    PG_Schema --> PG_Parser
    Python_Code --> Py_Parser
    Java_Code --> Java_Parser
    Rust_Code --> Rust_Parser
    TS_Code --> TS_Parser

    PG_Parser --> YAML_Out
    Py_Parser --> YAML_Out
    Java_Parser --> YAML_Out
    Rust_Parser --> YAML_Out
    TS_Parser --> YAML_Out

    style YAML_Out fill:#fff4e1
```

</details>

## Trinity Pattern Explained

![Trinity Pattern](diagrams/trinity_pattern.png)

<details>
<summary>View Mermaid source</summary>

```mermaid
erDiagram
    CONTACT {
        integer pk_contact PK "Auto-increment primary key"
        uuid id UK "UUID for external references"
        text identifier "Business identifier (email/slug)"
        text first_name
        text last_name
        text email
        timestamp created_at
        timestamp updated_at
    }

    COMPANY {
        integer pk_company PK
        uuid id UK
        text identifier "Company name"
        text industry
    }

    CONTACT }o--|| COMPANY : "belongs to"
```

</details>

**Trinity Pattern Benefits**:
- `pk_*`: Fast joins (integer)
- `id`: External API stability (UUID)
- `identifier`: Human-readable (business key)

## FraiseQL Integration

![FraiseQL Integration](diagrams/fraiseql_integration.png)

<details>
<summary>View Mermaid source</summary>

```mermaid
graph TB
    subgraph "SpecQL"
        YAML[SpecQL YAML]
        Generator[PostgreSQL Generator]
    end

    subgraph "Database"
        Schema[PostgreSQL Schema]
        Comments[FraiseQL Annotations]
    end

    subgraph "FraiseQL"
        Scanner[Schema Scanner]
        GraphQL[GraphQL Server]
    end

    subgraph "Clients"
        Web[Web App]
        Mobile[Mobile App]
        API[Third-party APIs]
    end

    YAML --> Generator
    Generator --> Schema
    Generator --> Comments

    Schema --> Scanner
    Comments --> Scanner
    Scanner --> GraphQL

    GraphQL --> Web
    GraphQL --> Mobile
    GraphQL --> API

    style YAML fill:#e1f5ff
    style GraphQL fill:#f3e5f5
```

</details>