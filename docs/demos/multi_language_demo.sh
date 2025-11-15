#!/bin/bash

# SpecQL Multi-Language Generation Demo Script

clear
echo "SpecQL Multi-Language Generation Demo"
echo "======================================"
echo ""
sleep 2

echo "Starting with one YAML file..."
echo ""
cat << 'EOF'
entity: Contact
schema: crm

fields:
  email: email
  name: text
  company: ref(Company)

actions:
  - name: archive
    steps:
      - update: Contact SET archived = true
EOF
sleep 4
echo ""

echo "Generating PostgreSQL..."
sleep 1
echo "✓ Generated: 01_tables.sql (450 lines)"
echo "✓ Generated: 02_functions.sql (280 lines)"
echo ""
sleep 2

echo "Generating Java/Spring Boot..."
sleep 1
echo "✓ Generated: Contact.java (380 lines)"
echo "✓ Generated: ContactRepository.java (120 lines)"
echo "✓ Generated: ContactService.java (240 lines)"
echo ""
sleep 2

echo "Generating Rust/Diesel..."
sleep 1
echo "✓ Generated: models.rs (420 lines)"
echo "✓ Generated: schema.rs (180 lines)"
echo ""
sleep 2

echo "Generating TypeScript/Prisma..."
sleep 1
echo "✓ Generated: schema.prisma (350 lines)"
echo "✓ Generated: types.ts (220 lines)"
echo ""
sleep 2

echo "════════════════════════════════════════"
echo "Total: 2,640 lines from 15 lines YAML"
echo "Code leverage: 176x"
echo "════════════════════════════════════════"
echo ""
sleep 3

echo "All languages maintain identical semantics!"