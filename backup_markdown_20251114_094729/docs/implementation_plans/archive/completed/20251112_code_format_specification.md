# SpecQL Code Format Specification

**Version**: 2.0 (REVISED with independent read-side sequencing)
**Date**: 2025-11-12

---

## Overview

SpecQL uses an 8-digit hexadecimal code system to organize SQL files hierarchically. Each digit has a specific meaning that determines the file's location in the directory structure.

**Format**: `0SDDSSEV`

---

## Digit Breakdown

### Position 1: Schema Prefix (X)
- **Always**: `0`
- **Purpose**: Indicates this is a schema file
- **Example**: `0`

---

### Position 2: Layer (S)
- **Values**:
  - `1` = write_side (tables, constraints, write operations)
  - `2` = read_side (views, table views, read operations)
  - `3` = functions (reusable functions, utilities)
- **Purpose**: Separates write-side from read-side
- **Example**: `1` (write) or `2` (read)

---

### Position 3-4: Domain Code (DD)
- **Values**: `01-99` (two digits)
- **Purpose**: Identifies the business domain
- **Examples**:
  - `01` = core (infrastructure)
  - `02` = crm (customer relationship management)
  - `03` = catalog (product catalog)
  - `04` = projects (project management)
  - `14` = dim (dimensions/reference data)

**Note**: First digit often used in directory name
- Domain `14` → directory `014_...`
- Domain `02` → directory `012_...` or `022_...` (layer + domain)

---

### Position 5-6: Subdomain Code (SS)
- **Values**: `01-99` (two digits)
- **Purpose**: Subdivides the domain
- **Examples** (within CRM domain `02`):
  - `01` = core (organization, user, team)
  - `02` = sales (opportunities, quotes)
  - `03` = customer (contacts, companies)
  - `04` = support (tickets, cases)

**Directory Naming**:
- Full code used: `0{domain}{subdomain}_{name}`
- Example: `0203_customer` (domain 2, subdomain 03)

---

### Position 7: Entity Sequence (E)
- **Values**: `0-9` (single digit, decimal)
- **Purpose**: Sequential number for entities within subdomain
- **CRITICAL**: **Independent per layer**
  - Write-side entity 1 ≠ Read-side entity 1
  - Each layer has its own sequence starting from 1

**Examples**:
- Write-side subdomain: entities 1, 2, 3, 4...
- Read-side same subdomain: entities 1, 2, 3, 4... (INDEPENDENT!)

**Limit**: Max 9 entities per subdomain per layer

---

### Position 8: File Number (V)
- **Values**: `0-9` (single digit, decimal)
- **Purpose**: Multiple files for same entity
- **Examples**:
  - `0` = primary file (tb_contact, tv_contact)
  - `1` = secondary file (additional view, helper)
  - `2` = tertiary file

**Common Patterns**:
- Write-side: `1` = main table, `2` = translation table (tl_*)
- Read-side: `0` = tv_*, `1` = v_*, `2` = mv_*

---

## Complete Examples

### Example 1: Write-Side Table

**Code**: `0120361`

**Breakdown**:
```
0  1  20  36  1
│  │  │   │   └─ File 1 (primary table file)
│  │  │   └───── Entity 36 in subdomain
│  │  └──────── Subdomain 36
│  └─────────── Layer 1 (write_side)
└────────────── Schema prefix
```

**Wait - this doesn't match!** Let me fix this...

Actually looking at the reference:
- `012036` would be parsed as: `0-1-2-03-6-?`

Let me re-examine the reference files more carefully...

**Code**: `0120361`

**Correct Breakdown**:
```
0  1  2  03  6  1
│  │  │  │   │  └─ File 1 for this entity
│  │  │  │   └──── Entity 6 in subdomain
│  │  │  └─────── Subdomain 03 (customer)
│  │  └────────── Domain 2 (CRM)
│  └───────────── Layer 1 (write_side)
└──────────────── Schema prefix (0)
```

**Path**: `01_write_side/012_crm/0123_customer/01236_contact/0120361_tb_contact.sql`

**Path Components**:
- `01_write_side/` - Layer 1
- `012_crm/` - Domain 2 (formatted as 0{layer}{domain})
- `0123_customer/` - Subdomain 03 (formatted as 0{layer}{domain}{subdomain[0]})
- `01236_contact/` - Entity directory
- `0120361_tb_contact.sql` - File 1

---

### Example 2: Read-Side Table View

**Code**: `0220130`

**Breakdown**:
```
0  2  2  03  1  3  0
│  │  │  │   │  │  └─ File 0 (primary tv_ file)
│  │  │  │   │  └──── Entity... wait this is 7 digits not 8!
```

I need to look at the actual reference more carefully. Let me check the pattern:

From reference: `02413_tv_location.sql` - this is 5 digits!

Ah! I think the format might be variable length or I'm misunderstanding. Let me look at actual reference examples:

- `014112_tb_location.sql` (6 digits)
- `02413_tv_location.sql` (5 digits)

This suggests the format isn't `0SDDSSEV` but something else. Let me reconsider...

Looking at:
- `014112` = 0-14-11-2 = Schema-Domain-Subdomain-File
- `02413` = 0-24-13-? or 0-2-41-3-?

Given the directory structure shows `024_dim` and `0241_geo`, I think:
- `024` = 0 (schema) + 2 (read layer) + 4 (domain)
- `0241` = 0 + 2 (read) + 4 (domain) + 1 (subdomain digit)

So the codes might be:
- `014112` = 0 (schema) + 14 (write+domain) + 11 (subdomain) + 2 (file)
- `02413` = 0 (schema) + 24 (read+domain) + 13 (?) + ...

I think I need to reconsider the entire format. The pattern seems to be:

**Write-side (6 digits)**: `0LDDSSF` where L+DD gives layer+domain as 2 digits
**Read-side (5 digits)**: `0LDDSEF` where sequence is different

Actually, let me just document what I observe from the reference and admit uncertainty on the exact parsing:

---

## REVISED: Observed Format from Reference

Based on actual reference files, the format appears to be:

### Write-Side Format
**Pattern**: `0{layer+domain}{subdomain}{sequence}{file}`
**Example**: `014112_tb_location.sql`

**Parsing**:
- `0` - Schema prefix
- `14` - Layer 1 + Domain 4 = "14"
- `11` - Subdomain 11 (but shows as "41" in directory `0141_geo`)
- `2` - File number

**Directory**: `01_write_side/014_dim/0141_geo/01411_location/014112_tb_location.sql`

**Pattern Observed**:
- First level: `01_write_side/`
- Second level: `014_dim/` (0 + layer + domain)
- Third level: `0141_geo/` (0 + layer + domain + subdomain first digit)
- Fourth level: `01411_location/` (0 + layer + domain + subdomain + entity)
- File: `014112_tb_location.sql` (full code + name)

### Read-Side Format
**Pattern**: `0{layer+domain}{subdomain}{entity}{file}`
**Example**: `02413_tv_location.sql`

**Parsing**:
- `0` - Schema prefix
- `24` - Layer 2 + Domain 4 = "24"
- `1` - Subdomain digit (partial)
- `3` - Entity/sequence number
- `0` - File number (not present in filename?)

**Directory**: `02_query_side/024_dim/0241_geo/02413_tv_location.sql`

**Pattern Observed**:
- First level: `02_query_side/`
- Second level: `024_dim/` (0 + layer + domain)
- Third level: `0241_geo/` (0 + layer + domain + subdomain first digit)
- File: `02413_tv_location.sql` (code + name)

---

## Key Observations

1. **Variable Length**: Write-side codes are 6 digits, read-side codes are 5 digits
2. **Layer + Domain**: Merged into 2 digits (14 = layer 1 + domain 4, 24 = layer 2 + domain 4)
3. **Independent Sequencing**: Read-side and write-side have independent numbering
4. **Directory Structure**: Hierarchical with progressive code building

---

## Critical Question for User

The exact parsing rules are unclear from observation alone. We need clarification on:

1. **Exact digit positions** - What does each digit mean?
2. **Why different lengths?** - Write-side 6 digits, read-side 5 digits
3. **How to parse domain/subdomain?** - Are they merged with layer?

**Recommendation**: Before implementing, we should:
1. Ask user to clarify exact format specification
2. Or analyze more reference examples to infer the pattern
3. Or examine any existing code in printoptim_specql that generates these codes

---

**STATUS**: INCOMPLETE - Needs clarification on exact code format parsing rules
