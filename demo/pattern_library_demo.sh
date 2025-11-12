#!/bin/bash
set -e

echo "========================================="
echo "SpecQL Pattern Library - Complete Demo"
echo "========================================="
echo ""
echo "This demo shows the full pattern library workflow:"
echo "1. Database setup"
echo "2. Embedding generation"
echo "3. Pattern retrieval testing"
echo "4. Pattern discovery from SQL"
echo "5. Suggestion review & approval"
echo "6. Natural language pattern generation"
echo ""
echo "Press Enter to start..."
read

# Configuration
DEMO_DB="specql_demo_patterns"
DEMO_USER="specql_demo_user"
DEMO_PASSWORD="demo_password_123"

echo ""
echo "========================================="
echo "Phase 1: Database Setup"
echo "========================================="

echo "Setting up PostgreSQL database for demo..."

# Create database and user
sudo -u postgres psql << EOF
-- Create user if not exists
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '$DEMO_USER') THEN
       CREATE USER $DEMO_USER WITH PASSWORD '$DEMO_PASSWORD';
    END IF;
END
\$\$;

-- Drop database if exists (for clean demo)
DROP DATABASE IF EXISTS $DEMO_DB;

-- Create fresh database
CREATE DATABASE $DEMO_DB;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE $DEMO_DB TO $DEMO_USER;
EOF

echo "✓ Database '$DEMO_DB' created"

# Install extensions
echo "Installing pgvector and pg_trgm extensions..."
sudo -u postgres psql -d $DEMO_DB << EOF
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
EOF

echo "✓ Extensions installed"

# Set environment variable for demo
export SPECQL_DB_URL="postgresql://$DEMO_USER:$DEMO_PASSWORD@localhost/$DEMO_DB"
echo "✓ Database URL set: $SPECQL_DB_URL"

# Create schema and seed patterns
echo ""
echo "Creating pattern library schema..."
psql $SPECQL_DB_URL -f database/pattern_library_schema.sql

echo "Seeding baseline patterns..."
psql $SPECQL_DB_URL -f database/seed_patterns.sql

echo "✓ Pattern library initialized"

echo ""
echo "========================================="
echo "Phase 2: Embedding Generation"
echo "========================================="

echo "Generating embeddings for all patterns..."
echo "This may take a moment for the 5 baseline patterns..."

uv run specql embeddings generate

echo ""
echo "Testing pattern retrieval..."
echo "Query: 'approval workflow'"
uv run specql embeddings test-retrieval "approval workflow"

echo ""
echo "Query: 'audit trail'"
uv run specql embeddings test-retrieval "audit trail"

echo ""
echo "========================================="
echo "Phase 3: Pattern Discovery from SQL"
echo "========================================="

echo "Now let's discover patterns from existing SQL code..."
echo "We'll use a complex SQL function that should trigger pattern discovery."

# Create a demo SQL file with pattern-worthy logic
cat > demo_complex_function.sql << 'EOF'
-- Complex function with approval workflow pattern
CREATE OR REPLACE FUNCTION approve_document(
    p_document_id UUID,
    p_approver_id UUID,
    p_comments TEXT DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    v_current_status TEXT;
    v_approval_count INTEGER;
BEGIN
    -- Get current status
    SELECT status INTO v_current_status
    FROM documents
    WHERE id = p_document_id;

    IF v_current_status != 'pending' THEN
        RAISE EXCEPTION 'Document is not in pending status';
    END IF;

    -- Record approval
    INSERT INTO document_approvals (
        document_id,
        approver_id,
        approved_at,
        comments
    ) VALUES (
        p_document_id,
        p_approver_id,
        NOW(),
        p_comments
    );

    -- Check if we have enough approvals
    SELECT COUNT(*) INTO v_approval_count
    FROM document_approvals
    WHERE document_id = p_document_id;

    -- Update status if approved
    IF v_approval_count >= 2 THEN
        UPDATE documents
        SET status = 'approved',
            approved_at = NOW()
        WHERE id = p_document_id;
    END IF;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;
EOF

echo "Created demo SQL function with approval workflow logic."
echo "Running reverse engineering with pattern discovery..."

uv run specql reverse demo_complex_function.sql --discover-patterns

echo ""
echo "Checking for pattern suggestions..."
uv run specql patterns review-suggestions

echo ""
echo "Let's examine the discovered pattern in detail..."
# Get the first suggestion ID (assuming there's at least one)
SUGGESTION_ID=$(uv run specql patterns review-suggestions --limit 1 | grep -o "ID: [0-9]" | cut -d' ' -f2 || echo "1")

if [ -n "$SUGGESTION_ID" ]; then
    echo "Showing details for suggestion #$SUGGESTION_ID..."
    uv run specql patterns show $SUGGESTION_ID

    echo ""
    echo "Approving the discovered pattern..."
    echo "y" | uv run specql patterns approve $SUGGESTION_ID
else
    echo "No suggestions found - this is expected if pattern discovery didn't trigger"
fi

echo ""
echo "========================================="
echo "Phase 4: Natural Language Pattern Generation"
echo "========================================="

echo "Now let's generate patterns from natural language descriptions..."

echo ""
echo "Example 1: Simple validation pattern"
uv run specql patterns create-from-description \
    --description "Email validation with format checking and domain whitelist" \
    --category validation

echo ""
echo "Example 2: Complex workflow pattern"
uv run specql patterns create-from-description \
    --description "Multi-stage approval workflow with email notifications and escalation after 48 hours" \
    --category workflow

echo ""
echo "Example 3: Audit pattern"
uv run specql patterns create-from-description \
    --description "Complete audit trail for user actions with before/after values and change reasons" \
    --category audit

echo ""
echo "========================================="
echo "Phase 5: Pattern Library Statistics"
echo "========================================="

echo "Final pattern library status:"
uv run specql patterns stats

echo ""
echo "Checking total patterns in library:"
psql $SPECQL_DB_URL -c "SELECT COUNT(*) as total_patterns FROM pattern_library.domain_patterns;"

echo ""
echo "========================================="
echo "Demo Complete! 🎉"
echo "========================================="
echo ""
echo "What we've accomplished:"
echo "✓ Set up PostgreSQL + pgvector database"
echo "✓ Generated embeddings for pattern retrieval"
echo "✓ Tested semantic search capabilities"
echo "✓ Discovered patterns from legacy SQL"
echo "✓ Reviewed and approved AI-suggested patterns"
echo "✓ Generated new patterns from natural language"
echo ""
echo "The pattern library is now ready for production use!"
echo ""
echo "To clean up the demo database:"
echo "sudo -u postgres psql -c 'DROP DATABASE $DEMO_DB;'"
echo "sudo -u postgres psql -c 'DROP USER $DEMO_USER;'"
echo ""
echo "========================================="