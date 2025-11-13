# Week 01: Database Inventory & Reverse Engineering

**Objective**: Extract complete database schema and functions from PrintOptim

## Day 1-2: Database Assessment

```bash
cd ../printoptim_migration

# Create workspace structure
mkdir -p reverse_engineering/{assessments,mappings,patterns,issues}
mkdir -p reverse_engineering/sql_inventory/{tables,functions,views,types}
mkdir -p reverse_engineering/specql_output/{entities,actions}

# Run database inventory
psql printoptim_production_old << 'EOF' > reverse_engineering/assessments/database_inventory.txt
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY schemaname, tablename;
EOF

# Extract all table definitions
pg_dump printoptim_production_old --schema-only --no-owner --no-privileges \
  > reverse_engineering/assessments/old_production_schema.sql
```

## Day 3-4: Automated Reverse Engineering

```bash
cd /home/lionel/code/specql

# Reverse engineer all SQL functions
for sql_file in ../printoptim_migration/db/0_schema/**/*.sql; do
  uv run specql reverse "$sql_file" \
    --output-dir ../printoptim_migration/reverse_engineering/specql_output/entities \
    --min-confidence 0.70 \
    --verbose
done

# Generate report
uv run python scripts/migration/generate_reverse_engineering_report.py \
  ../printoptim_migration/reverse_engineering/specql_output/entities/ \
  > ../printoptim_migration/reverse_engineering/assessments/RE_REPORT.md
```

## Day 5: Manual Review & Enhancement

- Review low-confidence conversions (<70%)
- Enhance with business context
- Document assumptions
- Create `KNOWN_ISSUES.md`

## Deliverables

- ✅ Complete database inventory
- ✅ All entities in SpecQL YAML format (≥70% confidence)
- ✅ Reverse engineering quality report
- ✅ Known issues documented