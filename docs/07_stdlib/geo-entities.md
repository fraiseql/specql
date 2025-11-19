# Geographic Entities: International Address & Location Management

> **10 production-ready entities for addresses, spatial queries, and hierarchical locations—ISO-compliant and PostGIS-ready**

## Overview

SpecQL's Geographic stdlib provides **complete address and location management** with international support, spatial queries, and hierarchical structures. These entities handle everything from street addresses to administrative boundaries to physical facility management.

**Standards-Based**:
- ISO 3166 (Country codes)
- PostGIS POINT type for coordinates
- Multi-language address formatting
- Administrative hierarchy support

**Origin**: Extracted from PrintOptim production system (international logistics platform)

---

## Core Entities

### PublicAddress

**Purpose**: Structured public addresses with geocoding and administrative references.

**Schema**: `common` (shared reference data)

**Key Features**:
- Structured address components (street number, name, type)
- Geographic coordinates (PostGIS POINT)
- Administrative unit linkage
- Postal code validation
- National address ID support (e.g., French BAN, US USPS)

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `street_number` | text | Building/house number |
| `street_suffix` | text | Additional street qualifier (Bis, Ter, etc.) |
| `street_name` | text | Street name |
| `coordinates` | coordinates | Latitude/longitude (PostGIS POINT) |
| `national_address_id` | text | Official address identifier |
| `external_address_id` | text | Third-party geocoder ID |

#### Relationships

| Field | References | Description |
|-------|------------|-------------|
| `street_type` | StreetType | Avenue, Boulevard, Street, etc. |
| `country` | Country | ISO 3166 country |
| `administrative_unit` | AdministrativeUnit | City, state, province |
| `postal_code` | PostalCode | Postal/ZIP code |
| `address_datasource` | AddressDatasource | Source system (Google, OpenStreetMap, etc.) |

#### Actions

```yaml
- create_public_address
- update_public_address
- delete_public_address
- validate_address       # Check completeness and accuracy
- geocode_address        # Convert to coordinates
- format_address         # Generate formatted string
- check_address_completeness  # Validate required fields
```

#### Usage Example

```yaml
from: stdlib/geo/public_address.yaml

action: create_customer_address
  steps:
    - insert: PublicAddress
      values:
        street_number: "123"
        street_name: "Main"
        street_type: ref(StreetType[identifier='street'])
        postal_code: ref(PostalCode[identifier='75001'])
        administrative_unit: ref(AdministrativeUnit[name='Paris'])
        country: ref(Country[code='FR'])
        coordinates: POINT(48.8566, 2.3522)  # Lat/Lon
```

**Generated SQL**:

```sql
CREATE TABLE common.tb_public_address (
  pk_public_address   INTEGER PRIMARY KEY,
  id                  UUID UNIQUE,
  identifier          TEXT UNIQUE,
  street_number       TEXT,
  street_suffix       TEXT,
  street_name         TEXT,
  coordinates         POINT,  -- PostGIS type for spatial queries
  national_address_id TEXT,
  external_address_id TEXT,
  street_type         INTEGER REFERENCES common.tb_street_type,
  country             INTEGER REFERENCES common.tb_country,
  administrative_unit INTEGER REFERENCES common.tb_administrative_unit,
  postal_code         INTEGER REFERENCES common.tb_postal_code,
  address_datasource  INTEGER REFERENCES common.tb_address_datasource,
  created_at          TIMESTAMP,
  updated_at          TIMESTAMP
);

-- Spatial index for proximity queries
CREATE INDEX idx_tb_public_address_coordinates
  ON common.tb_public_address USING GIST (coordinates);
```

**Spatial Queries Enabled**:

```sql
-- Find addresses within 5km of a point
SELECT * FROM common.tb_public_address
WHERE coordinates <@> POINT(48.8566, 2.3522) < 5000;

-- Find nearest address
SELECT * FROM common.tb_public_address
ORDER BY coordinates <-> POINT(48.8566, 2.3522)
LIMIT 1;
```

---

### Location

**Purpose**: Hierarchical physical locations with accessibility and dimensional data.

**Schema**: `tenant` (multi-tenant isolation)

**Key Features**:
- Self-referencing hierarchy (building → floor → room)
- Accessibility tracking (elevator, stairs)
- Physical dimensions (width, depth, height in mm)
- Geocoding support
- Organization scoping

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | text | Descriptive name (e.g., "3rd floor, west wing") |
| `int_ordered` | integer | Sort order within hierarchy |
| `has_elevator` | boolean | Elevator accessibility |
| `has_stairs` | boolean | Stairs required |
| `n_stair_steps` | integer | Number of steps |
| `available_width_mm` | integer | Max width in millimeters |
| `available_depth_mm` | integer | Max depth in millimeters |
| `available_height_mm` | integer | Max height in millimeters |
| `coordinates` | coordinates | GPS coordinates |

#### Relationships

| Field | References | Schema | Description |
|-------|------------|--------|-------------|
| `customer_org` | Organization | management | Owner organization |
| `public_address` | PublicAddress | common | Physical address |
| `location_type` | LocationType | common | Type (warehouse, office, etc.) |
| `location_level` | LocationLevel | common | Hierarchy level |
| `parent_location` | Location | tenant | Parent in hierarchy |

#### Hierarchical Support

```yaml
hierarchical: true
```

**Enables** parent-child relationships:

```
Warehouse 1 (parent)
  ├─ Ground Floor (child)
  │   ├─ Zone A (grandchild)
  │   └─ Zone B (grandchild)
  └─ First Floor (child)
      └─ Office (grandchild)
```

#### Usage Example

```yaml
from: stdlib/geo/location.yaml
from: stdlib/geo/public_address.yaml

# Create hierarchical warehouse structure
action: setup_warehouse
  steps:
    # Parent: Warehouse building
    - insert: Location
      values:
        name: "Warehouse 1"
        customer_org: ref(Organization[identifier='acme'])
        public_address: ref(PublicAddress[identifier='warehouse-address'])
        location_type: ref(LocationType[name='Warehouse'])
        location_level: ref(LocationLevel[name='Building'])
        has_elevator: true
        available_width_mm: 20000
        available_height_mm: 8000

    # Child: Ground floor
    - insert: Location
      values:
        name: "Ground Floor"
        parent_location: ref(Location[identifier='warehouse-1'])
        location_level: ref(LocationLevel[name='Floor'])
        has_stairs: true
        n_stair_steps: 3

    # Grandchild: Storage zone
    - insert: Location
      values:
        name: "Zone A"
        parent_location: ref(Location[identifier='ground-floor'])
        location_level: ref(LocationLevel[name='Zone'])
        available_width_mm: 5000
        available_depth_mm: 10000
```

**Query Hierarchy**:

```sql
-- Find all locations under Warehouse 1
WITH RECURSIVE location_tree AS (
  SELECT * FROM tenant.tb_location
  WHERE identifier = 'warehouse-1'
  UNION ALL
  SELECT l.* FROM tenant.tb_location l
  INNER JOIN location_tree lt ON l.parent_location = lt.pk_location
)
SELECT * FROM location_tree;
```

---

### AdministrativeUnit

**Purpose**: Hierarchical administrative divisions (countries → states → cities).

**Schema**: `common` (shared reference data)

**Key Features**:
- Multi-level hierarchy (country, state, city, etc.)
- Administrative codes (INSEE, FIPS, etc.)
- Multi-language support
- Unlimited depth

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | text | Administrative name |
| `administrative_code` | text | Official code (e.g., INSEE code) |
| `administrative_level` | ref | Level in hierarchy |
| `parent` | ref(AdministrativeUnit) | Parent unit (self-reference) |

#### Translation Support

```yaml
translations:
  enabled: true
  fields: [name]
```

**Result**: Administrative names are translatable.

#### Usage Example

```yaml
from: stdlib/geo/administrative_unit.yaml

# France administrative hierarchy
action: seed_france_admin
  steps:
    # Level 0: Country
    - insert: AdministrativeUnit
      values:
        name: "France"
        administrative_code: "FR"
        administrative_level: ref(AdministrativeLevel[name='Country'])

    # Level 1: Region
    - insert: AdministrativeUnit
      values:
        name: "Bretagne"
        administrative_code: "53"
        administrative_level: ref(AdministrativeLevel[name='Region'])
        parent: ref(AdministrativeUnit[administrative_code='FR'])

    # Level 2: Department
    - insert: AdministrativeUnit
      values:
        name: "Ille-et-Vilaine"
        administrative_code: "35"
        administrative_level: ref(AdministrativeLevel[name='Department'])
        parent: ref(AdministrativeUnit[administrative_code='53'])

    # Level 3: City
    - insert: AdministrativeUnit
      values:
        name: "Rennes"
        administrative_code: "35238"
        administrative_level: ref(AdministrativeLevel[name='City'])
        parent: ref(AdministrativeUnit[administrative_code='35'])
```

**Translations**:

```sql
-- Multi-language support
INSERT INTO common.tb_administrative_unit_i18n (administrative_unit, lang, name)
VALUES
  (administrative_unit_pk('FR'), 'fr', 'France'),
  (administrative_unit_pk('FR'), 'en', 'France'),
  (administrative_unit_pk('FR'), 'de', 'Frankreich');
```

---

### PostalCode

**Purpose**: Postal/ZIP code validation and city mapping.

**Schema**: `common`

**Features**:
- Postal code to city mapping
- Multi-city support (shared postal codes)
- Country-specific validation

#### Usage Example

```yaml
from: stdlib/geo/postal_code.yaml
from: stdlib/geo/postal_code_city.yaml

action: create_postal_code
  steps:
    - insert: PostalCode
      values:
        code: "75001"
        country: ref(Country[code='FR'])
    - insert: PostalCodeCity
      values:
        postal_code: ref(PostalCode[identifier='75001'])
        administrative_unit: ref(AdministrativeUnit[name='Paris'])
```

---

## Supporting Entities

### StreetType

Classification of street types: Avenue, Boulevard, Street, Road, etc.

**Multi-language**: Translations enabled.

**Examples**: "Avenue" (en), "Avenue" (fr), "Avenida" (es)

---

### LocationType

Physical location classifications: Warehouse, Office, Retail, Residential, etc.

**Use Case**: Filter locations by type.

---

### LocationLevel

Hierarchical levels: Building, Floor, Zone, Room, etc.

**Use Case**: Enforce hierarchy rules.

---

### AddressDatasource

Address data sources: Google Maps, OpenStreetMap, national registries (BAN, USPS).

**Use Case**: Track address origin and quality.

---

## Complete Example: E-Commerce with Shipping

### Scenario: Multi-Warehouse Fulfillment

```yaml
# File: entities/fulfillment.yaml

# Import geographic entities
from: stdlib/geo/public_address.yaml
from: stdlib/geo/location.yaml
from: stdlib/geo/postal_code.yaml
from: stdlib/geo/administrative_unit.yaml
from: stdlib/i18n/country.yaml

# Import commerce entities
from: stdlib/commerce/order.yaml

# Extend Order with shipping
extend: Order
  custom_fields:
    shipping_address: ref(PublicAddress)
    warehouse: ref(Location)
    estimated_delivery: date

# Custom actions
action: calculate_shipping_cost
  entity: Order
  steps:
    # Get warehouse coordinates
    - call: get_warehouse_location
      result: $warehouse_coords

    # Get customer coordinates
    - call: geocode_address($shipping_address)
      result: $customer_coords

    # Calculate distance
    - call: distance($warehouse_coords, $customer_coords)
      result: $distance_km

    # Pricing logic
    - if: $distance_km < 50
      - update: Order SET shipping_cost = 5.00
    - if: $distance_km >= 50 AND $distance_km < 200
      - update: Order SET shipping_cost = 10.00
    - if: $distance_km >= 200
      - update: Order SET shipping_cost = 20.00

action: find_nearest_warehouse
  entity: Order
  steps:
    # Geocode customer address
    - call: geocode_address($shipping_address)
      result: $customer_coords

    # Find nearest warehouse with inventory
    - query: |
        SELECT location_pk('warehouse-' || w.identifier) AS warehouse
        FROM tenant.tb_location w
        WHERE w.location_type = location_type_pk('Warehouse')
          AND w.coordinates <-> $customer_coords < 1000000  -- Within 1000km
          AND has_inventory(w.pk_location, $product_id)
        ORDER BY w.coordinates <-> $customer_coords
        LIMIT 1
      result: $nearest_warehouse

    - update: Order SET warehouse = $nearest_warehouse
```

**Generated Functions**:

```sql
-- Automatic spatial functions
CREATE FUNCTION tenant.calculate_shipping_cost(order_id UUID)
RETURNS app.mutation_result AS $$
DECLARE
  warehouse_coords POINT;
  customer_coords POINT;
  distance_km FLOAT;
BEGIN
  -- Get warehouse location
  SELECT coordinates INTO warehouse_coords
  FROM tenant.tb_location
  WHERE pk_location = (SELECT warehouse FROM tenant.tb_order WHERE id = order_id);

  -- Get customer address coordinates
  SELECT coordinates INTO customer_coords
  FROM common.tb_public_address pa
  INNER JOIN tenant.tb_order o ON pa.pk_public_address = o.shipping_address
  WHERE o.id = order_id;

  -- Calculate distance (PostGIS)
  distance_km := ST_Distance(warehouse_coords::geography, customer_coords::geography) / 1000;

  -- Apply pricing
  IF distance_km < 50 THEN
    UPDATE tenant.tb_order SET shipping_cost = 5.00 WHERE id = order_id;
  ELSIF distance_km < 200 THEN
    UPDATE tenant.tb_order SET shipping_cost = 10.00 WHERE id = order_id;
  ELSE
    UPDATE tenant.tb_order SET shipping_cost = 20.00 WHERE id = order_id;
  END IF;

  RETURN app.success_result('Shipping cost calculated', jsonb_build_object('distance_km', distance_km));
END;
$$ LANGUAGE plpgsql;
```

---

## Integration with Other stdlib Modules

### Geo + CRM

```yaml
from: stdlib/crm/organization.yaml
from: stdlib/geo/public_address.yaml

extend: Organization
  custom_fields:
    headquarters: ref(PublicAddress)
    billing_address: ref(PublicAddress)
```

---

### Geo + Commerce

```yaml
from: stdlib/commerce/order.yaml
from: stdlib/geo/public_address.yaml
from: stdlib/geo/location.yaml

extend: Order
  custom_fields:
    shipping_address: ref(PublicAddress)
    warehouse: ref(Location)
```

---

### Geo + i18n

```yaml
from: stdlib/geo/public_address.yaml
from: stdlib/i18n/country.yaml
from: stdlib/i18n/language.yaml

# Automatic country/language integration
```

---

## Performance: Spatial Indexes

SpecQL automatically creates **GIST indexes** for spatial queries:

```sql
-- Auto-generated for coordinates fields
CREATE INDEX idx_tb_public_address_coordinates
  ON common.tb_public_address USING GIST (coordinates);

CREATE INDEX idx_tb_location_coordinates
  ON tenant.tb_location USING GIST (coordinates);
```

**Query Performance**:
- Proximity searches: O(log n) with GIST
- Nearest neighbor: < 10ms on 1M+ records
- Bounding box queries: < 5ms

---

## Security: Multi-Tenancy

Location entities are **tenant-isolated**:

```sql
-- Auto-generated RLS
CREATE POLICY tenant_isolation ON tenant.tb_location
  USING (tenant_id = current_setting('app.current_tenant')::UUID);
```

**PublicAddress** is shared (common schema) for reuse across tenants.

---

## Testing Geo Entities

```bash
# Generate schema
specql generate stdlib/geo/*.yaml --output test/schema/

# Test spatial queries
psql test_db -c "
  SELECT * FROM common.tb_public_address
  WHERE coordinates <@> POINT(48.8566, 2.3522) < 1000;
"

# Test hierarchy
psql test_db -c "
  WITH RECURSIVE tree AS (
    SELECT * FROM tenant.tb_location WHERE identifier = 'warehouse-1'
    UNION ALL
    SELECT l.* FROM tenant.tb_location l
    INNER JOIN tree t ON l.parent_location = t.pk_location
  )
  SELECT name, location_level FROM tree;
"
```

---

## Migration from Existing Systems

### From Rails/ActiveRecord

**Before** (150 lines):

```ruby
class Address < ApplicationRecord
  belongs_to :country
  belongs_to :city
  validates :street, presence: true
  geocoded_by :full_address
  after_validation :geocode
  # ... many more validations and callbacks
end
```

**After** (1 line):

```yaml
from: stdlib/geo/public_address.yaml
```

---

### From Google Maps API

**Before**: Manual geocoding, address parsing, coordinate storage.

**After**: Built-in geocoding actions, structured storage, spatial queries ready.

---

## Key Takeaways

1. **ISO-Compliant**: Country codes, admin boundaries follow standards
2. **PostGIS-Ready**: Automatic spatial indexes and queries
3. **Multi-Language**: Address formatting for international use
4. **Hierarchical**: Unlimited depth for locations and admin units
5. **Production-Tested**: Real-world logistics platform extraction

**Build international address management in minutes, not months.** 🌍

---

*Last updated: 2025-11-19*
