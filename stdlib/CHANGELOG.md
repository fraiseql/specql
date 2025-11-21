# Changelog

All notable changes to the SpecQL standard library will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-11-09

### Changed (BREAKING)
- **PublicAddress**: Replaced `latitude`/`longitude` fields with `coordinates` rich type (PostgreSQL POINT)
- **Contact**: Updated `email` field to use `email` rich type with validation
- **Contact**: Updated `phone`/`mobile_phone` fields to use `phone` rich type (E.164 format)
- **Price**: Updated `amount` field to use `money` rich type

### Migration Guide

#### PublicAddress
```sql
-- Migrate existing data
ALTER TABLE common.tb_public_address ADD COLUMN coordinates POINT;
UPDATE common.tb_public_address
  SET coordinates = POINT(longitude, latitude);
ALTER TABLE common.tb_public_address
  DROP COLUMN latitude,
  DROP COLUMN longitude;

-- Add spatial index
CREATE INDEX idx_tb_public_address_coordinates
  ON common.tb_public_address USING GIST (coordinates);
```

#### Contact
```sql
-- Email and phone fields now have validation constraints
-- Existing data must conform to formats
```

## [1.0.0] - 2025-11-09

### Added
- Initial release of SpecQL standard library
- **i18n**: 6 entities (Country, Currency, Language, Locale, Continent, CountryLocale)
- **geo**: 11 entities (AdministrativeLevel, AdministrativeUnit, PostalCode, PostalCodeCity, PublicAddress, StreetType, AddressFormat, AddressDatasource, LocationLevel, LocationType, Location)
- **crm**: 3 entities (Organization, OrganizationType, Contact)
- **org**: 2 entities (OrganizationalUnit, OrganizationalUnitLevel)
- **commerce**: 3 entities (Contract, Order, Price)
- **tech**: 2 entities (OperatingSystem, OperatingSystemPlatform)
- **time**: 1 entity (Calendar)
- **common**: 5 entities (Genre, Industry, Continent)

Total: 33 entities in stdlib v1.0.0
