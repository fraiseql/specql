"""
FraiseQL Rich Type Registry
Maps SpecQL rich types to PostgreSQL storage types and GraphQL scalars
"""

from dataclasses import dataclass


@dataclass
class TypeMetadata:
    """Metadata for a rich type"""

    specql_name: str
    postgres_type: str
    graphql_scalar: str
    description: str
    validation_pattern: str | None = None


class TypeRegistry:
    """Registry of FraiseQL rich types and their mappings"""

    def __init__(self) -> None:
        self._types = self._build_type_registry()

    def _build_type_registry(self) -> dict[str, TypeMetadata]:
        """Build the complete type registry"""
        return {
            # String-based types
            "email": TypeMetadata(
                specql_name="email",
                postgres_type="TEXT",
                graphql_scalar="Email",
                description="Valid email address",
                validation_pattern=r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$",
            ),
            "url": TypeMetadata(
                specql_name="url",
                postgres_type="TEXT",
                graphql_scalar="Url",
                description="Valid URL",
                validation_pattern=r"^https?://",
            ),
            "phone": TypeMetadata(
                specql_name="phone",
                postgres_type="TEXT",
                graphql_scalar="PhoneNumber",
                description="Phone number (E.164 format)",
                validation_pattern=r"^\+?[1-9]\d{1,14}$",
            ),
            "phoneNumber": TypeMetadata(
                specql_name="phoneNumber",
                postgres_type="TEXT",
                graphql_scalar="PhoneNumber",
                description="Phone number (E.164 format)",
                validation_pattern=r"^\+?[1-9]\d{1,14}$",
            ),
            "ipAddress": TypeMetadata(
                specql_name="ipAddress",
                postgres_type="INET",
                graphql_scalar="IpAddress",
                description="IPv4 or IPv6 address",
            ),
            "macAddress": TypeMetadata(
                specql_name="macAddress",
                postgres_type="MACADDR",
                graphql_scalar="MacAddress",
                description="MAC address",
            ),
            "markdown": TypeMetadata(
                specql_name="markdown",
                postgres_type="TEXT",
                graphql_scalar="Markdown",
                description="Markdown formatted text",
            ),
            "html": TypeMetadata(
                specql_name="html",
                postgres_type="TEXT",
                graphql_scalar="Html",
                description="HTML content",
            ),
            # Numeric types
            "money": TypeMetadata(
                specql_name="money",
                postgres_type="NUMERIC(19,4)",
                graphql_scalar="Money",
                description="Monetary value",
            ),
            "percentage": TypeMetadata(
                specql_name="percentage",
                postgres_type="NUMERIC(5,2)",
                graphql_scalar="Percentage",
                description="Percentage value (0-100)",
            ),
            # Date/Time types
            "date": TypeMetadata(
                specql_name="date",
                postgres_type="DATE",
                graphql_scalar="Date",
                description="Date (YYYY-MM-DD)",
            ),
            "datetime": TypeMetadata(
                specql_name="datetime",
                postgres_type="TIMESTAMPTZ",
                graphql_scalar="DateTime",
                description="Timestamp with timezone",
            ),
            "time": TypeMetadata(
                specql_name="time",
                postgres_type="TIME",
                graphql_scalar="Time",
                description="Time of day",
            ),
            "duration": TypeMetadata(
                specql_name="duration",
                postgres_type="INTERVAL",
                graphql_scalar="Duration",
                description="Time duration",
            ),
            # Geographic types
            "coordinates": TypeMetadata(
                specql_name="coordinates",
                postgres_type="POINT",
                graphql_scalar="Coordinates",
                description="Geographic coordinates (lat/lng)",
            ),
            "latitude": TypeMetadata(
                specql_name="latitude",
                postgres_type="NUMERIC(10,8)",
                graphql_scalar="Latitude",
                description="Latitude (-90 to 90)",
            ),
            "longitude": TypeMetadata(
                specql_name="longitude",
                postgres_type="NUMERIC(11,8)",
                graphql_scalar="Longitude",
                description="Longitude (-180 to 180)",
            ),
            # Media types
            "image": TypeMetadata(
                specql_name="image",
                postgres_type="TEXT",
                graphql_scalar="Image",
                description="Image URL or path",
            ),
            "file": TypeMetadata(
                specql_name="file",
                postgres_type="TEXT",
                graphql_scalar="File",
                description="File URL or path",
            ),
            "color": TypeMetadata(
                specql_name="color",
                postgres_type="TEXT",
                graphql_scalar="Color",
                description="Color (hex code)",
                validation_pattern=r"^#[0-9A-Fa-f]{6}$",
            ),
            # Identifier types
            "uuid": TypeMetadata(
                specql_name="uuid",
                postgres_type="UUID",
                graphql_scalar="UUID",
                description="Universally unique identifier",
            ),
            "slug": TypeMetadata(
                specql_name="slug",
                postgres_type="TEXT",
                graphql_scalar="Slug",
                description="URL-friendly identifier",
                validation_pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
            ),
            # JSON types
            "json": TypeMetadata(
                specql_name="json",
                postgres_type="JSONB",
                graphql_scalar="JSON",
                description="JSON object",
            ),
        }

    def is_rich_type(self, type_name: str) -> bool:
        """Check if type is a FraiseQL rich type"""
        return type_name in self._types

    def get_postgres_type(self, type_name: str) -> str:
        """Get PostgreSQL storage type for rich type"""
        metadata = self._types.get(type_name)
        if not metadata:
            raise ValueError(f"Unknown rich type: {type_name}")
        return str(metadata.postgres_type)

    def get_graphql_scalar(self, type_name: str) -> str:
        """Get GraphQL scalar name for rich type"""
        metadata = self._types.get(type_name)
        if not metadata:
            raise ValueError(f"Unknown rich type: {type_name}")
        return str(metadata.graphql_scalar)

    def get_validation_pattern(self, type_name: str) -> str | None:
        """Get regex validation pattern for rich type"""
        metadata = self._types.get(type_name)
        if not metadata:
            return None
        return metadata.validation_pattern

    def get_all_rich_types(self) -> set[str]:
        """Get set of all rich type names"""
        return set(self._types.keys())


# Global singleton instance
_type_registry = TypeRegistry()

# Convenience constants
FRAISEQL_RICH_TYPES = _type_registry.get_all_rich_types()


def get_type_registry() -> TypeRegistry:
    """Get the global type registry instance"""
    return _type_registry
