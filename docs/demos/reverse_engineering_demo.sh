#!/bin/bash

# SpecQL Reverse Engineering Demo Script

clear
echo "SpecQL Reverse Engineering Demo"
echo "================================"
echo ""
sleep 2

echo "Scenario: Converting existing PostgreSQL schema to SpecQL YAML"
echo ""
sleep 2

# Show existing SQL
echo "Existing PostgreSQL schema:"
echo ""
cat << 'EOF'
CREATE TABLE crm.tb_contact (
    pk_contact SERIAL PRIMARY KEY,
    id UUID DEFAULT gen_random_uuid() UNIQUE,
    identifier TEXT,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
EOF
sleep 4
echo ""

# Run reverse engineering (when available)
echo "Running: specql reverse postgresql schema.sql --output entities/"
echo ""
sleep 2

# Show generated YAML
echo "Generated SpecQL YAML:"
echo ""
cat << 'EOF'
entity: Contact
schema: crm

fields:
  first_name: text
  last_name: text
  email: email
  created_at: timestamp

indexes:
  - fields: [email]
    unique: true
EOF
sleep 4
echo ""

echo "✅ Reverse engineering complete!"
echo ""
echo "Now you can:"
echo "  - Edit the YAML to add business logic"
echo "  - Generate code for multiple languages"
echo "  - Maintain schema as YAML going forward"
echo ""
sleep 3