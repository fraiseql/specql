# Team E: Database Decisions Implementation Plan

**Team**: CLI & Orchestration
**Impact**: MEDIUM (orchestration of new components)
**Timeline**: Week 7 (3-4 days)
**Status**: 🟡 MEDIUM PRIORITY - Integration layer

---

## 📋 Overview

Team E must orchestrate the new database patterns:

1. ✅ Generate migrations in correct order (extensions → utilities → schema → triggers)
2. ✅ CLI commands for deduplication management
3. ✅ CLI commands for node+info split entities
4. ✅ Validation commands for INTEGER paths
5. ✅ Helper function integration in CLI

**Total Effort**: 3-4 days

---

## 🎯 Phase 1: Migration Orchestration (Day 1)

### **Objective**: Generate migrations in correct dependency order

### **1.1: Migration Order**

**File**: `src/cli/orchestrator.py`

```python
class MigrationOrchestrator:
    """Orchestrate migration generation with correct dependency order."""

    def generate_migrations(self, entities: list[EntityAST]) -> list[Migration]:
        """Generate all migrations in dependency order."""

        migrations = []

        # 1. Extensions (MUST be first)
        migrations.append(self.generate_extensions_migration())

        # 2. Utility Functions (depends on extensions)
        migrations.append(self.generate_utilities_migration())

        # 3. Schema (tables, indexes, constraints)
        for entity in entities:
            migrations.append(self.generate_schema_migration(entity))

        # 4. Triggers (depends on schema)
        for entity in entities:
            if entity.hierarchical:
                migrations.append(self.generate_triggers_migration(entity))

        # 5. Helper Functions (depends on schema)
        for entity in entities:
            if entity.hierarchical:
                migrations.append(self.generate_helpers_migration(entity))

        # 6. FraiseQL Annotations (depends on everything)
        migrations.append(self.generate_fraiseql_migration(entities))

        return migrations

    def generate_extensions_migration(self) -> Migration:
        """Generate 000_extensions.sql."""
        return Migration(
            number=0,
            name='extensions',
            content=self.render_template('sql/000_extensions.sql.jinja2')
        )

    def generate_utilities_migration(self) -> Migration:
        """Generate 001_utilities.sql with safe_slug."""
        return Migration(
            number=1,
            name='utilities',
            content=self.render_template('sql/utilities/safe_slug.sql.jinja2')
        )

    def generate_schema_migration(self, entity: EntityAST) -> Migration:
        """Generate schema with all new patterns."""

        components = []

        # Determine if split
        if entity.metadata_split:
            # Node table
            components.append(
                self.render_template(
                    'sql/node_info/node_table.sql.jinja2',
                    entity=entity
                )
            )
            # Info table
            components.append(
                self.render_template(
                    'sql/node_info/info_table.sql.jinja2',
                    entity=entity
                )
            )
            # View
            components.append(
                self.render_template(
                    'sql/node_info/view.sql.jinja2',
                    entity=entity
                )
            )
        else:
            # Single table
            components.append(
                self.render_template(
                    'sql/schema/table.sql.jinja2',
                    entity=entity
                )
            )

        # Indexes (tenant-scoped)
        components.append(
            self.render_template(
                'sql/schema/tenant_indexes.sql.jinja2',
                entity=entity
            )
        )

        return Migration(
            number=self.next_migration_number(),
            name=f'{entity.schema}_{entity.name.lower()}',
            content='\n\n'.join(components)
        )

    def generate_triggers_migration(self, entity: EntityAST) -> Migration:
        """Generate safety triggers."""

        triggers = []

        # 1. Cycle prevention
        triggers.append(
            self.render_template(
                'sql/constraints/prevent_cycle.sql.jinja2',
                entity=entity
            )
        )

        # 2. Sequence limit
        triggers.append(
            self.render_template(
                'sql/constraints/check_sequence_limit.sql.jinja2',
                entity=entity
            )
        )

        # 3. Depth limit
        triggers.append(
            self.render_template(
                'sql/constraints/check_depth_limit.sql.jinja2',
                entity=entity
            )
        )

        # 4. Path update trigger
        triggers.append(
            self.render_template(
                'sql/hierarchy/update_path_trigger.sql.jinja2',
                entity=entity
            )
        )

        return Migration(
            number=self.next_migration_number(),
            name=f'{entity.schema}_{entity.name.lower()}_triggers',
            content='\n\n'.join(triggers)
        )

    def generate_helpers_migration(self, entity: EntityAST) -> Migration:
        """Generate helper functions."""

        helpers = []

        # Path calculation
        helpers.append(
            self.render_template(
                'sql/hierarchy/calculate_path.sql.jinja2',
                entity=entity
            )
        )

        # Descendant recalculation
        helpers.append(
            self.render_template(
                'sql/hierarchy/recalculate_descendants.sql.jinja2',
                entity=entity
            )
        )

        # 5 helper functions
        for helper_name in ['ancestors', 'descendants', 'move_subtree', 'root', 'depth']:
            helpers.append(
                self.render_template(
                    f'sql/helpers/get_{helper_name}.sql.jinja2',
                    entity=entity
                )
            )

        return Migration(
            number=self.next_migration_number(),
            name=f'{entity.schema}_{entity.name.lower()}_helpers',
            content='\n\n'.join(helpers)
        )
```

---

## 🎯 Phase 2: Deduplication Management CLI (Day 2)

### **Objective**: CLI commands for managing identifier deduplication

### **2.1: List Duplicates Command**

**File**: `src/cli/commands/deduplication.py`

```python
@cli.command()
@click.option('--entity', required=True, help='Entity name')
@click.option('--schema', default='public', help='Schema name')
@click.option('--min-count', default=2, help='Minimum duplicate count')
def list_duplicates(entity: str, schema: str, min_count: int):
    """List identifier duplicates for an entity."""

    entity_lower = entity.lower()
    table_name = f"{schema}.tb_{entity_lower}"

    query = f"""
    SELECT
        identifier,
        COUNT(*) as variant_count,
        array_agg(display_identifier ORDER BY sequence_number) as variants
    FROM {table_name}
    WHERE deleted_at IS NULL
    GROUP BY identifier
    HAVING COUNT(*) >= %s
    ORDER BY variant_count DESC;
    """

    results = execute_query(query, (min_count,))

    if not results:
        click.echo(f"No duplicates found for {entity}")
        return

    click.echo(f"\nDuplicates for {entity}:\n")

    for row in results:
        identifier = row['identifier']
        count = row['variant_count']
        variants = row['variants']

        click.echo(f"  {identifier}: {count} variants")
        for variant in variants:
            click.echo(f"    - {variant}")
        click.echo()

# Example usage:
# $ specql list-duplicates --entity=Location --schema=tenant
#
# Duplicates for Location:
#
#   headquarters: 3 variants
#     - headquarters
#     - headquarters#2
#     - headquarters#3
#
#   office: 2 variants
#     - office
#     - office#2
```

---

### **2.2: Recalculate Identifiers Command**

**File**: `src/cli/commands/recalculate.py`

```python
@cli.command()
@click.option('--entity', required=True, help='Entity name')
@click.option('--schema', default='public', help='Schema name')
@click.option('--tenant-id', help='Limit to specific tenant (UUID)')
@click.option('--dry-run', is_flag=True, help='Show what would change without updating')
def recalculate_identifiers(
    entity: str,
    schema: str,
    tenant_id: str = None,
    dry_run: bool = False
):
    """Recalculate identifiers for an entity."""

    entity_lower = entity.lower()
    function_name = f"{schema}.recalculate_{entity_lower}_identifiers_bulk"

    if dry_run:
        click.echo(f"[DRY RUN] Would call: {function_name}({tenant_id or 'ALL'})")

        # Preview changes
        preview_query = f"""
        SELECT
            id,
            identifier as current_identifier,
            {schema}.calculate_{entity_lower}_identifier(pk_{entity_lower}) as new_identifier,
            CASE
                WHEN identifier = {schema}.calculate_{entity_lower}_identifier(pk_{entity_lower})
                THEN 'NO CHANGE'
                ELSE 'WOULD UPDATE'
            END as status
        FROM {schema}.tb_{entity_lower}
        WHERE deleted_at IS NULL
          AND ({tenant_id} IS NULL OR tenant_id = %s)
        LIMIT 20;
        """

        results = execute_query(preview_query, (tenant_id,) if tenant_id else ())

        click.echo("\nPreview (first 20 rows):\n")
        for row in results:
            status_color = 'yellow' if row['status'] == 'WOULD UPDATE' else 'green'
            click.secho(
                f"  {row['id']}: {row['current_identifier']} → {row['new_identifier']} ({row['status']})",
                fg=status_color
            )

        click.echo("\nUse --no-dry-run to apply changes")
        return

    # Execute recalculation
    click.echo(f"Recalculating identifiers for {entity}...")

    call_query = f"SELECT {function_name}(%s) as updated_count;"
    result = execute_query(call_query, (tenant_id,))

    updated_count = result[0]['updated_count']

    click.secho(f"✓ Updated {updated_count} identifier(s)", fg='green')
```

---

## 🎯 Phase 3: Node+Info Split Management (Day 3)

### **Objective**: CLI commands for split entities

### **3.1: List Split Entities Command**

```python
@cli.command()
def list_split_entities():
    """List all entities using node+info split pattern."""

    # Detect split entities by checking for _node and _info tables
    query = """
    SELECT
        n.table_schema,
        REPLACE(n.table_name, '_node', '') as entity_name,
        (SELECT COUNT(*) FROM information_schema.tables t
         WHERE t.table_schema = n.table_schema
           AND t.table_name = REPLACE(n.table_name, '_node', '_info')) as has_info_table,
        (SELECT COUNT(*) FROM information_schema.views v
         WHERE v.table_schema = n.table_schema
           AND v.table_name = 'v_' || REPLACE(n.table_name, 'tb_', '')
           AND v.table_name LIKE '%' || REPLACE(n.table_name, '_node', '') || '%') as has_view
    FROM information_schema.tables n
    WHERE n.table_name LIKE '%_node'
      AND n.table_type = 'BASE TABLE'
    ORDER BY n.table_schema, entity_name;
    """

    results = execute_query(query)

    if not results:
        click.echo("No split entities found")
        return

    click.echo("\nSplit Entities:\n")

    for row in results:
        schema = row['table_schema']
        entity = row['entity_name'].replace('tb_', '')
        has_info = row['has_info_table'] > 0
        has_view = row['has_view'] > 0

        status = '✓' if (has_info and has_view) else '⚠'
        click.echo(f"  {status} {schema}.{entity}")

        if not has_info:
            click.secho(f"      Missing: {schema}.tb_{entity}_info", fg='red')
        if not has_view:
            click.secho(f"      Missing: {schema}.v_{entity}", fg='red')
```

---

### **3.2: Validate Split Integrity Command**

```python
@cli.command()
@click.option('--entity', required=True, help='Entity name')
@click.option('--schema', default='public', help='Schema name')
def validate_split_integrity(entity: str, schema: str):
    """Validate node+info split integrity."""

    entity_lower = entity.lower()

    checks = []

    # Check 1: All nodes have info records
    check1 = f"""
    SELECT COUNT(*) as orphaned_nodes
    FROM {schema}.tb_{entity_lower}_node n
    LEFT JOIN {schema}.tb_{entity_lower}_info i
        ON i.pk_{entity_lower}_info = n.fk_{entity_lower}_info
    WHERE i.pk_{entity_lower}_info IS NULL;
    """

    # Check 2: All info records are referenced
    check2 = f"""
    SELECT COUNT(*) as orphaned_info
    FROM {schema}.tb_{entity_lower}_info i
    LEFT JOIN {schema}.tb_{entity_lower}_node n
        ON n.fk_{entity_lower}_info = i.pk_{entity_lower}_info
    WHERE n.pk_{entity_lower} IS NULL;
    """

    # Check 3: Tenant consistency
    check3 = f"""
    SELECT COUNT(*) as tenant_mismatch
    FROM {schema}.tb_{entity_lower}_node n
    INNER JOIN {schema}.tb_{entity_lower}_info i
        ON i.pk_{entity_lower}_info = n.fk_{entity_lower}_info
    WHERE n.tenant_id != i.tenant_id;
    """

    orphaned_nodes = execute_query(check1)[0]['orphaned_nodes']
    orphaned_info = execute_query(check2)[0]['orphaned_info']
    tenant_mismatch = execute_query(check3)[0]['tenant_mismatch']

    all_ok = True

    click.echo(f"\nValidating {entity} split integrity:\n")

    if orphaned_nodes > 0:
        click.secho(f"  ✗ {orphaned_nodes} node(s) missing info records", fg='red')
        all_ok = False
    else:
        click.secho(f"  ✓ All nodes have info records", fg='green')

    if orphaned_info > 0:
        click.secho(f"  ✗ {orphaned_info} orphaned info record(s)", fg='red')
        all_ok = False
    else:
        click.secho(f"  ✓ No orphaned info records", fg='green')

    if tenant_mismatch > 0:
        click.secho(f"  ✗ {tenant_mismatch} tenant mismatch(es)", fg='red')
        all_ok = False
    else:
        click.secho(f"  ✓ Tenant IDs consistent", fg='green')

    if all_ok:
        click.secho(f"\n✓ {entity} split integrity: OK", fg='green', bold=True)
    else:
        click.secho(f"\n✗ {entity} split integrity: ERRORS FOUND", fg='red', bold=True)
```

---

## 🎯 Phase 4: INTEGER Path Validation (Day 4)

### **Objective**: Validate INTEGER-based LTREE paths

### **4.1: Validate Paths Command**

```python
@cli.command()
@click.option('--entity', required=True, help='Entity name')
@click.option('--schema', default='public', help='Schema name')
@click.option('--fix', is_flag=True, help='Fix invalid paths')
def validate_paths(entity: str, schema: str, fix: bool = False):
    """Validate INTEGER-based LTREE paths."""

    entity_lower = entity.lower()
    table_name = f"{schema}.tb_{entity_lower}"

    checks = []

    # Check 1: Path format (should be pure digits: "1.5.23.47")
    check1 = f"""
    SELECT id, path
    FROM {table_name}
    WHERE path::text !~ '^[0-9]+(\\.[0-9]+)*$'
      AND deleted_at IS NULL
    LIMIT 10;
    """

    # Check 2: Path consistency (path should match calculated path)
    check2 = f"""
    SELECT
        id,
        path as current_path,
        {schema}.calculate_{entity_lower}_path(pk_{entity_lower}) as expected_path
    FROM {table_name}
    WHERE path IS DISTINCT FROM {schema}.calculate_{entity_lower}_path(pk_{entity_lower})
      AND deleted_at IS NULL
    LIMIT 10;
    """

    # Check 3: Path includes own PK (last segment should be pk_{entity})
    check3 = f"""
    SELECT id, pk_{entity_lower}, path
    FROM {table_name}
    WHERE NOT (path::text ~ ('\\.' || pk_{entity_lower}::text || '$')
           OR path::text = pk_{entity_lower}::text)
      AND deleted_at IS NULL
    LIMIT 10;
    """

    invalid_format = execute_query(check1)
    inconsistent = execute_query(check2)
    wrong_pk = execute_query(check3)

    all_ok = True

    click.echo(f"\nValidating {entity} paths:\n")

    # Format validation
    if invalid_format:
        click.secho(f"  ✗ {len(invalid_format)} path(s) with invalid format", fg='red')
        for row in invalid_format[:3]:
            click.echo(f"      {row['id']}: {row['path']}")
        all_ok = False
    else:
        click.secho(f"  ✓ All paths have valid INTEGER format", fg='green')

    # Consistency validation
    if inconsistent:
        click.secho(f"  ✗ {len(inconsistent)} inconsistent path(s)", fg='red')
        for row in inconsistent[:3]:
            click.echo(f"      {row['id']}: {row['current_path']} (should be {row['expected_path']})")
        all_ok = False
    else:
        click.secho(f"  ✓ All paths consistent with hierarchy", fg='green')

    # PK validation
    if wrong_pk:
        click.secho(f"  ✗ {len(wrong_pk)} path(s) missing own PK", fg='red')
        for row in wrong_pk[:3]:
            click.echo(f"      {row['id']}: pk={row['pk_' + entity_lower]}, path={row['path']}")
        all_ok = False
    else:
        click.secho(f"  ✓ All paths include own PK", fg='green')

    if all_ok:
        click.secho(f"\n✓ {entity} paths: OK", fg='green', bold=True)
    else:
        click.secho(f"\n✗ {entity} paths: ERRORS FOUND", fg='red', bold=True)

        if fix:
            click.echo("\nFixing paths...")

            fix_query = f"""
            SELECT {schema}.recalculate_{entity_lower}_descendant_paths(NULL);
            """

            execute_query(fix_query)
            click.secho("✓ Paths recalculated", fg='green')
        else:
            click.echo("\nUse --fix to recalculate paths")
```

---

## 📊 Summary: Team E Deliverables

### **Files to Create**

| File | Purpose | Lines |
|------|---------|-------|
| `src/cli/orchestrator.py` | Migration ordering | 150 |
| `src/cli/commands/deduplication.py` | Dedup management | 100 |
| `src/cli/commands/recalculate.py` | Identifier recalc | 80 |
| `src/cli/commands/split_entities.py` | Node+info management | 120 |
| `src/cli/commands/validate_paths.py` | Path validation | 100 |

### **New CLI Commands**

| Command | Purpose |
|---------|---------|
| `specql list-duplicates` | Show identifier duplicates |
| `specql recalculate-identifiers` | Recalc identifiers for entity |
| `specql list-split-entities` | Show node+info split entities |
| `specql validate-split-integrity` | Check node+info consistency |
| `specql validate-paths` | Validate INTEGER paths |

### **Timeline**

- **Day 1**: Migration orchestration
- **Day 2**: Deduplication CLI commands
- **Day 3**: Node+info split CLI commands
- **Day 4**: Path validation CLI commands

**Total**: 4 days

---

## ✅ Acceptance Criteria

- [ ] Migrations generated in correct order
- [ ] Extensions generated first
- [ ] Utilities generated after extensions
- [ ] Triggers generated after schema
- [ ] Deduplication CLI commands work
- [ ] Split entity CLI commands work
- [ ] Path validation CLI commands work
- [ ] All commands have `--help` documentation

---

## 🔗 Dependencies

**Depends On**:
- Team B (all phases - provides templates)
- Team C (action generation)
- Team D (FraiseQL annotations)

**Blocks**:
- None (final integration layer)

---

**Status**: 🟡 WAITING ON ALL TEAMS
**Priority**: MEDIUM (integration)
**Effort**: 4 days
**Start**: After Teams B, C, D complete
