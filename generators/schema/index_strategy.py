"""Index generation strategy with partial index support."""


def generate_index(
    table_name: str,
    index_name: str,
    columns: list[str],
    index_type: str = "btree",
    unique: bool = False,
    partial: bool = True,  # NEW: Default to partial indexes
) -> str:
    """Generate index with optional partial index clause.

    Args:
        table_name: Full table name (schema.table_name)
        index_name: Name of the index
        columns: List of column names to index
        index_type: Index type ('btree', 'gin', 'gist', etc.)
        unique: Whether this is a unique index
        partial: Whether to add WHERE deleted_at IS NULL (default True)

    Returns:
        SQL CREATE INDEX statement

    Example:
        generate_index(
            table_name='tenant.tb_location',
            index_name='idx_location_parent',
            columns=['fk_parent_location'],
            partial=True  # Adds WHERE deleted_at IS NULL
        )
    """
    unique_clause = "UNIQUE " if unique else ""
    using_clause = f"USING {index_type}" if index_type != "btree" else ""
    column_list = ", ".join(columns)

    # Partial index clause (exclude soft-deleted rows)
    where_clause = ""
    if partial and not unique:  # Don't apply to unique constraints
        where_clause = "\n    WHERE deleted_at IS NULL"

    return f"""CREATE {unique_clause}INDEX {index_name}
    ON {table_name} {using_clause}({column_list}){where_clause};""".strip()


def generate_btree_index(
    table_name: str, index_name: str, columns: list[str], partial: bool = True
) -> str:
    """Generate B-tree index (most common type)."""
    return generate_index(table_name, index_name, columns, "btree", False, partial)


def generate_gin_index(
    table_name: str, index_name: str, columns: list[str], partial: bool = True
) -> str:
    """Generate GIN index for JSONB and full-text search."""
    return generate_index(table_name, index_name, columns, "gin", False, partial)


def generate_gist_index(
    table_name: str, index_name: str, columns: list[str], partial: bool = True
) -> str:
    """Generate GIST index for geometric and range types."""
    return generate_index(table_name, index_name, columns, "gist", False, partial)
