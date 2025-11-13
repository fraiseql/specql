# Week 02: Python Business Logic Reverse Engineering

**Objective**: Convert Python models, validators, and services to SpecQL actions

## Day 1-2: Python Code Inventory

```bash
cd ../printoptim_migration

# Find all Python models
find . -name "*.py" -path "*/models/*" > reverse_engineering/python_inventory/models_list.txt

# Find all service files
find . -name "*.py" -path "*/services/*" > reverse_engineering/python_inventory/services_list.txt

# Find all validators
find . -name "*.py" -path "*/validators/*" > reverse_engineering/python_inventory/validators_list.txt
```

## Day 3-4: Automated Python Reverse Engineering

```bash
cd /home/lionel/code/specql

# Reverse engineer Python models
for py_file in ../printoptim_migration/models/*.py; do
  uv run specql reverse python "$py_file" \
    --output-dir ../printoptim_migration/reverse_engineering/specql_output/entities \
    --discover-patterns \
    --verbose
done

# Reverse engineer services (business logic → actions)
for py_file in ../printoptim_migration/services/*.py; do
  uv run specql reverse python "$py_file" \
    --output-dir ../printoptim_migration/reverse_engineering/specql_output/actions \
    --extract-actions \
    --verbose
done
```

## Day 5: Integration & Validation

- Merge entity definitions from SQL and Python
- Validate consistency
- Identify conflicts
- Create unified SpecQL YAML

## Deliverables

- ✅ Python business logic mapped to SpecQL
- ✅ All actions in SpecQL YAML
- ✅ Merged entity definitions
- ✅ Validation report