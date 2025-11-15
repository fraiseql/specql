#!/bin/bash

# SpecQL Diagram Export Script
# Exports Mermaid diagrams to PNG format

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}SpecQL Diagram Export Utility${NC}"
echo "=============================="
echo ""

# Check for mmdc
if ! command -v mmdc &> /dev/null; then
    echo -e "${RED}Error: mermaid-cli (mmdc) not found${NC}"
    echo "Install with: npm install -g @mermaid-js/mermaid-cli"
    exit 1
fi

# Create Puppeteer config for system Chromium
PUPPETEER_CONFIG="/tmp/.puppeteerrc.json"
cat > "$PUPPETEER_CONFIG" << 'EOF'
{
  "executablePath": "/usr/bin/chromium"
}
EOF

echo -e "${GREEN}✓${NC} Puppeteer config created"

# Create output directories
mkdir -p docs/04_architecture/diagrams
mkdir -p docs/02_guides/diagrams

echo -e "${GREEN}✓${NC} Output directories ready"
echo ""

# Function to export diagram
export_diagram() {
    local input_file=$1
    local output_file=$2
    local width=$3
    local height=$4
    local name=$5

    echo -e "${BLUE}Exporting:${NC} $name"

    if [ ! -f "$input_file" ]; then
        echo -e "${RED}  Error: Input file not found: $input_file${NC}"
        return 1
    fi

    cd "$(dirname "$input_file")"
    mmdc -i "$(basename "$input_file")" \
         -o "$output_file" \
         -w "$width" \
         -H "$height" \
         -b transparent \
         --puppeteerConfigFile "$PUPPETEER_CONFIG" \
         2>&1 | grep -v "Store is a function" || true

    if [ -f "$output_file" ]; then
        size=$(ls -lh "$output_file" | awk '{print $5}')
        echo -e "${GREEN}  ✓${NC} Created: $output_file ($size)"
        return 0
    else
        echo -e "${RED}  ✗${NC} Failed to create: $output_file"
        return 1
    fi
}

# Export architecture diagrams
echo "Architecture Diagrams"
echo "---------------------"

export_diagram \
    "/tmp/diagram1_high_level_overview.mmd" \
    "$(pwd)/docs/04_architecture/diagrams/high_level_overview.png" \
    1200 800 \
    "High-Level Overview"

export_diagram \
    "/tmp/diagram2_code_generation_flow.mmd" \
    "$(pwd)/docs/04_architecture/diagrams/code_generation_flow.png" \
    1200 600 \
    "Code Generation Flow"

export_diagram \
    "/tmp/diagram3_reverse_engineering_flow.mmd" \
    "$(pwd)/docs/04_architecture/diagrams/reverse_engineering_flow.png" \
    1200 600 \
    "Reverse Engineering Flow"

export_diagram \
    "/tmp/diagram4_trinity_pattern.mmd" \
    "$(pwd)/docs/04_architecture/diagrams/trinity_pattern.png" \
    1000 400 \
    "Trinity Pattern"

export_diagram \
    "/tmp/diagram5_fraiseql_integration.mmd" \
    "$(pwd)/docs/04_architecture/diagrams/fraiseql_integration.png" \
    1200 600 \
    "FraiseQL Integration"

echo ""
echo "Workflow Diagrams"
echo "-----------------"

export_diagram \
    "/tmp/diagram6_development_workflow.mmd" \
    "$(pwd)/docs/02_guides/diagrams/development_workflow.png" \
    1200 600 \
    "Development Workflow"

export_diagram \
    "/tmp/diagram7_migration_workflow.mmd" \
    "$(pwd)/docs/02_guides/diagrams/migration_workflow.png" \
    1400 500 \
    "Migration Workflow"

echo ""
echo -e "${GREEN}=============================="
echo -e "All diagrams exported successfully!${NC}"
echo ""
echo "Output locations:"
echo "  • docs/04_architecture/diagrams/"
echo "  • docs/02_guides/diagrams/"
