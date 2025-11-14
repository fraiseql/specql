"""Naming utility functions with smart acronym handling"""

import re

# Common business/technical acronyms to preserve as single units
COMMON_ACRONYMS = {
    # Business models
    "B2B",
    "B2C",
    "C2C",
    "P2P",
    "G2B",
    "G2C",
    # Protocols & Standards
    "API",
    "REST",
    "HTTP",
    "HTTPS",
    "FTP",
    "SFTP",
    "SSH",
    "SSL",
    "TLS",
    "SOAP",
    "gRPC",
    "GraphQL",
    "MQTT",
    "AMQP",
    # Data formats
    "JSON",
    "XML",
    "HTML",
    "CSS",
    "YAML",
    "TOML",
    "SQL",
    "CSV",
    # Identifiers
    "URL",
    "URI",
    "URN",
    "UUID",
    "GUID",
    "ISBN",
    "ISSN",
    # File formats
    "PDF",
    "PNG",
    "JPG",
    "JPEG",
    "GIF",
    "SVG",
    "ZIP",
    "TAR",
    # Cloud/Infrastructure
    "AWS",
    "GCP",
    "Azure",
    "SDK",
    "IDE",
    "CLI",
    "GUI",
    "VM",
    "CDN",
    # Business systems
    "CRM",
    "ERP",
    "POS",
    "SKU",
    "WMS",
    "MRP",
    "SCM",
    "HRM",
    # Network/Protocol
    "IPv4",
    "IPv6",
    "TCP",
    "UDP",
    "DNS",
    "DHCP",
    "NAT",
    "VPN",
    "IP",
    "MAC",
    "LAN",
    "WAN",
    "VLAN",
    # Authentication/Security
    "2FA",
    "MFA",
    "SSO",
    "OAuth",
    "SAML",
    "LDAP",
    "JWT",
    "PKI",
    # Database
    "RDBMS",
    "NoSQL",
    "ACID",
    "CRUD",
    # Other common
    "SLA",
    "KPI",
    "ROI",
    "CEO",
    "CTO",
    "COO",
    "CFO",
}


def camel_to_snake(
    name: str,
    preserve_acronyms: set[str] | None = None,
    use_common_acronyms: bool = True,
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
        # Only preserve acronym if followed by uppercase letter, digit, or end of string
        pattern = rf"{re.escape(acronym)}(?=[A-Z0-9]|$)"
        matches = list(re.finditer(pattern, temp_name))
        for match in matches:
            placeholder = f"[[{i}]]"
            start, end = match.span()
            temp_name = temp_name[:start] + placeholder + temp_name[end:]
            placeholder_map[placeholder] = acronym.lower()
            i += 1  # Increment i for next placeholder

    # Standard camel_to_snake conversion on temp_name
    s1 = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", temp_name)
    s2 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", s1)
    s3 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s2)
    s4 = re.sub(
        r"([a-zA-Z])(\[\[\d+\]\])", r"\1_\2", s3
    )  # Handle transitions to placeholders
    s5 = re.sub(
        r"(\[\[\d+\]\])([A-Z])", r"\1_\2", s4
    )  # Handle transitions from placeholders
    s6 = re.sub(
        r"(\d)(\[\[\d+\]\])", r"\1_\2", s5
    )  # Handle digit to placeholder transitions
    s7 = re.sub(
        r"(\[\[\d+\]\])(\[\[\d+\]\])", r"\1_\2", s6
    )  # Handle transitions between placeholders
    # Handle letter to digit transitions (but not in placeholders)
    s8 = re.sub(r"([a-zA-Z])(\d)(?!\[\[)", r"\1_\2", s7)
    result = s8.lower()

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
    if not name:
        return ""

    if "_" in name and name.islower():
        return name

    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)
    s3 = re.sub(r"([a-zA-Z])(\d)", r"\1_\2", s2)
    return s3.lower().replace("__", "_").strip("_")


def to_entity_name(name: str, preserve_acronyms: set[str] | None = None) -> str:
    """
    Convert entity name to snake_case for use in file/directory names

    Convenience wrapper around camel_to_snake for entity names.

    Args:
        name: Entity name (usually PascalCase)

    Returns:
        snake_case entity name

    Examples:
        >>> to_entity_name("Contact")
        'contact'
        >>> to_entity_name("DuplexMode")
        'duplex_mode'
    """
    return camel_to_snake(name, preserve_acronyms=preserve_acronyms)


def to_snake_case(name: str) -> str:
    """
    Convert string to snake_case

    Alias for camel_to_snake for convenience.

    Args:
        name: String to convert

    Returns:
        snake_case version
    """
    return camel_to_snake(name)


def to_pascal_case(name: str) -> str:
    """
    Convert string to PascalCase

    Args:
        name: String to convert (snake_case, camelCase, etc.)

    Returns:
        PascalCase version

    Examples:
        >>> to_pascal_case("contact")
        'Contact'
        >>> to_pascal_case("duplex_mode")
        'DuplexMode'
        >>> to_pascal_case("userAPI")
        'UserAPI'
    """
    if not name:
        return ""

    # Split on underscores and other separators
    words = re.split(r"[_-]", name)

    # Capitalize each word
    pascal_words = []
    for word in words:
        if word:
            # Handle acronyms (all caps)
            if word.isupper() and len(word) > 1:
                pascal_words.append(word)
            else:
                pascal_words.append(word.capitalize())

    return "".join(pascal_words)
