#!/bin/bash
# Verification script for data storage consolidation

set -e

echo "========================================="
echo "SpecQL Data Storage Consolidation"
echo "Verification Report"
echo "========================================="
echo ""

export SPECQL_DB_URL='postgresql://specql_user:specql_dev_password@localhost/specql'

# 1. Check PostgreSQL connection
echo "1. PostgreSQL Connection"
echo "   Database: specql"
if psql $SPECQL_DB_URL -c "SELECT current_database(), current_user;" > /dev/null 2>&1; then
    echo "   ✓ Connection successful"
else
    echo "   ✗ Connection failed"
    exit 1
fi
echo ""

# 2. Check schemas
echo "2. Schemas"
SCHEMAS=$(psql $SPECQL_DB_URL -t -c "SELECT count(*) FROM information_schema.schemata WHERE schema_name IN ('specql_registry', 'pattern_library');")
if [ "$SCHEMAS" -eq 2 ]; then
    echo "   ✓ Both schemas exist (specql_registry, pattern_library)"
else
    echo "   ✗ Missing schemas"
    exit 1
fi
echo ""

# 3. Check domain registry
echo "3. Domain Registry (specql_registry schema)"
DOMAIN_COUNT=$(psql $SPECQL_DB_URL -t -c "SELECT count(*) FROM specql_registry.tb_domain;")
SUBDOMAIN_COUNT=$(psql $SPECQL_DB_URL -t -c "SELECT count(*) FROM specql_registry.tb_subdomain;")
echo "   Domains: $DOMAIN_COUNT"
echo "   Subdomains: $SUBDOMAIN_COUNT"
if [ "$DOMAIN_COUNT" -ge 6 ]; then
    echo "   ✓ Domain registry populated"
else
    echo "   ✗ Domain registry not properly initialized"
    exit 1
fi
echo ""

# 4. Check pattern library
echo "4. Pattern Library (pattern_library schema)"
PATTERN_COUNT=$(psql $SPECQL_DB_URL -t -c "SELECT count(*) FROM pattern_library.domain_patterns;")
echo "   Patterns: $PATTERN_COUNT"
if [ "$PATTERN_COUNT" -ge 25 ]; then
    echo "   ✓ Patterns migrated from SQLite"
else
    echo "   ✗ Pattern migration incomplete"
    exit 1
fi
echo ""

# 5. Check pgvector extension
echo "5. PostgreSQL Extensions"
PGVECTOR=$(psql $SPECQL_DB_URL -t -c "SELECT count(*) FROM pg_extension WHERE extname='vector';")
if [ "$PGVECTOR" -eq 1 ]; then
    echo "   ✓ pgvector extension installed"
else
    echo "   ✗ pgvector extension missing"
    exit 1
fi
echo ""

# 6. Check SQLite files archived
echo "6. SQLite Database Archival"
if [ -d "archive/sqlite_databases" ]; then
    if [ -f "archive/sqlite_databases/pattern_library.db" ]; then
        echo "   ✓ SQLite databases archived"
    else
        echo "   ✗ SQLite archival incomplete"
        exit 1
    fi
else
    echo "   ✗ Archive directory not found"
    exit 1
fi

if [ ! -f "pattern_library.db" ]; then
    echo "   ✓ SQLite databases removed from working directory"
else
    echo "   ✗ SQLite files still in working directory"
    exit 1
fi
echo ""

# 7. Sample data verification
echo "7. Sample Data Verification"
echo ""
echo "   Top 5 domains:"
psql $SPECQL_DB_URL -c "SELECT domain_number, domain_name FROM specql_registry.tb_domain ORDER BY domain_number LIMIT 5;" | sed 's/^/   /'
echo ""
echo "   Top 5 patterns:"
psql $SPECQL_DB_URL -c "SELECT name, category, source_type FROM pattern_library.domain_patterns ORDER BY name LIMIT 5;" | sed 's/^/   /'
echo ""

# 8. Final summary
echo "========================================="
echo "VERIFICATION COMPLETE ✓"
echo "========================================="
echo ""
echo "Current State:"
echo "  • PostgreSQL database: specql"
echo "  • Schemas: specql_registry, pattern_library"
echo "  • Domains: $DOMAIN_COUNT"
echo "  • Subdomains: $SUBDOMAIN_COUNT"
echo "  • Patterns: $PATTERN_COUNT"
echo "  • SQLite files: Archived"
echo ""
echo "Data Storage Consolidation: ✓ COMPLETE"
echo ""
echo "Connection string:"
echo "  export SPECQL_DB_URL='$SPECQL_DB_URL'"
echo ""
