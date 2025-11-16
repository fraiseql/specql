"""Integration tests for PostgreSQL Domain Repository migration"""

import pytest
from pathlib import Path
from src.infrastructure.repositories.postgresql_domain_repository import (
    PostgreSQLDomainRepository,
)
from src.infrastructure.repositories.yaml_domain_repository import YAMLDomainRepository


class TestPostgreSQLDomainRepositoryMigration:
    """Test migration from YAML to PostgreSQL domain repository"""

    @pytest.fixture(autouse=True)
    def setup_schema(self, test_db):
        """Set up the specql_registry schema for all tests"""
        schema_sql = """
        -- SPECQL Registry Schema
        CREATE SCHEMA IF NOT EXISTS specql_registry;

        -- Domain table
        CREATE TABLE IF NOT EXISTS specql_registry.tb_domain (
            pk_domain SERIAL PRIMARY KEY,
            domain_number VARCHAR(10) NOT NULL UNIQUE,
            domain_name VARCHAR(100) NOT NULL,
            description TEXT,
            multi_tenant BOOLEAN NOT NULL DEFAULT FALSE,
            aliases TEXT[] DEFAULT ARRAY[]::TEXT[]
        );

        -- Subdomain table
        CREATE TABLE IF NOT EXISTS specql_registry.tb_subdomain (
            pk_subdomain SERIAL PRIMARY KEY,
            fk_domain INTEGER NOT NULL REFERENCES specql_registry.tb_domain(pk_domain) ON DELETE CASCADE,
            subdomain_number VARCHAR(10) NOT NULL,
            subdomain_name VARCHAR(100) NOT NULL,
            description TEXT,
            next_entity_sequence INTEGER NOT NULL DEFAULT 1,
            UNIQUE(fk_domain, subdomain_number)
        );

        -- Entity registration table
        CREATE TABLE IF NOT EXISTS specql_registry.tb_entity_registration (
            pk_entity_registration SERIAL PRIMARY KEY,
            fk_subdomain INTEGER NOT NULL REFERENCES specql_registry.tb_subdomain(pk_subdomain) ON DELETE CASCADE,
            entity_name VARCHAR(100) NOT NULL,
            table_code VARCHAR(20) NOT NULL,
            entity_sequence INTEGER NOT NULL,
            UNIQUE(fk_subdomain, entity_name)
        );

        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_tb_domain_domain_number ON specql_registry.tb_domain(domain_number);
        CREATE INDEX IF NOT EXISTS idx_tb_domain_domain_name ON specql_registry.tb_domain(domain_name);
        CREATE INDEX IF NOT EXISTS idx_tb_subdomain_fk_domain ON specql_registry.tb_subdomain(fk_domain);
        CREATE INDEX IF NOT EXISTS idx_tb_entity_registration_fk_subdomain ON specql_registry.tb_entity_registration(fk_subdomain);
        """
        with test_db.cursor() as cur:
            cur.execute(schema_sql)
        test_db.commit()

    def test_schema_exists(self, test_db):
        """Test that specql_registry schema exists"""
        with test_db.cursor() as cur:
            cur.execute("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name = 'specql_registry'
            """)
            result = cur.fetchone()
            assert result is not None, "specql_registry schema should exist"
            assert result[0] == "specql_registry"

    def test_domain_table_exists(self, test_db):
        """Test that tb_domain table exists with correct structure"""
        with test_db.cursor() as cur:
            # Check table exists
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'specql_registry' AND table_name = 'tb_domain'
            """)
            result = cur.fetchone()
            assert result is not None, "tb_domain table should exist"

            # Check columns
            cur.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'specql_registry' AND table_name = 'tb_domain'
                ORDER BY column_name
            """)
            columns = cur.fetchall()
            column_names = [col[0] for col in columns]

            expected_columns = [
                "aliases",
                "description",
                "domain_name",
                "domain_number",
                "multi_tenant",
                "pk_domain",
            ]
            assert set(column_names) == set(expected_columns), (
                f"Expected columns {expected_columns}, got {column_names}"
            )

    def test_subdomain_table_exists(self, test_db):
        """Test that tb_subdomain table exists with correct structure"""
        with test_db.cursor() as cur:
            # Check table exists
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'specql_registry' AND table_name = 'tb_subdomain'
            """)
            result = cur.fetchone()
            assert result is not None, "tb_subdomain table should exist"

            # Check columns
            cur.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'specql_registry' AND table_name = 'tb_subdomain'
                ORDER BY column_name
            """)
            columns = cur.fetchall()
            column_names = [col[0] for col in columns]

            expected_columns = [
                "description",
                "fk_domain",
                "next_entity_sequence",
                "pk_subdomain",
                "subdomain_name",
                "subdomain_number",
            ]
            assert set(column_names) == set(expected_columns), (
                f"Expected columns {expected_columns}, got {column_names}"
            )

    def test_entity_registration_table_exists(self, test_db):
        """Test that tb_entity_registration table exists with correct structure"""
        with test_db.cursor() as cur:
            # Check table exists
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'specql_registry' AND table_name = 'tb_entity_registration'
            """)
            result = cur.fetchone()
            assert result is not None, "tb_entity_registration table should exist"

            # Check columns
            cur.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'specql_registry' AND table_name = 'tb_entity_registration'
                ORDER BY column_name
            """)
            columns = cur.fetchall()
            column_names = [col[0] for col in columns]

            expected_columns = [
                "entity_name",
                "entity_sequence",
                "fk_subdomain",
                "pk_entity_registration",
                "table_code",
            ]
            assert set(column_names) == set(expected_columns), (
                f"Expected columns {expected_columns}, got {column_names}"
            )

    def test_migration_populates_data(self, test_db, db_config):
        """Test that migration script populates data from YAML"""
        # Build connection string
        conn_parts = [
            f"host={db_config['host']}",
            f"port={db_config['port']}",
            f"dbname={db_config['dbname']}",
            f"user={db_config['user']}",
        ]
        if db_config["password"]:
            conn_parts.append(f"password={db_config['password']}")
        conn_string = " ".join(conn_parts)

        # Test that PostgreSQL repository can read data
        pg_repo = PostgreSQLDomainRepository(conn_string)

        # Compare with YAML repository
        yaml_repo = YAMLDomainRepository(Path("registry/domain_registry.yaml"))

        # Get all domains from both repositories
        yaml_domains = yaml_repo.list_all()
        pg_domains = pg_repo.list_all()

        assert len(pg_domains) == len(yaml_domains), (
            f"Expected {len(yaml_domains)} domains, got {len(pg_domains)}"
        )

        # Check each domain
        for yaml_domain in yaml_domains:
            pg_domain = pg_repo.get(yaml_domain.domain_number.value)

            assert pg_domain.domain_name == yaml_domain.domain_name
            assert pg_domain.description == yaml_domain.description
            assert pg_domain.multi_tenant == yaml_domain.multi_tenant
            assert set(pg_domain.aliases) == set(yaml_domain.aliases)

            # Check subdomains
            assert len(pg_domain.subdomains) == len(yaml_domain.subdomains)

            for subdomain_num, yaml_subdomain in yaml_domain.subdomains.items():
                pg_subdomain = pg_domain.get_subdomain(subdomain_num)

                assert pg_subdomain.subdomain_name == yaml_subdomain.subdomain_name
                assert pg_subdomain.description == yaml_subdomain.description
                assert (
                    pg_subdomain.next_entity_sequence
                    == yaml_subdomain.next_entity_sequence
                )

                # Check that essential entity data matches (PostgreSQL stores simplified version)
                assert len(pg_subdomain.entities) == len(yaml_subdomain.entities)
                for entity_name in yaml_subdomain.entities:
                    assert entity_name in pg_subdomain.entities
                    pg_entity = pg_subdomain.entities[entity_name]
                    yaml_entity = yaml_subdomain.entities[entity_name]

                    # PostgreSQL stores table_code and entity_sequence
                    if isinstance(yaml_entity, dict):
                        assert pg_entity["table_code"] == yaml_entity.get("table_code")
                        # entity_sequence might be stored as 'entity_sequence' or 'entity_number'
                        expected_sequence = yaml_entity.get(
                            "entity_sequence", yaml_entity.get("entity_number", 1)
                        )
                        assert pg_entity["entity_sequence"] == expected_sequence
                    else:
                        # Handle legacy format where yaml_entity might be just a table_code string
                        assert pg_entity["table_code"] == str(yaml_entity)

    def test_migration_script_populates_data(self, test_db, db_config):
        """Test that migration script correctly populates data from YAML"""
        from scripts.migrate_registry_to_postgres import migrate_registry_to_postgres

        # Build connection string
        conn_parts = [
            f"host={db_config['host']}",
            f"port={db_config['port']}",
            f"dbname={db_config['dbname']}",
            f"user={db_config['user']}",
        ]
        if db_config["password"]:
            conn_parts.append(f"password={db_config['password']}")
        conn_string = " ".join(conn_parts)

        # Run migration
        migrate_registry_to_postgres(conn_string, Path("registry/domain_registry.yaml"))

        # Verify data was migrated
        with test_db.cursor() as cur:
            # Check domains
            cur.execute("SELECT COUNT(*) FROM specql_registry.tb_domain")
            domain_count = cur.fetchone()[0]
            assert domain_count == 6  # Based on domain_registry.yaml

            # Check subdomains
            cur.execute("SELECT COUNT(*) FROM specql_registry.tb_subdomain")
            subdomain_count = cur.fetchone()[0]
            assert subdomain_count > 10  # Should have multiple subdomains

            # Check entity registrations
            cur.execute("SELECT COUNT(*) FROM specql_registry.tb_entity_registration")
            entity_count = cur.fetchone()[0]
            assert entity_count > 0  # Should have some entities

    def test_repository_api_compatibility(self, test_db, db_config):
        """Test that PostgreSQL repository has same API as YAML repository"""
        from scripts.migrate_registry_to_postgres import migrate_registry_to_postgres

        # Build connection string
        conn_parts = [
            f"host={db_config['host']}",
            f"port={db_config['port']}",
            f"dbname={db_config['dbname']}",
            f"user={db_config['user']}",
        ]
        if db_config["password"]:
            conn_parts.append(f"password={db_config['password']}")
        conn_string = " ".join(conn_parts)

        # First migrate data
        migrate_registry_to_postgres(conn_string, Path("registry/domain_registry.yaml"))

        pg_repo = PostgreSQLDomainRepository(conn_string)
        yaml_repo = YAMLDomainRepository(Path("registry/domain_registry.yaml"))

        # Test get method
        pg_domain = pg_repo.get("2")  # crm domain
        yaml_domain = yaml_repo.get("2")
        assert pg_domain.domain_name == yaml_domain.domain_name

        # Test find_by_name method
        pg_found = pg_repo.find_by_name("crm")
        yaml_found = yaml_repo.find_by_name("crm")
        assert pg_found is not None and yaml_found is not None
        assert pg_found.domain_number.value == yaml_found.domain_number.value

        # Test list_all method
        pg_all = pg_repo.list_all()
        yaml_all = yaml_repo.list_all()
        assert len(pg_all) == len(yaml_all)

        # Test save method (should work without errors)
        test_domain = pg_repo.get("1")  # core domain
        pg_repo.save(test_domain)  # Should not raise exception
