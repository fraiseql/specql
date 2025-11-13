# Week 03: Schema Generation & Comparison

**Objective**: Generate new schema from SpecQL and validate against original

## Day 1-2: Schema Generation

```bash
cd /home/lionel/code/specql

# Generate complete schema from SpecQL YAML
uv run specql generate \
  ../printoptim_migration/reverse_engineering/specql_output/entities/**/*.yaml \
  --output-dir ../printoptim_migration/specql_generated_schema \
  --hierarchical \
  --include-tv \
  --verbose

# Build test database
cd ../printoptim_migration
dropdb --if-exists printoptim_specql_test
createdb printoptim_specql_test

# Apply generated schema with Confiture
confiture build --env specql_test
```

## Day 3-4: Schema Comparison

```bash
# Generate schema diff
confiture diff \
  --source printoptim_production_old \
  --target printoptim_specql_test \
  --output reverse_engineering/assessments/schema_diff.sql \
  --format sql

# Generate human-readable diff
confiture diff \
  --source printoptim_production_old \
  --target printoptim_specql_test \
  --output reverse_engineering/assessments/schema_diff.md \
  --format markdown

# Analyze differences
uv run python scripts/migration/analyze_schema_diff.py \
  reverse_engineering/assessments/schema_diff.json \
  > reverse_engineering/assessments/SCHEMA_DIFF_ANALYSIS.md
```

## Day 5: Gap Resolution

- Review all schema differences
- Adjust SpecQL YAML for critical gaps
- Document acceptable differences
- Create migration strategy

## Deliverables

- ✅ Generated schema from SpecQL
- ✅ Schema diff report (SQL + Markdown)
- ✅ Gap analysis document
- ✅ Migration strategy document