"""
Index Generator for Rich Types
Generates appropriate database indexes for FraiseQL rich types
"""

from src.core.ast_models import Entity, FieldDefinition
from src.utils.safe_slug import safe_slug, safe_table_name


class IndexGenerator:
    """Generates database indexes appropriate for rich types"""

    def generate_indexes_for_rich_types(self, entity: Entity) -> list[str]:
        """Generate indexes for all rich type fields in an entity"""
        indexes = []

        for field_name, field_def in entity.fields.items():
            if field_def.is_rich_type():
                field_indexes = self._generate_index_for_field(field_def, entity)
                indexes.extend(field_indexes)

        return indexes

    def _generate_index_for_field(self, field: FieldDefinition, entity: Entity) -> list[str]:
        """
        Generate appropriate index for a single rich type field

        Index Strategy by Rich Type:
        ===========================

        **B-tree Indexes** (Default for exact lookups, sorting, range queries):
        - **Used for**: email, phoneNumber, macAddress, slug, color, money
        - **Performance**: ~O(log n) lookups, 10-20% table size overhead
        - **Use cases**: WHERE email = 'user@example.com', ORDER BY price, price > 100

        **GIN Indexes with Trigram Operations** (Pattern matching):
        - **Used for**: url
        - **Performance**: ~O(1) pattern match, 50-300% table size overhead
        - **Use cases**: WHERE url LIKE '%example%', WHERE url ~ 'example'
        - **Requires**: CREATE EXTENSION pg_trgm;

        **GiST Indexes** (Spatial/geometric operations):
        - **Used for**: coordinates, latitude, longitude
        - **Performance**: ~O(log n) spatial queries, 50-100% table size overhead
        - **Use cases**: Point-in-polygon, distance calculations, bounding box queries

        **GiST Indexes with INET Operations** (Network operations):
        - **Used for**: ipAddress
        - **Performance**: ~O(log n) network queries, 50-100% table size overhead
        - **Use cases**: Subnet containment (WHERE '192.168.1.0/24' >>= ip_address)
        - **Requires**: Built-in inet_ops support

        Performance Considerations:
        - B-tree: Best for exact matches and range queries
        - GIN: Essential for LIKE/regex on text fields
        - GiST: Required for spatial/network operations
        - All indexes increase write overhead and storage

        Fallback: Unknown rich types default to B-tree for safety.
        """
        table_name = f"{entity.schema}.{safe_table_name(entity.name)}"
        # Index name follows table naming convention: idx_tb_{entity}_{field}
        index_name = f"idx_tb_{safe_slug(entity.name)}_{safe_slug(field.name)}"

        # Different index types based on rich type
        if field.type_name in ("email", "phoneNumber", "macAddress", "slug", "color", "money"):
            # B-tree indexes for exact lookups and range queries
            return [f"CREATE INDEX {index_name} ON {table_name} USING btree ({field.name});"]

        elif field.type_name == "url":
            # GIN index with trigram ops for pattern matching
            return [
                f"CREATE INDEX {index_name} ON {table_name} USING gin ({field.name} gin_trgm_ops);"
            ]

        elif field.type_name in ("coordinates", "latitude", "longitude"):
            # GiST indexes for spatial operations
            return [f"CREATE INDEX {index_name} ON {table_name} USING gist ({field.name});"]

        elif field.type_name == "ipAddress":
            # GiST index with inet ops for network operations
            return [
                f"CREATE INDEX {index_name} ON {table_name} USING gist ({field.name} inet_ops);"
            ]

        # Default to btree for unknown rich types
        return [f"CREATE INDEX {index_name} ON {table_name} USING btree ({field.name});"]
