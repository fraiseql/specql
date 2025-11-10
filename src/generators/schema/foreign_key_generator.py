"""
Foreign Key Generator

Generates foreign key constraints from Team A's reference fields:
- INTEGER fk_* columns (Trinity Pattern)
- REFERENCES constraints
- ON DELETE/UPDATE actions
- B-tree indexes
"""

from dataclasses import dataclass

from src.core.ast_models import FieldDefinition

from .index_strategy import generate_btree_index


@dataclass
class ForeignKeyDDL:
    """DDL output for a foreign key"""

    column_name: str
    postgres_type: str = "INTEGER"  # Trinity Pattern
    nullable: bool = True
    references_schema: str = "public"
    references_table: str = ""
    references_column: str = ""
    on_delete: str = "RESTRICT"
    on_update: str = "CASCADE"
    comment: str | None = None


class ForeignKeyGenerator:
    """Generates foreign key DDL from reference fields"""

    def map_field(self, field: FieldDefinition) -> ForeignKeyDDL:
        """
        Map reference field to foreign key DDL

        Args:
            field: FieldDefinition with reference_entity and reference_schema

        Returns:
            ForeignKeyDDL with FK constraint details
        """
        if not field.is_reference():
            raise ValueError(f"Field {field.name} is not a reference type")

        # Generate FK column name: fk_{field_name}
        fk_column = f"fk_{field.name}"

        # Reference table and column
        if field.reference_entity is None:
            raise ValueError(f"Reference field {field.name} has no reference_entity")
        ref_entity_lower = field.reference_entity.lower()
        ref_table = f"tb_{ref_entity_lower}"
        ref_column = f"pk_{ref_entity_lower}"

        return ForeignKeyDDL(
            column_name=fk_column,
            postgres_type="INTEGER",  # Trinity Pattern: ALL FKs are INTEGER
            nullable=field.nullable,
            references_schema=field.reference_schema or "public",
            references_table=ref_table,
            references_column=ref_column,
            comment=f"Reference to {field.reference_entity}",
        )

    def generate_field_ddl(self, fk_ddl: ForeignKeyDDL) -> str:
        """
        Generate FK column with REFERENCES constraint

        Example output:
            fk_company INTEGER NOT NULL
            REFERENCES crm.tb_company(pk_company)
            ON DELETE RESTRICT ON UPDATE CASCADE
        """
        parts = [fk_ddl.column_name, fk_ddl.postgres_type]

        if not fk_ddl.nullable:
            parts.append("NOT NULL")

        # REFERENCES constraint
        ref_target = (
            f"{fk_ddl.references_schema}.{fk_ddl.references_table}({fk_ddl.references_column})"
        )
        parts.append(f"REFERENCES {ref_target}")

        # ON DELETE/UPDATE actions
        parts.append(f"ON DELETE {fk_ddl.on_delete}")
        parts.append(f"ON UPDATE {fk_ddl.on_update}")

        return " ".join(parts)

    def generate_index(self, schema: str, table: str, fk_ddl: ForeignKeyDDL) -> str:
        """
        Generate B-tree index on FK column with partial index support

        Example output:
            CREATE INDEX idx_contact_company
            ON crm.tb_contact(fk_company)
            WHERE deleted_at IS NULL;
        """
        entity_name = table.replace("tb_", "")
        field_name = fk_ddl.column_name.replace("fk_", "")
        index_name = f"idx_{entity_name}_{field_name}"
        table_name = f"{schema}.{table}"

        return generate_btree_index(table_name, index_name, [fk_ddl.column_name])
