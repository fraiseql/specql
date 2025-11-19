# Geographic Entities: Location & Address Management

> **Production-proven geographic data models with international support**

## Overview

The SpecQL stdlib **geographic (geo) module** provides comprehensive address and location management with support for:
- **International addresses** with postal codes and administrative boundaries
- **Hierarchical locations** (country → state → city → district → building → floor)
- **Geocoding** with PostGIS POINT type integration
- **Address validation** and formatting
- **Multi-source address data** (national address databases, user-entered, external APIs)

These entities are extracted from production systems handling international e-commerce and logistics.

## Quick Start

```yaml
# Import pre-built geographic entities
import:
  - stdlib/geo/public_address
  - stdlib/geo/location
  - stdlib/geo/postal_code
  - stdlib/i18n/country

# Use them in your entities
entity: Store
fields:
  name: text
  address: ref(PublicAddress)  # Ready to use!
  delivery_zone: ref(Location)
```

**Result**: Instant international address support with zero configuration.

---

## Core Entities

### 1. PublicAddress

**Purpose**: Geolocated public addresses with postal and administrative references

**Schema**: `common` (shared across tenants)

**Use Cases**:
- E-commerce shipping addresses
- Store/office locations
- Customer contact addresses
- Delivery points

#### Fields

```yaml
entity: PublicAddress
fields:
  # Street components
  street_number: text              # "1600"
  street_name: text                # "Pennsylvania Avenue"
  street_suffix: text              # "NW"

  # Geographic data
  coordinates:
    type: coordinates
    nullable: true
    description: "PostgreSQL POINT (latitude, longitude)"

  # External identifiers
  national_address_id: text        # Government database ID
  external_address_id: text        # Third-party API reference

  # References
  street_type: ref(StreetType)              # Avenue, Street, Road, etc.
  country: ref(Country)                     # ISO 3166 country
  administrative_unit: ref(AdministrativeUnit)  # State, province, region
  postal_code: ref(PostalCode)              # ZIP/postal code
  address_datasource: ref(AddressDatasource)  # Source of address data
```

#### Built-in Actions

```yaml
actions:
  # CRUD
  - create_public_address
  - update_public_address
  - delete_public_address

  # Business logic
  - validate_address        # Check completeness and accuracy
  - geocode_address        # Convert to coordinates
  - format_address         # Format for display (country-specific)
  - check_address_completeness  # Verify all required fields
```

#### Example: Creating a Store Address

```yaml
# Use stdlib PublicAddress directly
import:
  - stdlib/geo/public_address

entity: Store
fields:
  name: text
  address: ref(PublicAddress)

# Generate SQL - PublicAddress is automatically available!
```

**Generated Actions**:
```sql
-- Automatically generated from PublicAddress entity
CREATE FUNCTION common.validate_address(
  p_address_id UUID
) RETURNS app.mutation_result;

CREATE FUNCTION common.geocode_address(
  p_address_id UUID
) RETURNS app.mutation_result;
```

#### Extending PublicAddress

```yaml
# Add custom fields to stdlib entity
entity: DeliveryAddress
extends:
  from: stdlib/geo/public_address
fields:
  delivery_instructions: text
  safe_drop_location: text
  access_code: text
  preferred_delivery_time: time
```

**Result**: All PublicAddress functionality + your custom fields.

---

### 2. Location

**Purpose**: Hierarchical physical locations with accessibility and dimensional data

**Schema**: `tenant` (tenant-specific)

**Use Cases**:
- Warehouse zones and aisles
- Building floors and rooms
- Equipment installation sites
- Retail store sections

#### Key Features

✅ **Hierarchical**: Self-referencing `parent_location` for nested structures
✅ **Accessibility**: Elevator/stairs tracking for logistics
✅ **Dimensional**: Width/depth/height constraints for space planning
✅ **Geocoded**: Coordinates for each location level

#### Fields

```yaml
entity: Location
hierarchical: true  # Enables parent-child relationships
fields:
  # Basic info
  name: text                  # "3rd floor, west wing"
  int_ordered: integer        # Sort order among siblings

  # Accessibility
  has_elevator: boolean
  has_stairs: boolean
  n_stair_steps: integer      # For accessibility planning

  # Physical dimensions (millimeters)
  available_width_mm: integer
  available_depth_mm: integer
  available_height_mm: integer

  # Geographic
  coordinates:
    type: coordinates
    nullable: true

  # Relationships
  customer_org: ref(Organization)       # Owner/tenant
  public_address: ref(PublicAddress)    # Physical address
  location_type: ref(LocationType)      # Building, floor, room, etc.
  location_level: ref(LocationLevel)    # Hierarchy level
  parent_location: ref(Location)        # Self-reference for nesting
```

#### Built-in Actions

```yaml
actions:
  # CRUD
  - create_location
  - update_location
  - delete_location

  # Accessibility management
  - update_accessibility
  - change_elevator_access
  - change_stair_access

  # Physical properties
  - update_dimensions
  - update_coordinates

  # Relationships
  - change_address
  - change_location_type
  - move_to_parent  # Reorganize hierarchy
```

#### Example: Warehouse Location Hierarchy

```yaml
import:
  - stdlib/geo/location

# Warehouse structure:
# Warehouse (parent: null)
#   └─ Zone A (parent: Warehouse)
#       ├─ Aisle 1 (parent: Zone A)
#       │   ├─ Shelf 1A (parent: Aisle 1)
#       │   └─ Shelf 1B (parent: Aisle 1)
#       └─ Aisle 2 (parent: Zone A)

# Create root location
action: create_location
inputs:
  name: "Warehouse North"
  parent_location: null  # Top level
  has_elevator: true
  available_height_mm: 8000

# Create nested zone
action: create_location
inputs:
  name: "Zone A"
  parent_location: {identifier: "warehouse-north"}
  has_elevator: true
  available_height_mm: 7500
```

**Generated SQL**:
```sql
-- Automatically includes hierarchical queries
CREATE FUNCTION tenant.move_to_parent(
  p_location_id UUID,
  p_new_parent_id UUID
) RETURNS app.mutation_result;

-- PostgreSQL ltree or materialized path for hierarchy
-- (Auto-generated based on hierarchical: true)
```

---

### 3. PostalCode

**Purpose**: Postal code database with city mapping

**Schema**: `common` (shared reference data)

**Use Cases**:
- Address validation
- Auto-complete city names from postal codes
- Delivery zone mapping
- Shipping cost calculation

#### Fields

```yaml
entity: PostalCode
fields:
  code: text              # "94043", "75001", "SW1A 1AA"
  city_name: text         # Auto-populated from postal database

  # References
  country: ref(Country)
  administrative_unit: ref(AdministrativeUnit)  # State/province
```

#### Example: Auto-Complete City from ZIP

```yaml
import:
  - stdlib/geo/postal_code

# User enters ZIP code
action: lookup_postal_code
inputs:
  code: "94043"
  country_iso: "US"

# Returns:
# {
#   "code": "94043",
#   "city_name": "Mountain View",
#   "administrative_unit": "California"
# }
```

---

### 4. AdministrativeUnit

**Purpose**: Governmental/administrative boundaries (states, provinces, regions)

**Schema**: `common` (shared reference data)

**Use Cases**:
- Tax calculation by jurisdiction
- Regulatory compliance (shipping restrictions)
- Statistical reporting
- Address validation

#### Fields

```yaml
entity: AdministrativeUnit
hierarchical: true  # State → County → Municipality
fields:
  name: text
  abbreviation: text  # "CA", "TX", "ON"

  # References
  country: ref(Country)
  administrative_level: ref(AdministrativeLevel)  # Level 1, 2, 3, etc.
  parent_unit: ref(AdministrativeUnit)  # For nested hierarchies
```

#### Example: US State Tax Jurisdiction

```yaml
import:
  - stdlib/geo/administrative_unit

# Use for tax calculation
entity: SalesTax
fields:
  rate: decimal
  jurisdiction: ref(AdministrativeUnit)  # California, Texas, etc.

action: calculate_sales_tax
inputs:
  amount: money
  delivery_address: ref(PublicAddress)
steps:
  - query: |
      SELECT rate FROM SalesTax
      WHERE jurisdiction = (
        SELECT administrative_unit FROM PublicAddress
        WHERE id = :delivery_address
      )
```

---

## Supporting Entities

### StreetType

Classification of street types (Avenue, Boulevard, Road, etc.)

```yaml
entity: StreetType
fields:
  name: text           # "Avenue", "Boulevard", "Street"
  abbreviation: text   # "Ave", "Blvd", "St"
  country: ref(Country)  # Street types vary by country
```

**Example**:
- US: Avenue, Boulevard, Court, Drive, Lane, Road, Street
- France: Rue, Avenue, Boulevard, Place, Impasse
- Germany: Straße, Allee, Platz, Weg

### LocationType

Classification of location types

```yaml
entity: LocationType
fields:
  name: text  # Building, Floor, Room, Zone, Aisle, Shelf, etc.
  level: integer  # Hierarchy level
```

### LocationLevel

Hierarchy levels for nested locations

```yaml
entity: LocationLevel
fields:
  name: text  # Country, State, City, District, Building, Floor, Room
  depth: integer  # 0 = country, 1 = state, 2 = city, etc.
```

### AddressDatasource

Source of address data for audit and trust

```yaml
entity: AddressDatasource
fields:
  name: text  # "National Address Database", "Google Maps API", "User Entered"
  trust_level: enum(verified, unverified, user_provided)
```

**Use Case**: Track address reliability for delivery planning.

---

## Complete Import Example

```yaml
# Import all geographic entities
import:
  - stdlib/geo/public_address
  - stdlib/geo/location
  - stdlib/geo/postal_code
  - stdlib/geo/administrative_unit
  - stdlib/geo/street_type
  - stdlib/geo/location_type
  - stdlib/geo/address_datasource
  - stdlib/i18n/country  # ISO 3166 countries

# Now build your app entities
entity: DeliveryOrder
fields:
  order_number: text
  pickup_address: ref(PublicAddress)
  delivery_address: ref(PublicAddress)
  warehouse_location: ref(Location)
  estimated_delivery_zone: ref(AdministrativeUnit)

actions:
  - name: create_delivery_order
    steps:
      - validate: pickup_address IS NOT NULL
      - validate: delivery_address IS NOT NULL
      - call: common.validate_address(pickup_address)
      - call: common.validate_address(delivery_address)
      - insert: DeliveryOrder
```

**Generated Code**: 2000+ lines of PostgreSQL with:
- Address validation functions
- Geocoding utilities
- Hierarchy traversal queries
- Foreign key constraints
- Indexes on coordinates (GiST for spatial queries)

---

## Database Schema Details

### Generated Tables

```sql
-- PublicAddress table
CREATE TABLE common.tb_public_address (
  pk_public_address INTEGER PRIMARY KEY,
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  identifier TEXT NOT NULL,

  street_number TEXT,
  street_name TEXT,
  street_suffix TEXT,
  coordinates POINT,  -- PostGIS type for spatial queries
  national_address_id TEXT,
  external_address_id TEXT,

  -- Foreign keys (auto-generated)
  fk_street_type INTEGER REFERENCES common.tb_street_type(pk_street_type),
  fk_country INTEGER REFERENCES common.tb_country(pk_country),
  fk_administrative_unit INTEGER REFERENCES common.tb_administrative_unit(pk_administrative_unit),
  fk_postal_code INTEGER REFERENCES common.tb_postal_code(pk_postal_code),
  fk_address_datasource INTEGER REFERENCES common.tb_address_datasource(pk_address_datasource),

  -- Audit fields (auto-generated)
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ,
  deleted_at TIMESTAMPTZ,
  created_by UUID,
  updated_by UUID
);

-- Spatial index for coordinates (auto-generated)
CREATE INDEX idx_tb_public_address_coordinates
  ON common.tb_public_address
  USING GIST (coordinates);

-- Location table (hierarchical)
CREATE TABLE tenant.tb_location (
  pk_location INTEGER PRIMARY KEY,
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  identifier TEXT NOT NULL,

  name TEXT NOT NULL,
  int_ordered INTEGER,

  has_elevator BOOLEAN,
  has_stairs BOOLEAN,
  n_stair_steps INTEGER,

  available_width_mm INTEGER,
  available_depth_mm INTEGER,
  available_height_mm INTEGER,

  coordinates POINT,

  -- Foreign keys
  fk_customer_org INTEGER NOT NULL,
  fk_public_address INTEGER NOT NULL,
  fk_location_type INTEGER NOT NULL,
  fk_location_level INTEGER NOT NULL,
  fk_parent_location INTEGER REFERENCES tenant.tb_location(pk_location),  -- Self-reference!

  tenant_id UUID NOT NULL,  -- Multi-tenancy

  -- Audit fields
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ,
  deleted_at TIMESTAMPTZ
);

-- Hierarchy traversal helper (auto-generated)
CREATE FUNCTION tenant.location_ancestors(p_location_id UUID)
RETURNS TABLE(ancestor_id UUID, depth INTEGER)
AS $$
  WITH RECURSIVE ancestors AS (
    SELECT id, 0 AS depth FROM tenant.tb_location WHERE id = p_location_id
    UNION ALL
    SELECT l.id, a.depth + 1
    FROM tenant.tb_location l
    JOIN ancestors a ON l.pk_location = (
      SELECT fk_parent_location FROM tenant.tb_location WHERE id = a.id
    )
  )
  SELECT id, depth FROM ancestors;
$$ LANGUAGE SQL;
```

### Generated Indexes

SpecQL automatically creates indexes for:
- Foreign key columns (`fk_*`)
- Coordinates (GiST spatial index)
- Postal codes (for lookup performance)
- Hierarchical parent references
- Tenant ID (for multi-tenant isolation)

---

## Integration Patterns

### Pattern 1: E-Commerce Shipping

```yaml
import:
  - stdlib/geo/public_address
  - stdlib/geo/postal_code
  - stdlib/geo/administrative_unit
  - stdlib/i18n/country

entity: Order
fields:
  order_number: text
  shipping_address: ref(PublicAddress)
  billing_address: ref(PublicAddress)

actions:
  - name: calculate_shipping_cost
    inputs:
      order_id: uuid
    steps:
      - query: |
          SELECT
            pa.coordinates,
            au.name AS state,
            c.iso_code AS country
          FROM PublicAddress pa
          JOIN AdministrativeUnit au ON pa.administrative_unit = au.id
          JOIN Country c ON pa.country = c.id
          WHERE pa.id = (SELECT shipping_address FROM Order WHERE id = :order_id)
      - # Calculate distance-based shipping
```

### Pattern 2: Warehouse Location Management

```yaml
import:
  - stdlib/geo/location

entity: Inventory
fields:
  product_sku: text
  quantity: integer
  storage_location: ref(Location)  # Warehouse → Zone → Aisle → Shelf

actions:
  - name: find_product_location
    inputs:
      sku: text
    returns:
      - location_path: text  # "Warehouse A → Zone 2 → Aisle 5 → Shelf C"
      - accessibility: object  # {has_elevator: true, stairs: 0}
```

### Pattern 3: Service Area Coverage

```yaml
import:
  - stdlib/geo/administrative_unit
  - stdlib/geo/postal_code

entity: ServiceArea
fields:
  name: text
  covered_units: list(ref(AdministrativeUnit))
  covered_postal_codes: list(ref(PostalCode))

action: check_service_availability
inputs:
  delivery_address: ref(PublicAddress)
returns:
  available: boolean
  estimated_delivery_days: integer
```

---

## Best Practices

### ✅ DO

1. **Import what you need**: Only import entities you actually use
   ```yaml
   # Good: Specific imports
   import:
     - stdlib/geo/public_address
     - stdlib/geo/postal_code
   ```

2. **Extend for customization**: Add custom fields via `extends`
   ```yaml
   entity: RestaurantLocation
   extends:
     from: stdlib/geo/location
   fields:
     seating_capacity: integer
     outdoor_seating: boolean
   ```

3. **Use coordinates for spatial queries**: Leverage PostGIS
   ```sql
   -- Find addresses within 10km radius
   SELECT * FROM PublicAddress
   WHERE coordinates <-> point(:lat, :lon) < 10000;  -- meters
   ```

4. **Validate addresses before use**: Use built-in actions
   ```yaml
   action: create_order
   steps:
     - call: common.validate_address(:shipping_address)
     - insert: Order
   ```

### ❌ DON'T

1. **Don't reinvent address models**: Use stdlib instead
   ```yaml
   # ❌ Bad: Recreating address fields
   entity: MyAddress
   fields:
     street: text
     city: text
     zip: text

   # ✅ Good: Use stdlib
   import: stdlib/geo/public_address
   ```

2. **Don't skip geocoding**: Coordinates enable advanced features
   ```yaml
   # ❌ Bad: No coordinates
   entity: Store
   fields:
     address_text: text

   # ✅ Good: Use PublicAddress with coordinates
   fields:
     address: ref(PublicAddress)  # Includes coordinates field
   ```

3. **Don't ignore hierarchy**: Use parent-child relationships
   ```yaml
   # ❌ Bad: Flat location structure
   entity: WarehouseZone
   fields:
     zone_name: text

   # ✅ Good: Hierarchical locations
   import: stdlib/geo/location  # Built-in hierarchy
   ```

---

## Performance Considerations

### Spatial Indexes

SpecQL automatically creates GiST indexes on `coordinates` fields:

```sql
-- Auto-generated for PublicAddress.coordinates
CREATE INDEX idx_tb_public_address_coordinates
  ON common.tb_public_address
  USING GIST (coordinates);
```

**Query Performance**:
- Radius searches: O(log n) with GiST index
- Nearest neighbor: O(log n)
- Without index: O(n) - full table scan

### Hierarchy Queries

For deep location hierarchies (>5 levels), consider:

1. **Materialized Path**: Store full path as text
   ```sql
   -- Example: "/warehouse/zone-a/aisle-1/shelf-c"
   path TEXT NOT NULL
   ```

2. **Closure Table**: Pre-compute all ancestor-descendant pairs
   ```sql
   CREATE TABLE location_closure (
     ancestor_id UUID,
     descendant_id UUID,
     depth INTEGER
   );
   ```

SpecQL generates optimized hierarchy queries automatically based on tree depth.

---

## Migration from Legacy Systems

### From Flat Address Tables

**Before** (legacy SQL):
```sql
CREATE TABLE addresses (
  id SERIAL PRIMARY KEY,
  street TEXT,
  city TEXT,
  state TEXT,
  zip TEXT,
  country TEXT
);
```

**After** (SpecQL):
```yaml
import:
  - stdlib/geo/public_address
  - stdlib/geo/postal_code
  - stdlib/geo/administrative_unit
  - stdlib/i18n/country

# Automatic normalization:
# - PostalCode table (shared reference)
# - AdministrativeUnit table (shared reference)
# - Country table (ISO standard)
# - PublicAddress table (foreign keys to all above)
```

**Benefits**:
- ✅ No duplicate city/state/country data
- ✅ Enforced referential integrity
- ✅ Geocoding support
- ✅ International address formats

### Migration Script

```sql
-- Map legacy addresses to stdlib entities
INSERT INTO common.tb_country (name, iso_code)
SELECT DISTINCT country, country_iso FROM legacy.addresses;

INSERT INTO common.tb_postal_code (code, city_name, fk_country)
SELECT DISTINCT zip, city, c.pk_country
FROM legacy.addresses la
JOIN common.tb_country c ON la.country_iso = c.iso_code;

INSERT INTO common.tb_public_address (street_name, fk_postal_code, fk_country)
SELECT la.street, pc.pk_postal_code, c.pk_country
FROM legacy.addresses la
JOIN common.tb_postal_code pc ON la.zip = pc.code
JOIN common.tb_country c ON la.country_iso = c.iso_code;
```

---

## Reference

### Complete Entity List

| Entity | Schema | Hierarchical | Key Features |
|--------|--------|--------------|--------------|
| **PublicAddress** | common | No | Geocoded addresses, postal codes |
| **Location** | tenant | Yes | Physical locations, dimensions |
| **PostalCode** | common | No | ZIP/postal code database |
| **AdministrativeUnit** | common | Yes | States, provinces, regions |
| **StreetType** | common | No | Avenue, Boulevard, etc. |
| **LocationType** | common | No | Building, Floor, Room, etc. |
| **LocationLevel** | common | No | Hierarchy depth classification |
| **AddressDatasource** | common | No | Address data provenance |

### Coordinate System

SpecQL uses **PostgreSQL POINT type** with **WGS 84** coordinate system:
- Latitude: -90 to +90 (decimal degrees)
- Longitude: -180 to +180 (decimal degrees)
- Format: `(longitude, latitude)` ⚠️ Note: PostgreSQL uses (x, y) = (lon, lat)

**Example**:
```sql
-- Store coordinates
UPDATE common.tb_public_address
SET coordinates = POINT(-122.0841, 37.4220)  -- (longitude, latitude)
WHERE identifier = 'googleplex';

-- Distance query (meters)
SELECT identifier,
       coordinates <-> POINT(-122.0, 37.4) AS distance_meters
FROM common.tb_public_address
WHERE coordinates <-> POINT(-122.0, 37.4) < 5000  -- Within 5km
ORDER BY distance_meters;
```

### Related Documentation

- [CRM Entities](../crm/index.md) - Organization and Contact (both use PublicAddress)
- [i18n Entities](../i18n/index.md) - Country, Locale, Currency
- [Commerce Entities](../commerce/index.md) - Contract, Order, Price
- [Rich Types Reference](../../06_reference/rich-types-reference.md) - coordinates type details
- [Multi-Tenancy Guide](../../05_guides/multi-tenancy.md) - Location tenant isolation

---

## Next Steps

1. **Try it**: Import geographic entities in your project
2. **Extend it**: Add custom fields for your use case
3. **Deploy it**: Generate PostgreSQL schema with geocoding support
4. **Optimize it**: Add spatial indexes for performance

**Ready to build international address management? Import and go!** 🌍
