#!/bin/bash

# SpecQL Demo GIF Creation Script
# This script helps record and convert terminal demos to optimized GIFs

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}SpecQL Demo GIF Creation Utility${NC}"
echo "=================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v asciinema &> /dev/null; then
    echo -e "${RED}✗${NC} asciinema not found"
    echo "  Install: pip install asciinema"
    exit 1
fi
echo -e "${GREEN}✓${NC} asciinema found"

CONVERTER=""
if command -v agg &> /dev/null; then
    CONVERTER="agg"
    echo -e "${GREEN}✓${NC} agg found (GIF converter)"
elif command -v asciicast2gif &> /dev/null; then
    CONVERTER="asciicast2gif"
    echo -e "${GREEN}✓${NC} asciicast2gif found (GIF converter)"
else
    echo -e "${RED}✗${NC} No GIF converter found"
    echo "  Install: cargo install agg  OR  npm install -g asciicast2gif"
    exit 1
fi

if ! command -v gifsicle &> /dev/null; then
    echo -e "${YELLOW}⚠${NC} gifsicle not found (optional but recommended)"
    echo "  Install: sudo apt-get install gifsicle"
    OPTIMIZE=false
else
    echo -e "${GREEN}✓${NC} gifsicle found (optimizer)"
    OPTIMIZE=true
fi

echo ""

# Function to record and convert
create_demo() {
    local demo_name=$1
    local demo_title=$2
    local demo_script=$3
    local cast_file="docs/demos/${demo_name}.cast"
    local gif_file="docs/demos/${demo_name}.gif"

    echo -e "${BLUE}Creating: ${demo_title}${NC}"
    echo "-------------------------------------------"

    # Check if script exists
    if [ ! -f "$demo_script" ]; then
        echo -e "${RED}✗${NC} Demo script not found: $demo_script"
        return 1
    fi

    # Record (interactive)
    echo -e "${YELLOW}→${NC} Recording terminal session..."
    echo "  When ready, run: ./${demo_script}"
    echo "  Press Ctrl+D when done"
    echo ""

    asciinema rec "$cast_file" --title "$demo_title" --idle-time-limit 2 --overwrite

    # Convert to GIF
    echo ""
    echo -e "${YELLOW}→${NC} Converting to GIF..."

    if [ "$CONVERTER" = "agg" ]; then
        agg "$cast_file" "$gif_file"
    else
        asciicast2gif "$cast_file" "$gif_file"
    fi

    # Optimize GIF
    if [ "$OPTIMIZE" = true ]; then
        echo -e "${YELLOW}→${NC} Optimizing GIF..."
        gifsicle -O3 "$gif_file" -o "${gif_file}.tmp"
        mv "${gif_file}.tmp" "$gif_file"
    fi

    # Check file size
    local size=$(du -h "$gif_file" | cut -f1)
    echo -e "${GREEN}✓${NC} Created: $gif_file ($size)"

    # Warn if too large
    local size_bytes=$(stat -f%z "$gif_file" 2>/dev/null || stat -c%s "$gif_file" 2>/dev/null)
    if [ "$size_bytes" -gt 2097152 ]; then
        echo -e "${YELLOW}⚠${NC} Warning: GIF is larger than 2MB"
        echo "  Consider reducing terminal size or demo length"
    fi

    echo ""
}

# Main menu
show_menu() {
    echo "Available demos:"
    echo "  1) Installation demo"
    echo "  2) Quickstart demo"
    echo "  3) Both demos"
    echo "  4) Just convert existing .cast files"
    echo "  q) Quit"
    echo ""
}

# Convert existing cast files
convert_existing() {
    echo -e "${BLUE}Converting existing .cast files...${NC}"
    echo ""

    for cast_file in docs/demos/*.cast; do
        if [ -f "$cast_file" ]; then
            local base_name=$(basename "$cast_file" .cast)
            local gif_file="docs/demos/${base_name}.gif"

            echo -e "${YELLOW}→${NC} Converting: $base_name"

            if [ "$CONVERTER" = "agg" ]; then
                agg "$cast_file" "$gif_file"
            else
                asciicast2gif "$cast_file" "$gif_file"
            fi

            if [ "$OPTIMIZE" = true ]; then
                echo -e "${YELLOW}→${NC} Optimizing..."
                gifsicle -O3 "$gif_file" -o "${gif_file}.tmp"
                mv "${gif_file}.tmp" "$gif_file"
            fi

            local size=$(du -h "$gif_file" | cut -f1)
            echo -e "${GREEN}✓${NC} Created: $gif_file ($size)"
            echo ""
        fi
    done
}

# Interactive mode
if [ $# -eq 0 ]; then
    while true; do
        show_menu
        read -p "Select option: " choice

        case $choice in
            1)
                create_demo "installation" "SpecQL Installation" "docs/demos/installation_demo.sh"
                ;;
            2)
                create_demo "quickstart" "SpecQL Quickstart - 10 Minutes" "docs/demos/quickstart_demo.sh"
                ;;
            3)
                create_demo "installation" "SpecQL Installation" "docs/demos/installation_demo.sh"
                create_demo "quickstart" "SpecQL Quickstart - 10 Minutes" "docs/demos/quickstart_demo.sh"
                ;;
            4)
                convert_existing
                ;;
            q|Q)
                echo "Goodbye!"
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid option${NC}"
                ;;
        esac
    done
else
    # Non-interactive mode
    case "$1" in
        installation)
            create_demo "installation" "SpecQL Installation" "docs/demos/installation_demo.sh"
            ;;
        quickstart)
            create_demo "quickstart" "SpecQL Quickstart - 10 Minutes" "docs/demos/quickstart_demo.sh"
            ;;
        convert)
            convert_existing
            ;;
        *)
            echo "Usage: $0 [installation|quickstart|convert]"
            exit 1
            ;;
    esac
fi

echo -e "${GREEN}=============================="
echo -e "Demo GIF creation complete!${NC}"
echo ""
echo "Output location: docs/demos/"
