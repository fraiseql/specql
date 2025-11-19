# Organization, Time & Technology Entities

> **Enterprise-grade organizational hierarchy, temporal analytics, and technical infrastructure management**

## Overview

The **org**, **time**, **tech**, and **common** stdlib modules provide essential building blocks for enterprise applications:

- **org**: Hierarchical organizational structures (departments, divisions, teams)
- **time**: Temporal analytics and date dimension tables
- **tech**: Operating system and platform lifecycle management
- **common**: Shared reference data (industries, genres)

These modules handle complex patterns like recursive hierarchies, temporal analysis, and multi-level classifications that are tedious to build from scratch.

---

## Organization Entities (`stdlib/org/`)

### OrganizationalUnit

**Category**: Multi-tenant (`schema: tenant`)
**Pattern**: Hierarchical (recursive tree structure)
**Standard**: N/A

Represents departments, divisions, sites, or any hierarchical unit within an organization.

#### Entity Definition

```yaml
entity: OrganizationalUnit
schema: tenant
hierarchical: true

fields:
  abbreviation: text           # "HR", "IT", "R&D"
  short_name: text             # "Human Resources"
  name: text                   # "Human Resources Department"

  customer_org: ref(Organization)
    schema: management
    nullable: false

  organizational_unit_level: ref(OrganizationalUnitLevel)
    schema: common
    nullable: false

  parent_organizational_unit: ref(OrganizationalUnit)  # Recursive!

translations:
  enabled: true
  fields: [name, short_name]
```

#### Key Features

1. **Recursive Hierarchy**: Units can have parent units, creating unlimited depth
2. **Level Classification**: Each unit has a defined level (e.g., Division > Department > Team)
3. **Multi-Language**: Names translated automatically
4. **Organization Scoping**: Units belong to specific organizations

#### Pre-Built Actions

```yaml
actions:
  # CRUD
  - create_organizational_unit
  - update_organizational_unit
  - delete_organizational_unit

  # Business logic
  - activate_unit
  - deactivate_unit
  - change_parent           # Move unit in hierarchy
  - update_abbreviation
  - reorder_siblings        # Change display order
  - merge_units             # Consolidate two units
```

#### Common Use Cases

**Corporate Structure**:
```
Acme Corp
├── Executive (Division)
│   ├── CEO Office (Department)
│   └── Board Relations (Department)
├── Engineering (Division)
│   ├── Backend Team (Department)
│   ├── Frontend Team (Department)
│   └── DevOps (Department)
└── Sales (Division)
    ├── Enterprise Sales (Department)
    └── SMB Sales (Department)
```

**Hospital Structure**:
```
City Hospital
├── Medical Services (Division)
│   ├── Emergency (Department)
│   ├── Surgery (Department)
│   └── Cardiology (Department)
└── Administrative (Division)
    ├── HR (Department)
    └── Finance (Department)
```

#### Example: Import and Extend

```yaml
# Import stdlib organizational unit
from: stdlib/org/organizational_unit

# Add custom fields specific to your business
extend: OrganizationalUnit
  custom_fields:
    budget_allocation: money
    headcount: integer
    cost_center_code: text
    manager: ref(Employee)
```

#### SQL Generated

```sql
-- Trinity pattern table
CREATE TABLE tenant.tb_organizational_unit (
    pk_organizational_unit INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    identifier TEXT NOT NULL,
    tenant_id UUID NOT NULL,

    -- Fields
    abbreviation TEXT,
    short_name TEXT,
    name TEXT NOT NULL,

    -- Relationships
    customer_org_fk INTEGER NOT NULL REFERENCES management.tb_organization(pk_organization),
    organizational_unit_level_fk INTEGER NOT NULL REFERENCES common.tb_organizational_unit_level(pk_organizational_unit_level),
    parent_organizational_unit_fk INTEGER REFERENCES tenant.tb_organizational_unit(pk_organizational_unit),

    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_tb_organizational_unit_customer_org_fk ON tenant.tb_organizational_unit(customer_org_fk);
CREATE INDEX idx_tb_organizational_unit_parent ON tenant.tb_organizational_unit(parent_organizational_unit_fk);
CREATE INDEX idx_tb_organizational_unit_tenant_id ON tenant.tb_organizational_unit(tenant_id);
```

### OrganizationalUnitLevel

**Category**: Shared (`schema: common`)
**Pattern**: Simple reference table
**Standard**: N/A

Defines the hierarchy levels (e.g., Division, Department, Team).

```yaml
entity: OrganizationalUnitLevel
schema: common

fields:
  name: text                   # "Division", "Department", "Team"
  hierarchy_level: integer     # 1, 2, 3 (for ordering)

translations:
  enabled: true
  fields: [name]
```

---

## Time Entities (`stdlib/time/`)

### Calendar

**Category**: Shared (`schema: common`)
**Pattern**: Date dimension table (analytics)
**Standard**: N/A

A pre-populated date dimension table that provides temporal analytics capabilities.

#### Entity Definition

```yaml
entity: Calendar
schema: common

fields:
  # Primary date
  reference_date: date

  # Time period identifiers
  week: integer
  half_month: integer
  month: integer
  quarter: integer
  semester: integer
  year: integer

  # Period day counts
  week_n_days: integer
  half_month_n_days: integer
  month_n_days: integer
  quarter_n_days: integer
  semester_n_days: integer
  year_n_days: integer

  # Reference dates (first day of period)
  week_reference_date: date
  half_month_reference_date: date
  month_reference_date: date
  quarter_reference_date: date
  semester_reference_date: date
  year_reference_date: date

  # Flags (is this date the first day of period?)
  is_week_reference_date: boolean
  is_half_month_reference_date: boolean
  is_month_reference_date: boolean
  is_quarter_reference_date: boolean
  is_semester_reference_date: boolean
  is_year_reference_date: boolean

  # Computed metadata (JSON)
  date_info: json
  week_info: json
  month_info: json
  quarter_info: json
  year_info: json
```

#### Key Features

1. **Pre-Populated**: Typically filled with 10+ years of dates
2. **Multi-Granularity**: Analyze by week, month, quarter, semester, year
3. **Fast Joins**: Optimized for analytical queries
4. **Fiscal Calendar Support**: Customize for fiscal years

#### Pre-Built Actions

```yaml
actions:
  # CRUD
  - create_calendar
  - update_calendar
  - delete_calendar

  # Business logic
  - calculate_date_ranges
  - get_business_days
  - check_holiday
  - get_fiscal_period
```

#### Common Use Cases

**Sales Analytics**:
```sql
-- Monthly sales report
SELECT
  c.year,
  c.month,
  SUM(o.total) AS monthly_revenue
FROM orders o
JOIN common.tb_calendar c ON o.order_date = c.reference_date
WHERE c.year = 2025
GROUP BY c.year, c.month, c.month_reference_date
ORDER BY c.month_reference_date;
```

**Quarterly Performance**:
```sql
-- Quarterly comparison
SELECT
  c.year,
  c.quarter,
  COUNT(DISTINCT c2.id) AS new_customers,
  SUM(o.total) AS revenue
FROM common.tb_calendar c
LEFT JOIN crm.tb_contact c2 ON DATE(c2.created_at) = c.reference_date
LEFT JOIN orders o ON DATE(o.created_at) = c.reference_date
WHERE c.year IN (2024, 2025)
  AND c.is_quarter_reference_date = TRUE
GROUP BY c.year, c.quarter
ORDER BY c.year, c.quarter;
```

**Week-over-Week Growth**:
```sql
-- WoW growth rate
WITH weekly_sales AS (
  SELECT
    c.week_reference_date,
    SUM(o.total) AS week_revenue
  FROM orders o
  JOIN common.tb_calendar c ON DATE(o.order_date) = c.reference_date
  GROUP BY c.week_reference_date
)
SELECT
  w1.week_reference_date,
  w1.week_revenue,
  w2.week_revenue AS prev_week_revenue,
  ROUND(100.0 * (w1.week_revenue - w2.week_revenue) / w2.week_revenue, 2) AS growth_pct
FROM weekly_sales w1
JOIN weekly_sales w2 ON w2.week_reference_date = w1.week_reference_date - INTERVAL '1 week'
ORDER BY w1.week_reference_date DESC;
```

#### Example: Extend for Fiscal Year

```yaml
# Import stdlib calendar
from: stdlib/time/calendar

# Add fiscal year logic
extend: Calendar
  custom_fields:
    fiscal_year: integer
    fiscal_quarter: integer
    fiscal_month: integer
    is_fiscal_year_end: boolean
```

---

## Technology Entities (`stdlib/tech/`)

### OperatingSystem

**Category**: Shared (`schema: common`)
**Pattern**: Lifecycle management
**Standard**: N/A

Tracks operating system versions with release and end-of-life dates.

#### Entity Definition

```yaml
entity: OperatingSystem
schema: common

fields:
  name: text                      # "macOS 12 Monterey", "Ubuntu 22.04 LTS"
  release_date: date
  endoflife_date: date

  operating_system_platform: ref(OperatingSystemPlatform)  # macOS, Windows, Linux
```

#### Pre-Built Actions

```yaml
actions:
  # CRUD
  - create_operating_system
  - update_operating_system
  - delete_operating_system

  # Business logic
  - activate_os
  - deactivate_os
  - mark_end_of_life
  - update_release_date
```

#### Common Use Cases

**IT Asset Management**:
```yaml
# Track which servers run which OS
entity: Server
fields:
  hostname: text
  operating_system: ref(OperatingSystem)
    schema: common

actions:
  - name: check_end_of_life
    steps:
      - validate: operating_system.endoflife_date > CURRENT_DATE
        error: "Operating system is end-of-life. Please upgrade."
```

**Compatibility Matrix**:
```sql
-- Find devices running unsupported OS versions
SELECT
  d.name AS device_name,
  os.name AS os_version,
  os.endoflife_date,
  CURRENT_DATE - os.endoflife_date AS days_past_eol
FROM devices d
JOIN common.tb_operating_system os ON d.operating_system_fk = os.pk_operating_system
WHERE os.endoflife_date < CURRENT_DATE
ORDER BY os.endoflife_date;
```

### OperatingSystemPlatform

**Category**: Shared (`schema: common`)
**Pattern**: Simple classification
**Standard**: N/A

Defines OS families (Windows, macOS, Linux, etc.).

```yaml
entity: OperatingSystemPlatform
schema: common

fields:
  name: text                      # "Windows", "macOS", "Linux", "Android"
  vendor: text                    # "Microsoft", "Apple", "Various"

translations:
  enabled: true
  fields: [name]
```

---

## Common Reference Entities (`stdlib/common/`)

### Industry

**Category**: Shared (`schema: common`)
**Pattern**: Hierarchical classification
**Standard**: N/A

Represents hierarchical industry/business sector classification.

#### Entity Definition

```yaml
entity: Industry
schema: common
hierarchical: true

fields:
  name: text                      # "Healthcare", "Manufacturing"
  nomenclature: text              # "NAICS 62", "SIC 20"

  parent: ref(Industry)           # Recursive hierarchy

translations:
  enabled: true
  fields: [name]
```

#### Pre-Built Actions

```yaml
actions:
  # CRUD
  - create_industry
  - update_industry
  - delete_industry

  # Business logic
  - activate_industry
  - deactivate_industry
  - change_parent
  - update_nomenclature
```

#### Common Use Cases

**CRM Industry Classification**:
```
Healthcare
├── Hospitals
├── Clinics
└── Pharmaceuticals
    ├── Biotech
    └── Generic Drugs

Manufacturing
├── Automotive
│   ├── Electric Vehicles
│   └── Internal Combustion
└── Aerospace
```

**Organization Categorization**:
```yaml
entity: Organization
fields:
  name: text
  industry: ref(Industry)
    schema: common

# Filter organizations by industry hierarchy
action: get_organizations_by_industry
  steps:
    - query: |
        SELECT o.*
        FROM tb_organization o
        JOIN common.tb_industry i ON o.industry_fk = i.pk_industry
        WHERE i.pk_industry = $industry_id
           OR i.parent_fk = $industry_id  -- Include sub-industries
```

### Genre

**Category**: Shared (`schema: common`)
**Pattern**: Simple classification
**Standard**: N/A

General-purpose categorization (e.g., music genres, book categories).

```yaml
entity: Genre
schema: common

fields:
  name: text                      # "Science Fiction", "Jazz", "Documentary"
  category: text                  # "Books", "Music", "Films"

translations:
  enabled: true
  fields: [name]
```

---

## Combining stdlib Modules

### Example: Enterprise HR System

```yaml
# Import multiple stdlib modules
from: stdlib/crm/contact
from: stdlib/org/organizational_unit
from: stdlib/common/industry

# Define custom entities that reference stdlib
entity: Employee
schema: tenant
fields:
  employee_id: text!
  contact: ref(Contact)            # stdlib CRM
    schema: crm

  organizational_unit: ref(OrganizationalUnit)  # stdlib org
    schema: tenant

  hire_date: date
  termination_date: date

actions:
  - name: assign_to_department
    steps:
      - validate: organizational_unit EXISTS
      - update: Employee SET organizational_unit = $new_unit

entity: Organization
schema: management
fields:
  legal_name: text
  industry: ref(Industry)          # stdlib common
    schema: common

  founded_date: date
```

### Example: SaaS Analytics Dashboard

```yaml
# Temporal analytics with stdlib calendar
from: stdlib/time/calendar

entity: UserActivity
schema: analytics
fields:
  user_id: uuid
  activity_date: date
  page_views: integer
  session_duration: integer

# Pre-built action leveraging stdlib
action: monthly_active_users
  description: "Calculate MAU using stdlib calendar"
  steps:
    - query: |
        SELECT
          c.year,
          c.month,
          COUNT(DISTINCT ua.user_id) AS monthly_active_users
        FROM analytics.tb_user_activity ua
        JOIN common.tb_calendar c ON ua.activity_date = c.reference_date
        WHERE c.month_reference_date = $target_month
        GROUP BY c.year, c.month
```

---

## Performance Considerations

### Calendar Pre-Population

The `Calendar` entity should be **pre-populated** during database initialization:

```sql
-- Populate 10 years of calendar data (2020-2030)
INSERT INTO common.tb_calendar (reference_date, week, month, quarter, year, ...)
SELECT
  date_series AS reference_date,
  EXTRACT(WEEK FROM date_series) AS week,
  EXTRACT(MONTH FROM date_series) AS month,
  EXTRACT(QUARTER FROM date_series) AS quarter,
  EXTRACT(YEAR FROM date_series) AS year,
  -- ... computed fields
FROM generate_series('2020-01-01'::DATE, '2030-12-31'::DATE, '1 day'::INTERVAL) AS date_series;
```

### Hierarchical Queries

For deep organizational hierarchies, use PostgreSQL **recursive CTEs**:

```sql
-- Get all descendants of a unit
WITH RECURSIVE org_tree AS (
  -- Base case: starting unit
  SELECT pk_organizational_unit, name, parent_organizational_unit_fk, 1 AS level
  FROM tenant.tb_organizational_unit
  WHERE pk_organizational_unit = $start_unit

  UNION ALL

  -- Recursive case: children
  SELECT u.pk_organizational_unit, u.name, u.parent_organizational_unit_fk, t.level + 1
  FROM tenant.tb_organizational_unit u
  JOIN org_tree t ON u.parent_organizational_unit_fk = t.pk_organizational_unit
)
SELECT * FROM org_tree ORDER BY level, name;
```

---

## Migration Guide

### From Custom Organizational Structure

**Before** (Custom implementation):
```sql
CREATE TABLE departments (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  parent_id INTEGER REFERENCES departments(id),
  company_id INTEGER NOT NULL
);
```

**After** (stdlib import):
```yaml
from: stdlib/org/organizational_unit
from: stdlib/org/organizational_unit_level

# Extend if needed
extend: OrganizationalUnit
  custom_fields:
    legacy_department_id: integer
```

**Benefits**:
- ✅ Trinity pattern identifiers
- ✅ Multi-language support
- ✅ Pre-built actions
- ✅ Audit trail
- ✅ Tenant isolation

### From Custom Date Dimension

**Before** (Manual date table):
```sql
CREATE TABLE dim_date (
  date_key INTEGER PRIMARY KEY,
  full_date DATE,
  year INTEGER,
  month INTEGER,
  -- ... 50 more columns
);
```

**After** (stdlib import):
```yaml
from: stdlib/time/calendar

# Ready to use!
```

**Benefits**:
- ✅ Pre-populated data
- ✅ Standardized naming
- ✅ Computed JSON metadata
- ✅ Business day calculations
- ✅ Fiscal year support

---

## Summary

### stdlib Modules Covered

| Module   | Entities                          | Use Cases                                    |
|----------|-----------------------------------|----------------------------------------------|
| **org**  | OrganizationalUnit, UnitLevel     | Corporate hierarchies, department management |
| **time** | Calendar                          | Temporal analytics, date dimensions          |
| **tech** | OperatingSystem, OSPlatform       | IT asset management, lifecycle tracking      |
| **common** | Industry, Genre                 | Classification, categorization               |

### Key Patterns

1. **Hierarchical Entities**: Recursive self-references for tree structures
2. **Date Dimensions**: Pre-populated analytics tables
3. **Lifecycle Management**: Track release dates and end-of-life
4. **Multi-Language**: Automatic translation support

### Next Steps

1. **Explore Action Patterns**: See `action-patterns.md` for CRUD, state machines, workflows
2. **Learn Infrastructure**: See `infrastructure-overview.md` for deployment patterns
3. **Reference Documentation**: Check `yaml-syntax.md` for complete SpecQL grammar

---

**Last Updated**: 2025-11-19
**Version**: 1.0
**Coverage**: org, time, tech, common stdlib modules
