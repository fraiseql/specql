# SpecQL Enhanced Type System Specification

**Date**: 2025-11-13
**Status**: 🟢 Approved
**Implementation**: Weeks 12-14

---

## 🎯 Design Principles

1. **Backward Compatible**: Existing `integer`, `text`, `decimal` still work
2. **Progressive Disclosure**: Simple by default, powerful when needed
3. **Context-Aware**: Smart defaults inferred from usage
4. **Explicit Control**: Override defaults with subtypes
5. **Cross-Language Accurate**: Precise mapping to all target languages

---

## 📋 Complete Type System

### Format: `type:subtype`

**Examples:**
```yaml
fields:
  age: integer              # Smart default → integer:small
  user_id: integer:big      # Explicit → bigint
  price: decimal:money      # Explicit → numeric(10,2)
  email: text               # Smart default → text:short
```

---

## 1️⃣ Integer Types

### Syntax
```yaml
fields:
  # Simple (smart defaults)
  id: integer                    # → integer:big (PK inferred)
  age: integer                   # → integer:small (range inferred)
  count: integer                 # → integer:int (general use)

  # Explicit subtypes
  tiny_val: integer:tiny         # tinyint/smallint (0-255)
  small_val: integer:small       # smallint (-32K to 32K)
  int_val: integer:int           # integer (-2B to 2B)
  big_val: integer:big           # bigint (-9Q to 9Q)
```

### Database Mappings

| SpecQL | PostgreSQL | MySQL | SQLite |
|--------|-----------|-------|--------|
| `integer:tiny` | SMALLINT | TINYINT | INTEGER |
| `integer:small` | SMALLINT | SMALLINT | INTEGER |
| `integer:int` | INTEGER | INT | INTEGER |
| `integer:big` | BIGINT | BIGINT | INTEGER |
| `integer` | INTEGER* | INT* | INTEGER |

*Context-aware default

### Language Mappings

| SpecQL | Python | Java | Rust | TypeScript | Go |
|--------|--------|------|------|------------|-----|
| `integer:tiny` | int | Short | i16 | number | int16 |
| `integer:small` | int | Integer | i32 | number | int32 |
| `integer:int` | int | Integer | i32 | number | int32 |
| `integer:big` | int | Long | i64 | number/bigint | int64 |
| `integer` | int | Integer* | i32* | number | int32* |

### Inference Rules

```python
def infer_integer_subtype(field: Field, entity: Entity) -> str:
    # Primary keys
    if field.is_primary_key or field.name in ['id', 'pk']:
        return 'big'

    # Foreign keys
    if field.name.endswith('_id') or field.field_type == 'ref':
        return 'big'

    # Age/count patterns
    if re.match(r'(age|years?|months?|days?)', field.name, re.I):
        return 'small'

    # Tiny numbers (flags, small enums)
    if re.match(r'(flag|status_code|type_id)', field.name, re.I):
        return 'tiny'

    # Large numbers
    if re.match(r'(population|revenue|bytes|size)', field.name, re.I):
        return 'big'

    # Default
    return 'int'
```

---

## 2️⃣ Decimal Types

### Syntax
```yaml
fields:
  # Simple (smart defaults)
  price: decimal                 # → decimal:money
  latitude: decimal              # → decimal:geo
  tax_rate: decimal              # → decimal:percent

  # Explicit subtypes
  price: decimal:money           # numeric(10,2) - currency
  tax: decimal:percent           # numeric(5,4) - percentages
  lat: decimal:geo               # numeric(9,6) - GPS coordinates
  scientific: decimal:precise    # numeric(18,8) - high precision
  general: decimal:standard      # numeric(15,4) - general use
```

### Database Mappings

| SpecQL | PostgreSQL | MySQL | SQLite |
|--------|-----------|-------|--------|
| `decimal:money` | NUMERIC(10,2) | DECIMAL(10,2) | REAL |
| `decimal:percent` | NUMERIC(5,4) | DECIMAL(5,4) | REAL |
| `decimal:geo` | NUMERIC(9,6) | DECIMAL(9,6) | REAL |
| `decimal:precise` | NUMERIC(18,8) | DECIMAL(18,8) | REAL |
| `decimal:standard` | NUMERIC(15,4) | DECIMAL(15,4) | REAL |
| `decimal` | NUMERIC(15,4)* | DECIMAL(15,4)* | REAL |

### Language Mappings

| SpecQL | Python | Java | Rust | TypeScript | Go |
|--------|--------|------|------|------------|-----|
| `decimal:money` | Decimal | BigDecimal | rust_decimal::Decimal | number | decimal.Decimal |
| `decimal:percent` | Decimal | BigDecimal | rust_decimal::Decimal | number | decimal.Decimal |
| `decimal:geo` | Decimal | BigDecimal | f64 | number | float64 |
| `decimal:precise` | Decimal | BigDecimal | rust_decimal::Decimal | number | decimal.Decimal |
| `decimal:standard` | Decimal | BigDecimal | rust_decimal::Decimal | number | decimal.Decimal |
| `decimal` | Decimal | BigDecimal | rust_decimal::Decimal | number | decimal.Decimal |

### Inference Rules

```python
def infer_decimal_subtype(field: Field) -> str:
    # Money patterns
    money_patterns = ['price', 'cost', 'amount', 'fee', 'salary', 'wage', 'payment']
    if any(p in field.name.lower() for p in money_patterns):
        return 'money'

    # Percentage patterns
    percent_patterns = ['rate', 'percent', 'ratio', 'tax']
    if any(p in field.name.lower() for p in percent_patterns):
        return 'percent'

    # Geo patterns
    geo_patterns = ['lat', 'long', 'latitude', 'longitude', 'coordinate']
    if any(p in field.name.lower() for p in geo_patterns):
        return 'geo'

    # Scientific patterns
    science_patterns = ['coefficient', 'constant', 'measure', 'calculation']
    if any(p in field.name.lower() for p in science_patterns):
        return 'precise'

    return 'standard'
```

---

## 3️⃣ Text Types

### Syntax
```yaml
fields:
  # Simple (smart defaults)
  email: text                    # → text:short (unique inferred)
  name: text                     # → text:short
  description: text              # → text:long
  content: text                  # → text:full

  # Explicit subtypes
  code: text:tiny                # varchar(10) - codes, abbreviations
  username: text:short           # varchar(255) - indexed strings
  summary: text:medium           # varchar(1000) - medium text
  body: text:long                # text - long content
  article: text:full             # text - unlimited
```

### Database Mappings

| SpecQL | PostgreSQL | MySQL | SQLite |
|--------|-----------|-------|--------|
| `text:tiny` | VARCHAR(10) | VARCHAR(10) | TEXT |
| `text:short` | VARCHAR(255) | VARCHAR(255) | TEXT |
| `text:medium` | VARCHAR(1000) | TEXT | TEXT |
| `text:long` | TEXT | TEXT | TEXT |
| `text:full` | TEXT | LONGTEXT | TEXT |
| `text` | VARCHAR(255)* | VARCHAR(255)* | TEXT |

*Smart default based on context

### Language Mappings

| SpecQL | Python | Java | Rust | TypeScript | Go |
|--------|--------|------|------|------------|-----|
| `text:tiny` | str | String | String | string | string |
| `text:short` | str | String | String | string | string |
| `text:medium` | str | String | String | string | string |
| `text:long` | str | String | String | string | string |
| `text:full` | str | String | String | string | string |
| `text` | str | String | String | string | string |

### Inference Rules

```python
def infer_text_subtype(field: Field) -> str:
    # Unique fields should be short (for indexing)
    if field.unique or field.is_indexed:
        return 'short'

    # Tiny patterns (codes, abbreviations)
    tiny_patterns = ['code', 'abbr', 'abbreviation', 'currency', 'country']
    if any(p in field.name.lower() for p in tiny_patterns):
        return 'tiny'

    # Short patterns (typical indexed fields)
    short_patterns = ['email', 'username', 'name', 'title', 'label', 'tag']
    if any(p in field.name.lower() for p in short_patterns):
        return 'short'

    # Medium patterns
    medium_patterns = ['summary', 'excerpt', 'abstract', 'snippet']
    if any(p in field.name.lower() for p in medium_patterns):
        return 'medium'

    # Long patterns
    long_patterns = ['description', 'bio', 'notes', 'comment', 'message']
    if any(p in field.name.lower() for p in long_patterns):
        return 'long'

    # Full patterns
    full_patterns = ['content', 'body', 'text', 'article', 'document']
    if any(p in field.name.lower() for p in full_patterns):
        return 'full'

    # Default to short (safe for indexing)
    return 'short'
```

---

## 4️⃣ Float Types

### Syntax
```yaml
fields:
  # Simple
  temperature: float             # → float:double (default)

  # Explicit subtypes
  simple: float:single           # real/float4 (7 digits precision)
  precise: float:double          # double precision/float8 (15 digits)
```

### Database Mappings

| SpecQL | PostgreSQL | MySQL | SQLite |
|--------|-----------|-------|--------|
| `float:single` | REAL | FLOAT | REAL |
| `float:double` | DOUBLE PRECISION | DOUBLE | REAL |
| `float` | DOUBLE PRECISION | DOUBLE | REAL |

### Language Mappings

| SpecQL | Python | Java | Rust | TypeScript | Go |
|--------|--------|------|------|------------|-----|
| `float:single` | float | Float | f32 | number | float32 |
| `float:double` | float | Double | f64 | number | float64 |
| `float` | float | Double | f64 | number | float64 |

---

## 5️⃣ JSON Types

### Syntax
```yaml
fields:
  # Simple
  metadata: json                 # → json:any (any JSON)

  # Explicit subtypes
  config: json:object            # jsonb, enforce object {}
  tags: json:array               # jsonb, enforce array []
  raw: json:raw                  # json (not jsonb) - preserve format
```

### Database Mappings

| SpecQL | PostgreSQL | MySQL | SQLite |
|--------|-----------|-------|--------|
| `json:object` | JSONB + CHECK | JSON | TEXT |
| `json:array` | JSONB + CHECK | JSON | TEXT |
| `json:raw` | JSON | JSON | TEXT |
| `json` | JSONB | JSON | TEXT |

### Language Mappings

| SpecQL | Python | Java | Rust | TypeScript | Go |
|--------|--------|------|------|------------|-----|
| `json:object` | dict | JsonNode | serde_json::Map | Record<string, any> | map[string]interface{} |
| `json:array` | list | JsonNode | Vec<Value> | Array<any> | []interface{} |
| `json:raw` | str | String | String | string | string |
| `json` | dict/list | JsonNode | Value | any | interface{} |

---

## 6️⃣ Binary Types

### Syntax
```yaml
fields:
  # New binary types
  avatar: binary:small           # bytea (< 1MB)
  file: binary:large             # bytea/blob (> 1MB)
  hash: binary:fixed             # bytea with fixed length
```

### Database Mappings

| SpecQL | PostgreSQL | MySQL | SQLite |
|--------|-----------|-------|--------|
| `binary:small` | BYTEA | BLOB | BLOB |
| `binary:large` | BYTEA | LONGBLOB | BLOB |
| `binary:fixed` | BYTEA | BINARY | BLOB |
| `binary` | BYTEA | BLOB | BLOB |

### Language Mappings

| SpecQL | Python | Java | Rust | TypeScript | Go |
|--------|--------|------|------|------------|-----|
| `binary:small` | bytes | byte[] | Vec<u8> | Buffer | []byte |
| `binary:large` | bytes | byte[] | Vec<u8> | Buffer | []byte |
| `binary:fixed` | bytes | byte[] | [u8; N] | Buffer | [N]byte |
| `binary` | bytes | byte[] | Vec<u8> | Buffer | []byte |

---

## 7️⃣ Date/Time Types

### Syntax
```yaml
fields:
  # Existing
  created_at: timestamp          # timestamptz (with timezone)
  birthdate: date                # date only

  # New subtypes
  scheduled_at: timestamp:tz     # timestamptz (explicit timezone)
  event_time: timestamp:local    # timestamp (no timezone)
  duration: interval             # interval (time duration)
```

### Database Mappings

| SpecQL | PostgreSQL | MySQL | SQLite |
|--------|-----------|-------|--------|
| `timestamp:tz` | TIMESTAMPTZ | DATETIME | TEXT |
| `timestamp:local` | TIMESTAMP | TIMESTAMP | TEXT |
| `timestamp` | TIMESTAMPTZ | DATETIME | TEXT |
| `date` | DATE | DATE | TEXT |
| `time` | TIME | TIME | TEXT |
| `interval` | INTERVAL | N/A | TEXT |

### Language Mappings

| SpecQL | Python | Java | Rust | TypeScript | Go |
|--------|--------|------|------|------------|-----|
| `timestamp:tz` | datetime | Instant | DateTime<Utc> | Date | time.Time |
| `timestamp:local` | datetime | LocalDateTime | NaiveDateTime | Date | time.Time |
| `date` | date | LocalDate | NaiveDate | Date | time.Time |
| `time` | time | LocalTime | NaiveTime | Date | time.Time |
| `interval` | timedelta | Duration | Duration | number | time.Duration |

---

## 🧠 Type Inference Engine

### Implementation

**File**: `src/core/type_inference.py`

```python
"""
Type Inference Engine

Infers subtypes from context when not explicitly specified.
"""

from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class TypeInferenceContext:
    """Context for type inference"""
    field_name: str
    is_primary_key: bool = False
    is_foreign_key: bool = False
    is_unique: bool = False
    is_indexed: bool = False
    entity_name: Optional[str] = None


class TypeInferenceEngine:
    """Infer subtypes from context"""

    def infer_subtype(
        self,
        field_type: str,
        context: TypeInferenceContext
    ) -> str:
        """
        Infer subtype from context

        Args:
            field_type: Base type (integer, decimal, text, etc.)
            context: Inference context

        Returns:
            Inferred subtype
        """
        if field_type == "integer":
            return self._infer_integer(context)
        elif field_type == "decimal":
            return self._infer_decimal(context)
        elif field_type == "text":
            return self._infer_text(context)
        elif field_type == "float":
            return self._infer_float(context)
        elif field_type == "json":
            return self._infer_json(context)
        else:
            return None  # No subtype

    def _infer_integer(self, ctx: TypeInferenceContext) -> str:
        """Infer integer subtype"""
        name = ctx.field_name.lower()

        # Primary/Foreign keys → big
        if ctx.is_primary_key or ctx.is_foreign_key:
            return 'big'

        # ID fields → big
        if name in ['id', 'pk'] or name.endswith('_id'):
            return 'big'

        # Tiny patterns (flags, small enums)
        tiny_patterns = [
            r'^(is|has|can)_',  # Boolean-like flags
            r'_flag$',
            r'status_code',
            r'type_id',
        ]
        if any(re.search(p, name) for p in tiny_patterns):
            return 'tiny'

        # Small patterns (age, counts, limited ranges)
        small_patterns = [
            r'age$',
            r'^(year|month|day|hour|minute)s?$',
            r'quantity',
            r'count$',
            r'_count$',
        ]
        if any(re.search(p, name) for p in small_patterns):
            return 'small'

        # Large patterns (big numbers)
        large_patterns = [
            r'population',
            r'revenue',
            r'bytes',
            r'size$',
            r'_size$',
            r'total',
            r'_total$',
        ]
        if any(re.search(p, name) for p in large_patterns):
            return 'big'

        # Default
        return 'int'

    def _infer_decimal(self, ctx: TypeInferenceContext) -> str:
        """Infer decimal subtype"""
        name = ctx.field_name.lower()

        # Money patterns
        money_patterns = [
            r'price',
            r'cost',
            r'amount',
            r'fee',
            r'salary',
            r'wage',
            r'payment',
            r'revenue',
            r'balance',
        ]
        if any(re.search(p, name) for p in money_patterns):
            return 'money'

        # Percentage patterns
        percent_patterns = [
            r'rate$',
            r'_rate$',
            r'percent',
            r'ratio',
            r'tax',
        ]
        if any(re.search(p, name) for p in percent_patterns):
            return 'percent'

        # Geo patterns
        geo_patterns = [
            r'lat(itude)?$',
            r'lon(g(itude)?)?$',
            r'coordinate',
        ]
        if any(re.search(p, name) for p in geo_patterns):
            return 'geo'

        # Scientific patterns
        science_patterns = [
            r'coefficient',
            r'constant',
            r'measurement',
            r'precision',
        ]
        if any(re.search(p, name) for p in science_patterns):
            return 'precise'

        return 'standard'

    def _infer_text(self, ctx: TypeInferenceContext) -> str:
        """Infer text subtype"""
        name = ctx.field_name.lower()

        # Unique/indexed fields → short (for performance)
        if ctx.is_unique or ctx.is_indexed:
            return 'short'

        # Tiny patterns (codes, abbreviations)
        tiny_patterns = [
            r'^code$',
            r'_code$',
            r'abbr(eviation)?',
            r'currency',
            r'country_',
            r'language_',
        ]
        if any(re.search(p, name) for p in tiny_patterns):
            return 'tiny'

        # Short patterns
        short_patterns = [
            r'email',
            r'username',
            r'^name$',
            r'_name$',
            r'title',
            r'label',
            r'tag',
            r'slug',
            r'url',
            r'phone',
        ]
        if any(re.search(p, name) for p in short_patterns):
            return 'short'

        # Medium patterns
        medium_patterns = [
            r'summary',
            r'excerpt',
            r'abstract',
            r'snippet',
            r'subtitle',
        ]
        if any(re.search(p, name) for p in medium_patterns):
            return 'medium'

        # Long patterns
        long_patterns = [
            r'description',
            r'bio',
            r'notes?$',
            r'comment',
            r'message',
            r'reason',
        ]
        if any(re.search(p, name) for p in long_patterns):
            return 'long'

        # Full patterns
        full_patterns = [
            r'content',
            r'body',
            r'^text$',
            r'article',
            r'document',
            r'markdown',
            r'html',
        ]
        if any(re.search(p, name) for p in full_patterns):
            return 'full'

        # Default to short (safe for indexing)
        return 'short'

    def _infer_float(self, ctx: TypeInferenceContext) -> str:
        """Infer float subtype"""
        name = ctx.field_name.lower()

        # Single precision patterns (when precision not critical)
        single_patterns = [
            r'temperature',
            r'humidity',
            r'speed',
        ]
        if any(re.search(p, name) for p in single_patterns):
            return 'single'

        # Default to double (safer)
        return 'double'

    def _infer_json(self, ctx: TypeInferenceContext) -> str:
        """Infer JSON subtype"""
        name = ctx.field_name.lower()

        # Object patterns
        object_patterns = [
            r'config',
            r'settings',
            r'options',
            r'metadata',
            r'properties',
        ]
        if any(re.search(p, name) for p in object_patterns):
            return 'object'

        # Array patterns
        array_patterns = [
            r'tags?$',
            r'items',
            r'list$',
            r'_list$',
            r'array',
            r'entries',
        ]
        if any(re.search(p, name) for p in array_patterns):
            return 'array'

        # Default to any
        return 'any'
```

---

## 📝 YAML Examples

### Example 1: E-commerce Platform

```yaml
entity: Product
fields:
  # IDs (auto-inferred → big)
  id: integer                        # → integer:big (PK)
  merchant_id: integer               # → integer:big (FK)
  category_id: integer               # → integer:big (FK)

  # Quantities
  stock_quantity: integer:small      # Explicit (0-65K)
  units_sold: integer                # → integer:int (general)
  views_count: integer               # → integer:big (large numbers)

  # Money
  price: decimal:money               # Explicit → numeric(10,2)
  discount_percent: decimal:percent  # Explicit → numeric(5,4)
  tax_rate: decimal                  # → decimal:percent (inferred)

  # Text
  sku: text:short {unique: true}     # Explicit → varchar(255)
  name: text                         # → text:short (inferred)
  description: text                  # → text:long (inferred)
  specifications: text:full          # Explicit → text

  # Binary
  thumbnail: binary:small            # < 1MB

  # Metadata
  attributes: json:object            # Enforce object type
  tags: json:array                   # Enforce array type
```

**Generated PostgreSQL:**
```sql
CREATE TABLE products (
    -- IDs
    pk_product INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    id UUID DEFAULT gen_random_uuid() NOT NULL,
    merchant_id BIGINT NOT NULL,
    category_id BIGINT NOT NULL,

    -- Quantities
    stock_quantity SMALLINT DEFAULT 0,
    units_sold INTEGER DEFAULT 0,
    views_count BIGINT DEFAULT 0,

    -- Money
    price NUMERIC(10,2) NOT NULL,
    discount_percent NUMERIC(5,4) DEFAULT 0,
    tax_rate NUMERIC(5,4) DEFAULT 0,

    -- Text
    sku VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    specifications TEXT,

    -- Binary
    thumbnail BYTEA,

    -- Metadata
    attributes JSONB DEFAULT '{}',
    tags JSONB DEFAULT '[]',

    -- Trinity audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Constraints
    CONSTRAINT chk_product_attributes_object
        CHECK (jsonb_typeof(attributes) = 'object'),
    CONSTRAINT chk_product_tags_array
        CHECK (jsonb_typeof(tags) = 'array')
);
```

### Example 2: Geolocation Service

```yaml
entity: Location
fields:
  id: integer                    # → integer:big

  # Geo coordinates (explicit)
  latitude: decimal:geo          # numeric(9,6)
  longitude: decimal:geo         # numeric(9,6)
  altitude: decimal:standard     # numeric(15,4)

  # Precision
  accuracy: float:single         # real (sufficient for GPS)

  # Address
  country_code: text:tiny        # varchar(10)
  city: text:short               # varchar(255)
  address: text:medium           # varchar(1000)
  directions: text:long          # text
```

---

## 🔄 Migration Guide

### For Existing SpecQL Projects

**Step 1: Analyze Current Types**
```bash
# Scan existing YAML
specql analyze entities/*.yaml

# Output:
# Found 45 integer fields
#   - 12 could be integer:small (age, count)
#   - 8 could be integer:big (already IDs)
#   - 25 are integer:int (appropriate)
#
# Found 23 text fields
#   - 15 could be text:short (email, name)
#   - 8 could be text:long (description, bio)
```

**Step 2: Add Subtypes (Optional)**
```bash
# Auto-add inferred subtypes
specql migrate --add-subtypes entities/*.yaml

# Creates: entities/*.specql.yaml (with subtypes)
```

**Step 3: Review & Customize**
```bash
# Review suggestions
git diff entities/

# Customize as needed
vim entities/product.yaml

# Regenerate schema
specql generate entities/*.yaml
```

---

## ✅ Backward Compatibility

**Existing YAML works unchanged:**

```yaml
# Old YAML (no subtypes)
entity: User
fields:
  id: integer
  email: text
  age: integer
```

**Still generates correctly with smart defaults:**
- `id: integer` → `BIGINT` (PK inferred)
- `email: text` → `VARCHAR(255)` (indexed field)
- `age: integer` → `SMALLINT` (range inferred)

**No breaking changes!**

---

## 📊 Implementation Checklist

- [ ] **Week 12 Day 1**: Type inference engine
- [ ] **Week 12 Day 2**: Parser updates for subtypes
- [ ] **Week 12 Day 3**: PostgreSQL type mapper
- [ ] **Week 12 Day 4**: Python type mapper
- [ ] **Week 12 Day 5**: Integration tests
- [ ] **Week 13**: Java, Rust type mappers
- [ ] **Week 14**: TypeScript, Go type mappers
- [ ] **Week 15**: CLI migration tools
- [ ] **Weeks 23-38**: All reverse engineering type detection

---

**Status**: 🟢 Ready for Implementation
**Priority**: High (foundational for multi-language support)
**Impact**: Precise type control, better performance, accurate code generation
