#!/bin/bash
set -e

echo "========================================="
echo "SpecQL Pattern Library: Database Setup"
echo "========================================="
echo ""

# Configuration
DB_NAME="specql_patterns"
DB_USER="specql_user"
DB_PASSWORD="specql_dev_password"  # Change for production!

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

# Install pgvector extension
echo ""
echo "Installing pgvector extension..."
sudo -u postgres psql -d $DB_NAME << EOF
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For text similarity
EOF

echo "✓ pgvector extension installed"
echo "✓ pg_trgm extension installed"

# Set connection string
echo ""
echo "Connection string:"
echo "postgresql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME"
echo ""
echo "Add to ~/.bashrc:"
echo "export SPECQL_DB_URL='postgresql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME'"

echo ""
echo "========================================="
echo "Setup complete! ✓"
echo "========================================="