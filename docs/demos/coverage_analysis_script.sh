#!/bin/bash
# Demo Script: Coverage Analysis
# This script demonstrates analyzing test coverage with reverse engineering
# Run time: ~30 seconds

set -e

echo "📊 SpecQL Coverage Analysis Demo"
echo "==============================="
echo ""

# Setup: Copy test files
echo "📋 Setup: Preparing test files"
echo "------------------------------"
mkdir -p demo_tests
cp docs/06_examples/simple_contact/generated_tests/test_contact_*.sql demo_tests/
cp docs/06_examples/simple_contact/generated_tests/test_contact_integration.py demo_tests/
echo "✅ Test files ready"
echo ""

# Step 1: Show what we're analyzing
echo "🔍 Step 1: Test Files to Analyze"
echo "--------------------------------"
echo "Analyzing test coverage for Contact entity:"
ls -la demo_tests/
echo ""

# Step 2: Run coverage analysis
echo "⚡ Step 2: Running Coverage Analysis"
echo "-----------------------------------"
echo "Command: specql reverse-tests demo_tests/ --analyze-coverage --entity=Contact --preview"
echo ""

# Simulate coverage analysis output
cat << 'EOF'
📊 Coverage Analysis for Contact Entity

✅ Well Covered (90-100%):
  • Table structure (100%) - 10/10 scenarios
  • Basic CRUD operations (95%) - 18/19 scenarios
  • Primary key constraints (100%) - 3/3 scenarios
  • qualify_lead action happy path (100%) - 4/4 scenarios

⚠️ Partially Covered (50-89%):
  • Error handling (60%) - 7/10 scenarios
    Missing: Invalid email format test
    Missing: Null email test
  • State transitions (70%) - 3/5 scenarios
    Missing: Reverse transition tests

❌ Not Covered (0-49%):
  • Concurrent updates - 0/5 scenarios
  • Bulk operations - 0/3 scenarios
  • Permission edge cases - 0/4 scenarios

📝 Suggested Tests:
  1. test_create_contact_invalid_email
  2. test_create_contact_null_email
  3. test_qualify_already_qualified_contact
  4. test_concurrent_contact_updates
  5. test_bulk_contact_creation

Coverage Score: 78% (43/55 potential scenarios)
EOF

echo ""

# Step 3: Show detailed gap analysis
echo "🎯 Step 3: Detailed Gap Analysis"
echo "-------------------------------"
echo "Command: specql reverse-tests demo_tests/ --analyze-gaps --entity=Contact"
echo ""

# Simulate gap analysis output
cat << 'EOF'
Critical Gaps (High Priority):

1. Error Handling - Invalid Email Format
   Impact: High - Data integrity
   Current: 0 tests
   Recommended: 3 tests
   Example:
   SELECT throws_ok(
       $$SELECT app.create_contact(
           '01232122-0000-0000-2000-000000000001'::UUID,
           '01232122-0000-0000-2000-000000000002'::UUID,
           '{"email": "not-an-email", "first_name": "Test"}'::JSONB
       )$$,
       'invalid_email',
       'Invalid email should be rejected'
   );

2. Concurrent Update Handling
   Impact: High - Data consistency
   Current: 0 tests
   Recommended: 2 tests

3. Permission Validation
   Impact: Medium - Security
   Current: 1/4 tests
   Recommended: 3 tests
EOF

echo ""

# Step 4: Show TestSpec generation
echo "📄 Step 4: Generate TestSpec"
echo "---------------------------"
echo "Command: specql reverse-tests demo_tests/ --format testspec --output-dir specs/"
echo ""

# Simulate TestSpec generation
echo "📄 Generated specs/test_contact_spec.yaml"
echo "📄 Generated specs/test_contact_integration_spec.yaml"
echo ""

# Step 5: Show TestSpec preview
echo "👀 Step 5: TestSpec Preview"
echo "--------------------------"
echo "First few scenarios from generated TestSpec:"
echo ""

cat << 'EOF'
entity_name: Contact
test_framework: pgtap
source_language: pgtap

scenarios:
  - name: table_exists
    category: structure
    description: Verify Contact table exists in database
    assertions:
      - type: has_table
        target: crm.tb_contact
        expected: true
        message: Contact table should exist

  - name: create_contact_success
    category: crud_create
    description: Successfully create a new contact
    setup:
      - type: insert_fixture
        table: crm.tenant
        data:
          id: "01232122-0000-0000-2000-000000000001"
          name: "Test Tenant"
    steps:
      - action: call_function
        function: app.create_contact
        parameters:
          - type: uuid
            value: "01232122-0000-0000-2000-000000000001"
    assertions:
      - type: equals
        target: result.status
        expected: success
        message: Contact creation should return success
EOF

echo "... (15+ more scenarios)"
echo ""

# Step 6: Show actionable recommendations
echo "💡 Step 6: Actionable Recommendations"
echo "------------------------------------"
echo "Based on the analysis, here are the next steps:"
echo ""
echo "1. 🔴 HIGH PRIORITY - Add validation tests"
echo "   - Generate: specql generate-tests entities/contact.yaml --focus validation"
echo ""
echo "2. 🟡 MEDIUM PRIORITY - Add concurrency tests"
echo "   - Generate: specql generate-tests entities/contact.yaml --focus concurrency"
echo ""
echo "3. 🔵 LOW PRIORITY - Add bulk operation tests"
echo "   - Generate: specql generate-tests entities/contact.yaml --focus bulk"
echo ""
echo "4. 📈 Target: Improve coverage from 78% to 95%"
echo ""

echo "🎉 Demo Complete!"
echo "================="
echo "Coverage analysis revealed 12 gaps and provided specific recommendations!"
echo ""
echo "Key insights:"
echo "- Current coverage: 78% (43/55 scenarios)"
echo "- 5 critical gaps identified"
echo "- Actionable test generation commands provided"

# Cleanup
rm -rf demo_tests