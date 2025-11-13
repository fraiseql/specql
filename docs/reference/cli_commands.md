# CLI Commands Reference

This document provides a comprehensive reference for all SpecQL command-line interface commands, organized by category with examples and options.

## Command Categories

### Core Commands

#### `generate`
Generate production-ready code from SpecQL YAML entities.

```bash
# Generate all entities with default settings
specql generate entities/**/*.yaml

# Generate for specific framework
specql generate entities/**/*.yaml --framework django

# Development mode with flat structure
specql generate entities/**/*.yaml --dev

# Custom output directory
specql generate entities/**/*.yaml --output ./generated/

# Generate specific entities
specql generate entities/user.yaml entities/product.yaml

# Dry run to see what would be generated
specql generate entities/**/*.yaml --dry-run
```

**Options**:
- `--framework [fraiseql|django|rails|prisma]`: Target framework (default: fraiseql)
- `--format [hierarchical|flat]`: Output format (default: hierarchical)
- `--output DIRECTORY`: Output directory (default: migrations/)
- `--dev`: Development mode with flat structure
- `--no-tv`: Skip table view generation
- `--foundation-only`: Generate only app foundation
- `--verbose, -v`: Show detailed progress
- `--dry-run`: Preview without writing files

**Generated Artifacts**:
- PostgreSQL tables and functions
- Django models and admin
- SQLAlchemy models
- Migration scripts
- Test files

#### `reverse`
Convert existing SQL to SpecQL YAML (reverse engineering).

```bash
# Reverse engineer SQL files
specql reverse reference_sql/**/*.sql --output entities/

# Reverse engineer with AI enhancement
specql reverse complex_function.sql --ai-enhance --model llama3.1

# Batch process directory
specql reverse legacy_code/ --batch --confidence-threshold 0.8

# Show analysis without generating files
specql reverse function.sql --analyze-only
```

**Options**:
- `--output DIRECTORY`: Output directory for YAML files
- `--ai-enhance`: Use AI for better conversion accuracy
- `--model MODEL`: AI model to use (default: llama3.1)
- `--batch`: Process multiple files
- `--confidence-threshold FLOAT`: Minimum confidence for conversion
- `--analyze-only`: Show analysis without generating files

### Template Commands

#### `instantiate`
Create entity from pre-built templates.

```bash
# Instantiate a CRM contact template
specql instantiate crm.contact --output contact.yaml

# Instantiate with customizations
specql instantiate ecommerce.product \
  --customizations '{"enable_variants": true, "enable_inventory_tracking": true}' \
  --output product.yaml

# List available templates
specql templates list

# Show template details
specql templates show crm.contact

# List templates by category
specql templates list --category crm
```

**Options**:
- `--output FILE`: Output YAML file
- `--customizations JSON`: Template customizations
- `--category CATEGORY`: Filter templates by category

#### `patterns`
Manage and query domain patterns.

```bash
# List all available patterns
specql patterns list

# Show pattern details
specql patterns show state_machine

# List patterns by category
specql patterns list --category workflow

# Search patterns
specql patterns search "audit"
```

### Registry Commands

#### `registry list-domains`
List all registered domains.

```bash
specql registry list-domains
```

#### `registry list-subdomains`
List subdomains for a domain.

```bash
specql registry list-subdomains --domain crm
```

#### `registry show-entity`
Show entity details from registry.

```bash
specql registry show-entity crm.contact
```

#### `registry add-domain`
Add a new domain to registry.

```bash
specql registry add-domain --name crm --description "Customer Relationship Management"
```

#### `registry add-subdomain`
Add a subdomain to a domain.

```bash
specql registry add-subdomain --domain crm --name contact --description "Contact management"
```

#### `registry validate`
Validate registry consistency.

```bash
specql registry validate
```

### Validation Commands

#### `validate`
Validate SpecQL YAML syntax and semantics.

```bash
# Validate single file
specql validate entity.yaml

# Validate multiple files
specql validate entities/**/*.yaml

# Strict validation with all checks
specql validate entity.yaml --strict

# Show detailed validation report
specql validate entity.yaml --verbose
```

**Options**:
- `--strict`: Enable strict validation mode
- `--verbose, -v`: Show detailed validation messages
- `--format [text|json]`: Output format

### CDC Commands

#### `cdc enable`
Enable Change Data Capture for entities.

```bash
# Enable CDC for specific entities
specql cdc enable entities/user.yaml entities/product.yaml

# Enable CDC for all entities
specql cdc enable entities/**/*.yaml

# Enable with custom retention
specql cdc enable entity.yaml --retention-days 30
```

#### `cdc disable`
Disable Change Data Capture.

```bash
specql cdc disable entity.yaml
```

### CI/CD Commands

#### `cicd convert-cicd`
Convert universal pipeline YAML to platform-specific CI/CD configurations.

```bash
# Convert to GitHub Actions
specql cicd convert-cicd pipeline.yaml github-actions --output .github/workflows/ci.yml

# Convert to GitLab CI
specql cicd convert-cicd pipeline.yaml gitlab-ci --output .gitlab-ci.yml

# Convert to CircleCI
specql cicd convert-cicd pipeline.yaml circleci --output .circleci/config.yml

# Convert to Jenkins Pipeline
specql cicd convert-cicd pipeline.yaml jenkins --output Jenkinsfile

# Convert to Azure DevOps
specql cicd convert-cicd pipeline.yaml azure --output azure-pipelines.yml

# Convert to all supported platforms
specql cicd convert-cicd pipeline.yaml all --output ./cicd-configs/
```

**Options**:
- `--output FILE/DIRECTORY`: Output file or directory (default: stdout for single platform, ./cicd-configs/ for all)
- `--validate`: Validate generated configuration syntax
- `--optimize`: Apply performance optimizations during generation

**Supported Platforms**:
- `github-actions`: GitHub Actions workflows
- `gitlab-ci`: GitLab CI/CD pipelines
- `circleci`: CircleCI configuration
- `jenkins`: Jenkins Pipeline (Jenkinsfile)
- `azure`: Azure DevOps YAML pipelines
- `all`: Generate for all supported platforms

#### `cicd reverse-cicd`
Reverse engineer existing CI/CD configurations to universal pipeline format.

```bash
# Reverse engineer GitHub Actions workflow
specql cicd reverse-cicd .github/workflows/ci.yml --output pipeline.yaml

# Reverse engineer GitLab CI pipeline
specql cicd reverse-cicd .gitlab-ci.yml --platform gitlab-ci --output pipeline.yaml

# Reverse engineer CircleCI config
specql cicd reverse-cicd .circleci/config.yml --platform circleci --output pipeline.yaml

# Batch process multiple files
specql cicd reverse-cicd workflows/*.yml --output universal/

# Auto-detect platform from file content
specql cicd reverse-cicd unknown-config.yml
```

**Options**:
- `--platform PLATFORM`: Explicitly specify source platform (auto-detected if not provided)
- `--output FILE/DIRECTORY`: Output file or directory
- `--validate`: Validate input configuration before parsing
- `--extract-patterns`: Extract reusable patterns during reverse engineering

**Auto-Detection**:
The command automatically detects the platform based on:
- File naming conventions (.github/workflows/, .gitlab-ci.yml, etc.)
- YAML structure and syntax patterns
- Platform-specific keywords and constructs

#### `cicd generate-cicd`
Generate CI/CD pipeline from SpecQL entities or project analysis.

```bash
# Generate pipeline from SpecQL entities
specql cicd generate-cicd entities/*.yaml --output pipeline.yaml

# Auto-generate pipeline from project structure
specql cicd generate-cicd --auto --language python --framework fastapi

# Generate from pattern with customizations
specql cicd generate-cicd --from-pattern python_fastapi_backend --customize '{"database": "postgres"}'
```

**Options**:
- `--auto`: Auto-detect project structure and generate appropriate pipeline
- `--language LANGUAGE`: Programming language (python, node, go, rust, java)
- `--framework FRAMEWORK`: Framework name (fastapi, django, express, react)
- `--from-pattern PATTERN`: Generate from existing pattern
- `--customize JSON`: Pattern customizations as JSON string
- `--output FILE`: Output universal pipeline YAML file

#### `cicd search-pipeline`
Search CI/CD pipeline patterns using semantic search.

```bash
# Search for patterns by description
specql cicd search-pipeline "fastapi backend with postgres"

# Search by category
specql cicd search-pipeline --category backend

# Search by tags
specql cicd search-pipeline --tags python,fastapi,docker

# List all available patterns
specql cicd search-pipeline --list

# Show pattern details
specql cicd search-pipeline --show python_fastapi_backend
```

**Options**:
- `--category CATEGORY`: Filter by category (backend, frontend, data, mobile)
- `--tags TAG1,TAG2`: Filter by tags
- `--language LANGUAGE`: Filter by programming language
- `--framework FRAMEWORK`: Filter by framework
- `--list`: List all available patterns
- `--show PATTERN_ID`: Show detailed information for specific pattern
- `--limit N`: Limit number of results (default: 10)

#### `cicd validate-pipeline`
Validate universal pipeline YAML syntax and semantics.

```bash
# Validate single pipeline file
specql cicd validate-pipeline pipeline.yaml

# Validate multiple files
specql cicd validate-pipeline pipelines/*.yaml

# Strict validation with all checks
specql cicd validate-pipeline pipeline.yaml --strict

# Show detailed validation report
specql cicd validate-pipeline pipeline.yaml --verbose
```

**Options**:
- `--strict`: Enable strict validation mode
- `--verbose, -v`: Show detailed validation messages
- `--format [text|json]`: Output format for validation results

#### `cicd benchmark`
Run performance benchmarks on CI/CD pipelines.

```bash
# Benchmark pipeline execution time
specql cicd benchmark execution pipeline.yaml --iterations 10

# Benchmark resource usage
specql cicd benchmark resources pipeline.yaml

# Compare performance across platforms
specql cicd benchmark compare pipeline.yaml --platforms github-actions,gitlab-ci

# Benchmark pattern library performance
specql cicd benchmark patterns --query "fastapi backend"
```

**Benchmark Types**:
- `execution`: Measure pipeline execution time
- `resources`: Monitor memory and CPU usage
- `compare`: Compare performance across platforms
- `patterns`: Benchmark pattern search performance
- `reliability`: Test pipeline success rates

**Options**:
- `--iterations N`: Number of benchmark iterations (default: 5)
- `--timeout MINUTES`: Benchmark timeout in minutes (default: 30)
- `--platforms P1,P2`: Platforms to compare (for compare benchmark)
- `--output FILE`: Save benchmark results to JSON file

#### `cicd recommend-pipeline`
Get AI-powered pipeline recommendations.

```bash
# Get recommendations for project type
specql cicd recommend-pipeline --language python --framework fastapi --database postgres

# Analyze existing pipeline for improvements
specql cicd recommend-pipeline pipeline.yaml --analyze

# Get security recommendations
specql cicd recommend-pipeline pipeline.yaml --security

# Suggest optimizations
specql cicd recommend-pipeline pipeline.yaml --optimize
```

**Options**:
- `--language LANGUAGE`: Programming language
- `--framework FRAMEWORK`: Framework name
- `--database DATABASE`: Database type
- `--analyze`: Analyze existing pipeline for improvements
- `--security`: Focus on security recommendations
- `--optimize`: Focus on performance optimizations
- `--model MODEL`: AI model to use (default: llama3.1)

#### `cicd optimize-pipeline`
Automatically optimize pipeline performance and structure.

```bash
# Optimize existing pipeline
specql cicd optimize-pipeline pipeline.yaml --output optimized.yaml

# Apply specific optimizations
specql cicd optimize-pipeline pipeline.yaml --caching --parallelization

# Optimize for specific platform
specql cicd optimize-pipeline pipeline.yaml --platform github-actions
```

**Optimization Types**:
- `--caching`: Add intelligent caching strategies
- `--parallelization`: Optimize job parallelization
- `--matrix`: Suggest matrix build optimizations
- `--artifacts`: Optimize artifact handling
- `--security`: Add security scanning optimizations

**Options**:
- `--platform PLATFORM`: Optimize for specific platform
- `--output FILE`: Output optimized pipeline file
- `--dry-run`: Show optimizations without applying them

### Documentation Commands

#### `docs generate`
Generate documentation from entities.

```bash
# Generate API documentation
specql docs generate entities/**/*.yaml --output docs/api/

# Generate entity relationship diagrams
specql docs generate entities/**/*.yaml --erd --output docs/diagrams/

# Generate with custom template
specql docs generate entities/**/*.yaml --template custom.md
```

**Options**:
- `--output DIRECTORY`: Documentation output directory
- `--erd`: Generate entity relationship diagrams
- `--template FILE`: Custom documentation template
- `--format [markdown|html|pdf]`: Documentation format

### Development Commands

#### `check-codes`
Validate table codes and numbering.

```bash
# Check codes for all entities
specql check-codes entities/**/*.yaml

# Check specific domain
specql check-codes entities/crm/**/*.yaml

# Auto-fix code issues
specql check-codes entities/**/*.yaml --fix

# Show detailed report
specql check-codes entities/**/*.yaml --verbose
```

**Options**:
- `--fix`: Automatically fix code issues
- `--verbose, -v`: Show detailed validation messages
- `--domain DOMAIN`: Check only specific domain

#### `diff`
Compare entity versions or schemas.

```bash
# Compare two entity files
specql diff entity_v1.yaml entity_v2.yaml

# Compare entity with generated SQL
specql diff entity.yaml --generated-sql schema.sql

# Compare with database schema
specql diff entity.yaml --database postgres://user:pass@localhost/db

# Show only breaking changes
specql diff entity_v1.yaml entity_v2.yaml --breaking-only
```

**Options**:
- `--generated-sql FILE`: Compare with generated SQL
- `--database URL`: Compare with database schema
- `--breaking-only`: Show only breaking changes
- `--format [text|json]`: Output format

### Performance Commands

#### `performance benchmark`
Run performance benchmarks.

```bash
# Benchmark entity generation
specql performance benchmark --type generation entities/**/*.yaml

# Benchmark pattern queries
specql performance benchmark --type patterns

# Benchmark reverse engineering
specql performance benchmark --type reverse reference_sql/**/*.sql

# Custom benchmark configuration
specql performance benchmark --config benchmark_config.yaml
```

#### `performance profile`
Profile SpecQL operations.

```bash
# Profile entity generation
specql performance profile generate entities/user.yaml

# Profile with flame graph
specql performance profile generate entities/**/*.yaml --flame-graph

# Profile memory usage
specql performance profile generate entities/**/*.yaml --memory
```

### Utility Commands

#### `help`
Show help information.

```bash
# General help
specql --help

# Command-specific help
specql generate --help
specql reverse --help

# Show version
specql --version
```

#### `version`
Show SpecQL version information.

```bash
specql version
specql --version
```

## Command Groups

Commands are organized into logical groups:

### Entity Management
- `generate`: Create code from YAML
- `validate`: Check YAML syntax
- `diff`: Compare versions
- `check-codes`: Validate numbering

### Template System
- `instantiate`: Create from templates
- `templates list`: Browse templates
- `templates show`: Template details
- `patterns list`: Browse patterns
- `patterns show`: Pattern details

### Registry Management
- `registry list-domains`: Domain listing
- `registry list-subdomains`: Subdomain listing
- `registry show-entity`: Entity details
- `registry add-domain`: Add domain
- `registry add-subdomain`: Add subdomain
- `registry validate`: Registry validation

### Data Integration
- `reverse`: SQL to YAML conversion
- `cdc enable/disable`: Change data capture

### CI/CD Pipeline Management
- `cicd convert-cicd`: Convert universal pipelines to platform-specific configs
- `cicd reverse-cicd`: Reverse engineer existing CI/CD configs
- `cicd generate-cicd`: Generate pipelines from entities or auto-detection
- `cicd search-pipeline`: Search pipeline patterns
- `cicd validate-pipeline`: Validate pipeline syntax
- `cicd benchmark`: Performance benchmarking
- `cicd recommend-pipeline`: AI-powered recommendations
- `cicd optimize-pipeline`: Automatic pipeline optimization

### Documentation
- `docs generate`: Create documentation

### Development Tools
- `performance benchmark`: Performance testing
- `performance profile`: Profiling tools

## Configuration

SpecQL can be configured through:

### Environment Variables
```bash
export SPECQL_DATABASE_URL="sqlite:///pattern_library.db"
export SPECQL_DEFAULT_FRAMEWORK="fraiseql"
export SPECQL_OUTPUT_DIR="migrations/"
export SPECQL_AI_MODEL="llama3.1"
```

### Configuration File
Create `specql.yaml` or `.specql.yaml`:

```yaml
database:
  url: "sqlite:///pattern_library.db"

generation:
  default_framework: "fraiseql"
  output_directory: "migrations/"
  include_table_views: true

reverse_engineering:
  ai_model: "llama3.1"
  confidence_threshold: 0.85
  batch_processing: true

cdc:
  retention_days: 30
  enable_compression: true
```

### Project-Specific Settings
Override settings per project in `pyproject.toml`:

```toml
[tool.specql]
database_url = "sqlite:///pattern_library.db"
default_framework = "fraiseql"
output_directory = "migrations/"
```

## Exit Codes

- `0`: Success
- `1`: General error
- `2`: Validation error
- `3`: Configuration error
- `4`: File system error
- `5`: Database error

## Examples

### Complete Workflow
```bash
# 1. Create entity from template
specql instantiate crm.contact --output contact.yaml

# 2. Customize the entity
# Edit contact.yaml with your requirements

# 3. Validate the YAML
specql validate contact.yaml

# 4. Generate PostgreSQL code
specql generate contact.yaml --target postgresql

# 5. Generate Django models
specql generate contact.yaml --target django

# 6. Check for issues
specql check-codes contact.yaml

# 7. Enable CDC if needed
specql cdc enable contact.yaml
```

### Migration Workflow
```bash
# 1. Reverse engineer existing SQL
specql reverse legacy_functions.sql --output migrated/

# 2. Validate converted entities
specql validate migrated/*.yaml

# 3. Generate new code
specql generate migrated/*.yaml

# 4. Compare with original
specql diff legacy_functions.sql --generated-sql generated/schema.sql
```

### Development Workflow
```bash
# Quick development iteration
specql generate entities/**/*.yaml --dev --verbose

# Run tests
pytest tests/

# Performance check
specql performance benchmark --type generation entities/**/*.yaml

# Generate documentation
specql docs generate entities/**/*.yaml
```

## Troubleshooting

### Common Issues

**"Command not found"**
```bash
# Install SpecQL
pip install specql

# Or run from source
python -m src.cli.main
```

**"Database connection failed"**
```bash
# Set database URL
export SPECQL_DATABASE_URL="sqlite:///pattern_library.db"

# Or use configuration file
echo "database:\n  url: 'sqlite:///pattern_library.db'" > .specql.yaml
```

**"Template not found"**
```bash
# List available templates
specql templates list

# Check template name spelling
specql templates show crm.contact
```

**"Validation errors"**
```bash
# Get detailed validation messages
specql validate entity.yaml --verbose

# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('entity.yaml'))"
```

### Getting Help

```bash
# General help
specql --help

# Command help
specql generate --help

# Version information
specql --version

# Check installation
specql version
```

## Related Documentation

- [Getting Started](../../getting_started.md) - Quick start guide
- [Actions Guide](../../guides/actions-guide.md) - YAML specification
- [Migration Guide](../../guides/migration_guide.md) - Converting existing code
- [Best Practices](../../guides/best_practices.md) - Development guidelines