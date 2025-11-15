#!/bin/bash

# List all markdown files
find docs -name "*.md" -type f | sort > /tmp/all_docs.txt

# Already audited (8 files)
AUDITED=(
    "docs/00_getting_started/README.md"
    "docs/00_getting_started/QUICKSTART.md"
    "docs/README.md"
    "docs/06_examples/CRM_SYSTEM_COMPLETE.md"
    "docs/06_examples/ECOMMERCE_SYSTEM.md"
    "docs/06_examples/simple_contact/README.md"
    "docs/03_reference/cli/command_reference.md"
    "docs/03_reference/yaml/complete_reference.md"
)

echo "# Documentation Audit - Remaining Files"
echo ""
echo "Total docs: $(wc -l < /tmp/all_docs.txt)"
echo "Already audited: ${#AUDITED[@]}"
echo "Remaining: $(($(wc -l < /tmp/all_docs.txt) - ${#AUDITED[@]}))"
echo ""
echo "## To Audit:"
echo ""

while IFS= read -r file; do
    skip=false
    for audited in "${AUDITED[@]}"; do
        if [ "$file" = "$audited" ]; then
            skip=true
            break
        fi
    done

    if [ "$skip" = false ]; then
        echo "- [ ] $file"
    fi
done < /tmp/all_docs.txt