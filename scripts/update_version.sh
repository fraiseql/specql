#!/bin/bash
# Update version in pyproject.toml and create git tag

if [ -z "$1" ]; then
    echo "Usage: ./update_version.sh <version>"
    echo "Example: ./update_version.sh 0.5.0"
    exit 1
fi

NEW_VERSION="$1"

# Update pyproject.toml
sed -i.bak "s/version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml
rm pyproject.toml.bak

# Update CHANGELOG.md (add date)
TODAY=$(date +%Y-%m-%d)
sed -i.bak "s/\[Unreleased\]/[$NEW_VERSION] - $TODAY/" CHANGELOG.md
rm CHANGELOG.md.bak

echo "✅ Updated version to $NEW_VERSION"
echo "Next steps:"
echo "  1. Review changes: git diff"
echo "  2. Commit: git commit -am 'chore: bump version to $NEW_VERSION'"
echo "  3. Tag: git tag -a v$NEW_VERSION -m 'Release v$NEW_VERSION'"
echo "  4. Push: git push && git push --tags"