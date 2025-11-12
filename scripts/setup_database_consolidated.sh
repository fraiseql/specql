#!/bin/bash
set -e

echo "========================================="
echo "SpecQL: Consolidated Database Setup"
echo "========================================="
echo ""

# Configuration
DB_NAME="specql"
DB_USER="specql_user"
DB_PASSWORD="specql_dev_password"  # Change for production!

echo "Creating PostgreSQL database and user..."

# Create database and user
sudo -u postgres psql << EOF
-- Create user if not exists
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '$DB_USER') THEN
       CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    END IF;
END
\$\$;

-- Create database if not exists
SELECT 'CREATE DATABASE $DB_NAME'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF

echo "✓ Database '$DB_NAME' created"
echo "✓ User '$DB_USER' created"

# Install extensions
echo ""
echo "Installing PostgreSQL extensions..."
sudo -u postgres psql -d $DB_NAME << EOF
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
EOF

echo "✓ pgvector extension installed"
echo "✓ pg_trgm extension installed"

# Create schemas
echo ""
echo "Creating schemas..."
sudo -u postgres psql -d $DB_NAME << EOF
-- Grant schema creation privilege
GRANT CREATE ON DATABASE $DB_NAME TO $DB_USER;
EOF

# Now run as specql_user to create schemas
PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d $DB_NAME << EOF
-- Create specql_registry schema
\i db/schema/00_registry/specql_registry.sql

-- Create pattern_library schema
\i database/pattern_library_schema.sql

-- Verify schemas
SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('specql_registry', 'pattern_library');
EOF

echo "✓ Schemas created"

# Set connection string
echo ""
echo "========================================="
echo "Setup complete! ✓"
echo "========================================="
echo ""
echo "Connection string:"
echo "postgresql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME"
echo ""
echo "Add to your environment:"
echo "export SPECQL_DB_URL='postgresql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME'"
echo ""
echo "Verify schemas:"
echo "psql \$SPECQL_DB_URL -c \"\\dn\""
echo ""
