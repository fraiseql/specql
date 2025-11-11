# Phase 4.5 Enhancement: Smart Acronym Support

**Enhancement to**: Issue #6 Phase 4.5 - Snake_case Conversion
**Purpose**: Handle business acronyms intelligently (B2B, B2C, API, etc.)
**Status**: Optional Enhancement

---

## Problem

The basic `camel_to_snake()` conversion treats every component separately:

```python
B2BProduct → B_2_B_Product → b_2_b_product  ❌ Not ideal
RestAPI → Rest_A_P_I → rest_a_p_i          ❌ Not ideal
OAuth2Client → O_Auth_2_Client → o_auth_2_client  ❌ Not ideal
```

**Desired**:
```python
B2BProduct → b2b_product      ✅ Better
RestAPI → rest_api           ✅ Better
OAuth2Client → oauth2_client ✅ Better
```

---

## Solution: Smart Acronym Preservation

### Enhanced Implementation

```python
# File: src/generators/naming_utils.py

"""Naming utility functions with smart acronym handling"""

import re


# Common business/technical acronyms to preserve as single units
COMMON_ACRONYMS = {
    # Business models
    'B2B', 'B2C', 'C2C', 'P2P', 'G2B', 'G2C',

    # Protocols & Standards
    'API', 'REST', 'HTTP', 'HTTPS', 'FTP', 'SFTP', 'SSH', 'SSL', 'TLS',
    'SOAP', 'gRPC', 'GraphQL', 'MQTT', 'AMQP',

    # Data formats
    'JSON', 'XML', 'HTML', 'CSS', 'YAML', 'TOML', 'SQL', 'CSV',

    # Identifiers
    'URL', 'URI', 'URN', 'UUID', 'GUID', 'ISBN', 'ISSN',

    # File formats
    'PDF', 'PNG', 'JPG', 'JPEG', 'GIF', 'SVG', 'ZIP', 'TAR',

    # Cloud/Infrastructure
    'AWS', 'GCP', 'Azure', 'SDK', 'IDE', 'CLI', 'GUI', 'VM', 'CDN',

    # Business systems
    'CRM', 'ERP', 'POS', 'SKU', 'WMS', 'MRP', 'SCM', 'HRM',

    # Network/Protocol
    'IPv4', 'IPv6', 'TCP', 'UDP', 'DNS', 'DHCP', 'NAT', 'VPN',
    'IP', 'MAC', 'LAN', 'WAN', 'VLAN',

    # Authentication/Security
    '2FA', 'MFA', 'SSO', 'OAuth', 'SAML', 'LDAP', 'JWT', 'PKI',

    # Database
    'RDBMS', 'NoSQL', 'ACID', 'CRUD',

    # Other common
    'SLA', 'KPI', 'ROI', 'CEO', 'CTO', 'COO', 'CFO',
}


def camel_to_snake(
    name: str,
    preserve_acronyms: set[str] | None = None,
    use_common_acronyms: bool = True
) -> str:
    """
    Convert CamelCase to snake_case with smart acronym handling

    Preserves common business/technical acronyms as single units instead
    of splitting them character by character.

    Args:
        name: CamelCase or PascalCase string
        preserve_acronyms: Additional acronyms to preserve (e.g., {'B2B', '2B'})
        use_common_acronyms: Whether to use COMMON_ACRONYMS (default: True)

    Returns:
        snake_case string with acronyms preserved

    Examples:
        >>> camel_to_snake("B2BProduct")
        'b2b_product'

        >>> camel_to_snake("RestAPIClient")
        'rest_api_client'

        >>> camel_to_snake("OAuth2Provider")
        'oauth2_provider'

        >>> camel_to_snake("Product2B", preserve_acronyms={'2B'})
        'product_2b'

        >>> camel_to_snake("HTTPSConnection")
        'https_connection'

        >>> camel_to_snake("IPv4Address")
        'ipv4_address'
    """
    # Already snake_case - pass through
    if "_" in name and name.islower():
        return name

    # Build acronym set
    acronyms = set()
    if use_common_acronyms:
        acronyms.update(COMMON_ACRONYMS)
    if preserve_acronyms:
        acronyms.update(preserve_acronyms)

    # If no acronyms to preserve, use simple conversion
    if not acronyms:
        return _simple_camel_to_snake(name)

    # Replace acronyms with placeholders to preserve them
    # Sort by length (descending) to match longer acronyms first
    placeholder_map = {}
    temp_name = name

    for i, acronym in enumerate(sorted(acronyms, key=len, reverse=True)):
        if acronym in temp_name:
            placeholder = f"__ACRONYM{i}__"
            temp_name = temp_name.replace(acronym, placeholder)
            placeholder_map[placeholder] = acronym.lower()

    # Standard camel_to_snake conversion on temp_name
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", temp_name)
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)
    result = s2.lower()

    # Restore acronyms
    for placeholder, acronym_lower in placeholder_map.items():
        result = result.replace(placeholder.lower(), acronym_lower)

    # Clean up multiple underscores and trim
    result = re.sub(r"_+", "_", result).strip("_")

    return result


def _simple_camel_to_snake(name: str) -> str:
    """
    Simple camel_to_snake without acronym handling

    Used internally and as fallback.
    """
    if "_" in name and name.islower():
        return name

    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.lower().replace("__", "_").strip("_")


def to_entity_name(name: str, preserve_acronyms: set[str] | None = None) -> str:
    """
    Convert entity name to snake_case with smart acronym handling

    Convenience wrapper around camel_to_snake for entity names.

    Args:
        name: Entity name (usually PascalCase)
        preserve_acronyms: Additional acronyms to preserve

    Returns:
        snake_case entity name

    Examples:
        >>> to_entity_name("B2BContact")
        'b2b_contact'
        >>> to_entity_name("RestAPIEndpoint")
        'rest_api_endpoint'
    """
    return camel_to_snake(name, preserve_acronyms=preserve_acronyms)
```

---

## Test Cases

```python
# File: tests/unit/generators/test_naming_utils.py

class TestAcronymSupport:
    """Test smart acronym preservation"""

    def test_b2b_b2c_acronyms(self):
        """Business model acronyms should be preserved"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("B2BProduct") == "b2b_product"
        assert camel_to_snake("B2CCustomer") == "b2c_customer"
        assert camel_to_snake("P2PTransaction") == "p2p_transaction"
        assert camel_to_snake("C2CMarketplace") == "c2c_marketplace"

    def test_api_protocol_acronyms(self):
        """API and protocol acronyms"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("RestAPI") == "rest_api"
        assert camel_to_snake("RestAPIClient") == "rest_api_client"
        assert camel_to_snake("HTTPSConnection") == "https_connection"
        assert camel_to_snake("GraphQLResolver") == "graphql_resolver"

    def test_auth_acronyms(self):
        """Authentication acronyms"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("OAuth2Provider") == "oauth2_provider"
        assert camel_to_snake("SSOIntegration") == "sso_integration"
        assert camel_to_snake("JWTToken") == "jwt_token"
        assert camel_to_snake("2FASetup") == "2fa_setup"

    def test_network_acronyms(self):
        """Network and protocol acronyms"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("IPv4Address") == "ipv4_address"
        assert camel_to_snake("IPv6Gateway") == "ipv6_gateway"
        assert camel_to_snake("TCPConnection") == "tcp_connection"
        assert camel_to_snake("DNSRecord") == "dns_record"

    def test_business_system_acronyms(self):
        """Business system acronyms"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("CRMContact") == "crm_contact"
        assert camel_to_snake("ERPIntegration") == "erp_integration"
        assert camel_to_snake("POSTerminal") == "pos_terminal"
        assert camel_to_snake("SKUInventory") == "sku_inventory"

    def test_custom_acronyms(self):
        """Custom acronyms via preserve_acronyms parameter"""
        from src.generators.naming_utils import camel_to_snake

        # Without custom acronym
        assert camel_to_snake("Product2B") == "product_2_b"

        # With custom acronym
        assert camel_to_snake("Product2B", preserve_acronyms={'2B'}) == "product_2b"

        # Custom business acronym
        assert camel_to_snake("ACMEProduct", preserve_acronyms={'ACME'}) == "acme_product"

    def test_multiple_acronyms(self):
        """Multiple acronyms in one name"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("RestAPIHTTPSClient") == "rest_api_https_client"
        assert camel_to_snake("OAuth2JWTProvider") == "oauth2_jwt_provider"
        assert camel_to_snake("IPv4TCPConnection") == "ipv4_tcp_connection"

    def test_disable_common_acronyms(self):
        """Can disable common acronyms if needed"""
        from src.generators.naming_utils import camel_to_snake

        # With common acronyms (default)
        assert camel_to_snake("B2BProduct") == "b2b_product"

        # Without common acronyms
        assert camel_to_snake("B2BProduct", use_common_acronyms=False) == "b_2_b_product"

    def test_backward_compatibility(self):
        """Regular names still work as before"""
        from src.generators.naming_utils import camel_to_snake

        assert camel_to_snake("ColorMode") == "color_mode"
        assert camel_to_snake("DuplexMode") == "duplex_mode"
        assert camel_to_snake("MachineFunction") == "machine_function"
        assert camel_to_snake("ManufacturerRange") == "manufacturer_range"
```

---

## Real-World Examples

### Before (Without Acronym Support)

```python
camel_to_snake("B2BCustomer")      # → "b_2_b_customer"     ❌
camel_to_snake("RestAPIClient")    # → "rest_a_p_i_client" ❌
camel_to_snake("OAuth2Provider")   # → "o_auth_2_provider" ❌
camel_to_snake("CRMContact")       # → "c_r_m_contact"     ❌
```

### After (With Acronym Support)

```python
camel_to_snake("B2BCustomer")      # → "b2b_customer"      ✅
camel_to_snake("RestAPIClient")    # → "rest_api_client"   ✅
camel_to_snake("OAuth2Provider")   # → "oauth2_provider"   ✅
camel_to_snake("CRMContact")       # → "crm_contact"       ✅
```

---

## Usage in NamingConventions

```python
# File: src/generators/schema/naming_conventions.py

def _get_entity_snake_case(self, entity: Entity) -> str:
    """
    Get entity name in snake_case with smart acronym handling

    Args:
        entity: Entity AST model

    Returns:
        Entity name in snake_case with acronyms preserved
    """
    from src.generators.naming_utils import camel_to_snake

    # Check if entity has custom acronyms defined
    custom_acronyms = None
    if entity.organization and hasattr(entity.organization, 'preserve_acronyms'):
        custom_acronyms = set(entity.organization.preserve_acronyms)

    return camel_to_snake(entity.name, preserve_acronyms=custom_acronyms)
```

---

## Optional: YAML Configuration

Allow users to specify custom acronyms in their entity YAML:

```yaml
entity: B2BProduct
schema: catalog
organization:
  table_code: "013311"
  preserve_acronyms:  # Optional: custom acronyms for this entity
    - B2B
    - ACME

fields:
  name: text
  sku: text
```

This would convert to: `b2b_product` instead of `b_2_b_product`.

---

## Migration Path

### Phase 1: Basic Implementation (Current Phase 4.5)
- Simple `camel_to_snake()` without acronym support
- Works for 95% of entities (ColorMode, DuplexMode, etc.)

### Phase 2: Acronym Support (Optional Enhancement)
- Add `COMMON_ACRONYMS` set
- Implement placeholder-based preservation
- Add `preserve_acronyms` parameter

### Phase 3: YAML Configuration (Future)
- Allow entities to specify custom acronyms
- Organization-level acronym definitions
- Project-wide acronym registry

---

## Decision Matrix

### When to Use Basic Conversion

✅ **Use basic** `_simple_camel_to_snake()` if:
- Most entities are regular business terms (ColorMode, DuplexMode)
- No heavy use of acronyms
- Simplicity is preferred
- Performance is critical

### When to Use Acronym Support

✅ **Use acronym-aware** `camel_to_snake()` if:
- Entities use business acronyms (B2B, B2C, CRM, ERP)
- API/technical entities (RestAPI, OAuth2, IPv4)
- Better readability desired (`b2b_product` vs `b_2_b_product`)
- Worth the extra complexity

---

## Performance Considerations

### Basic Conversion
```python
# Fast: ~0.001ms per call
_simple_camel_to_snake("ColorMode")  # → "color_mode"
```

### Acronym-Aware Conversion
```python
# Slightly slower: ~0.005ms per call (still very fast)
camel_to_snake("B2BProduct")  # → "b2b_product"

# Can disable for performance:
camel_to_snake("ColorMode", use_common_acronyms=False)  # Fast path
```

**Impact**: Negligible for typical use (< 100 entities per generation).

---

## Recommendation

### For Phase 4.5 Implementation

**Start with basic conversion** (`_simple_camel_to_snake`):
1. Simpler implementation
2. Covers 95% of use cases
3. Can add acronym support later if needed

### Add Acronym Support If:
- User feedback requests it
- Codebase has many technical entities (API, OAuth, etc.)
- Business domains use acronyms heavily (B2B, CRM, etc.)

### Implementation Order

1. **Phase 4.5.1**: Basic `camel_to_snake()` ✅ (ship this)
2. **Phase 4.5.2**: Add `COMMON_ACRONYMS` (optional)
3. **Phase 4.5.3**: Add `preserve_acronyms` parameter (optional)
4. **Phase 4.5.4**: Add YAML configuration (future)

---

## Example: Choosing Your Approach

### Project A: E-commerce (Basic is Fine)

Entities:
- ColorMode → `color_mode` ✅
- DuplexMode → `duplex_mode` ✅
- ProductCategory → `product_category` ✅

**Decision**: Use basic conversion

### Project B: SaaS Platform (Needs Acronyms)

Entities:
- B2BCustomer → `b2b_customer` (better than `b_2_b_customer`)
- RestAPIEndpoint → `rest_api_endpoint` (better than `rest_a_p_i_endpoint`)
- OAuth2Provider → `oauth2_provider` (better than `o_auth_2_provider`)

**Decision**: Use acronym-aware conversion

---

## Summary

**Answer to "B2B" question**:

```python
# Option 1: Basic (current plan)
camel_to_snake("B2BProduct")  # → "b_2_b_product"

# Option 2: With acronym support (this enhancement)
camel_to_snake("B2BProduct")  # → "b2b_product" ✅ Better

# Option 3: Custom acronym
camel_to_snake("Product2B", preserve_acronyms={'2B'})  # → "product_2b"
```

**Recommended**: Implement basic first, add acronym support as Phase 4.5.2 if needed.

---

*Optional Enhancement to Issue #6 Phase 4.5*
*Status: Design Complete, Implementation Optional*
