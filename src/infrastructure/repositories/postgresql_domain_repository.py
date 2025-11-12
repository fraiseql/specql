"""PostgreSQL-backed Domain Repository"""
import psycopg
from src.domain.entities.domain import Domain, Subdomain
from src.domain.value_objects import DomainNumber

class PostgreSQLDomainRepository:
    """PostgreSQL-backed repository"""

    def __init__(self, db_url: str):
        self.db_url = db_url

    def get(self, domain_number: str) -> Domain:
        """Get domain by number from PostgreSQL"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                # Get domain
                cur.execute("""
                    SELECT domain_number, domain_name, description, multi_tenant, aliases
                    FROM specql_registry.tb_domain
                    WHERE domain_number = %s
                """, (domain_number,))

                row = cur.fetchone()
                if not row:
                    raise ValueError(f"Domain {domain_number} not found")

                domain = Domain(
                    domain_number=DomainNumber(row[0]),
                    domain_name=row[1],
                    description=row[2],
                    multi_tenant=row[3],
                    aliases=row[4] or []
                )

                # Get subdomains
                cur.execute("""
                    SELECT pk_subdomain, subdomain_number, subdomain_name, description, next_entity_sequence
                    FROM specql_registry.tb_subdomain
                    WHERE fk_domain = (
                        SELECT pk_domain FROM specql_registry.tb_domain WHERE domain_number = %s
                    )
                """, (domain_number,))

                for subdomain_row in cur.fetchall():
                    subdomain = Subdomain(
                        subdomain_number=subdomain_row[1],
                        subdomain_name=subdomain_row[2],
                        description=subdomain_row[3],
                        next_entity_sequence=subdomain_row[4]
                    )

                    # Get entities for this subdomain
                    cur.execute("""
                        SELECT entity_name, table_code, entity_sequence
                        FROM specql_registry.tb_entity_registration
                        WHERE fk_subdomain = %s
                    """, (subdomain_row[0],))

                    for entity_row in cur.fetchall():
                        subdomain.entities[entity_row[0]] = {
                            'table_code': entity_row[1],
                            'entity_sequence': entity_row[2]
                        }

                    domain.add_subdomain(subdomain)

                return domain

    def save(self, domain: Domain) -> None:
        """Save domain to PostgreSQL (transactional)"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                # Save domain
                cur.execute("""
                    INSERT INTO specql_registry.tb_domain
                    (domain_number, domain_name, description, multi_tenant, aliases)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (domain_number) DO UPDATE SET
                        domain_name = EXCLUDED.domain_name,
                        description = EXCLUDED.description,
                        multi_tenant = EXCLUDED.multi_tenant,
                        aliases = EXCLUDED.aliases
                    RETURNING pk_domain
                """, (
                    domain.domain_number.value,
                    domain.domain_name,
                    domain.description,
                    domain.multi_tenant,
                    domain.aliases
                ))

                result = cur.fetchone()
                if result is None:
                    raise ValueError(f"Failed to insert domain {domain.domain_number.value}")
                domain_pk = result[0]

                # Save subdomains
                for subdomain in domain.subdomains.values():
                    cur.execute("""
                        INSERT INTO specql_registry.tb_subdomain
                        (fk_domain, subdomain_number, subdomain_name, description, next_entity_sequence)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (fk_domain, subdomain_number) DO UPDATE SET
                            subdomain_name = EXCLUDED.subdomain_name,
                            description = EXCLUDED.description,
                            next_entity_sequence = EXCLUDED.next_entity_sequence
                    """, (
                        domain_pk,
                        subdomain.subdomain_number,
                        subdomain.subdomain_name,
                        subdomain.description,
                        subdomain.next_entity_sequence
                    ))

                conn.commit()

    def find_by_name(self, name_or_alias: str) -> Domain | None:
        """Find domain by name or alias"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                # Try exact name match first
                cur.execute("""
                    SELECT domain_number FROM specql_registry.tb_domain
                    WHERE domain_name = %s
                """, (name_or_alias,))

                row = cur.fetchone()
                if row:
                    return self.get(row[0])

                # Try alias match
                cur.execute("""
                    SELECT domain_number FROM specql_registry.tb_domain
                    WHERE %s = ANY(aliases)
                """, (name_or_alias,))

                row = cur.fetchone()
                if row:
                    return self.get(row[0])

                return None

    def list_all(self) -> list[Domain]:
        """List all domains"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT domain_number FROM specql_registry.tb_domain")
                domain_numbers = [row[0] for row in cur.fetchall()]
                return [self.get(num) for num in domain_numbers]