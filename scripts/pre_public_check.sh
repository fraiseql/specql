#!/bin/bash
set -e

echo "🔍 Running Pre-Public Release Checks..."
echo ""

# Track issues
WARNINGS=0
ERRORS=0

# Security checks
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 SECURITY: Checking for sensitive patterns..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if rg -i "password\s*=|secret\s*=|api_key\s*=|token\s*=" --type yaml --type py --type-not sql 2>/dev/null; then
    echo "⚠️  WARNING: Potential hardcoded secrets found!"
    WARNINGS=$((WARNINGS + 1))
else
    echo "✅ No obvious secrets detected"
fi

echo ""
if rg "@evolution-digitale\.fr" --type py --type yaml --type-not sql 2>/dev/null; then
    echo "⚠️  WARNING: Internal email references found (review if appropriate)"
    WARNINGS=$((WARNINGS + 1))
else
    echo "✅ No internal email references in code"
fi

# Check for TODOs
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 CODE QUALITY: Checking for TODOs/FIXMEs..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TODO_COUNT=$(rg "TODO|FIXME|XXX|HACK" --type py 2>/dev/null | wc -l || echo "0")
if [ "$TODO_COUNT" -gt 0 ]; then
    echo "⚠️  WARNING: Found $TODO_COUNT TODO/FIXME comments"
    echo "   Review and resolve before public release:"
    rg "TODO|FIXME|XXX|HACK" --type py 2>/dev/null | head -10
    WARNINGS=$((WARNINGS + 1))
else
    echo "✅ No TODO/FIXME comments found"
fi

# Code quality
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 TESTS: Running test suite..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if make test > /tmp/specql_test_output.log 2>&1; then
    echo "✅ All tests passed"
else
    echo "❌ ERROR: Tests failed!"
    echo "   See /tmp/specql_test_output.log for details"
    ERRORS=$((ERRORS + 1))
fi

# Code style
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎨 CODE STYLE: Checking linting..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if make lint > /tmp/specql_lint_output.log 2>&1; then
    echo "✅ Linting passed"
else
    echo "❌ ERROR: Linting issues found!"
    cat /tmp/specql_lint_output.log
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 TYPE CHECKING: Running mypy..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if make typecheck > /tmp/specql_typecheck_output.log 2>&1; then
    echo "✅ Type checking passed"
else
    echo "⚠️  WARNING: Type checking issues found"
    cat /tmp/specql_typecheck_output.log
    WARNINGS=$((WARNINGS + 1))
fi

# Documentation checks
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 DOCUMENTATION: Checking required files..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! test -f README.md; then
    echo "❌ ERROR: README.md missing!"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ README.md exists"
fi

if ! test -f LICENSE; then
    echo "⚠️  WARNING: No LICENSE file!"
    WARNINGS=$((WARNINGS + 1))
else
    echo "✅ LICENSE file exists"
fi

if ! test -f CHANGELOG.md; then
    echo "⚠️  WARNING: No CHANGELOG.md file!"
    WARNINGS=$((WARNINGS + 1))
else
    echo "✅ CHANGELOG.md exists"
fi

# Version consistency
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🏷️  VERSION: Checking version consistency..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! test -f VERSION; then
    echo "❌ ERROR: VERSION file missing!"
    ERRORS=$((ERRORS + 1))
else
    VERSION=$(cat VERSION)
    PYPROJECT_VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)

    if [ "$VERSION" != "$PYPROJECT_VERSION" ]; then
        echo "❌ ERROR: Version mismatch!"
        echo "   VERSION file: $VERSION"
        echo "   pyproject.toml: $PYPROJECT_VERSION"
        ERRORS=$((ERRORS + 1))
    else
        echo "✅ Version consistent: $VERSION"
    fi
fi

# Git checks
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔀 GIT: Checking repository state..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! git diff-index --quiet HEAD --; then
    echo "⚠️  WARNING: Uncommitted changes detected"
    WARNINGS=$((WARNINGS + 1))
else
    echo "✅ No uncommitted changes"
fi

# .gitignore check
if ! test -f .gitignore; then
    echo "⚠️  WARNING: No .gitignore file!"
    WARNINGS=$((WARNINGS + 1))
else
    echo "✅ .gitignore exists"
fi

# Check for common files that shouldn't be committed
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🗑️  CLEANUP: Checking for unwanted files..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

UNWANTED_COUNT=0

if find . -name "*.pyc" -o -name ".DS_Store" | grep -q .; then
    echo "⚠️  WARNING: Found build artifacts or OS files"
    find . -name "*.pyc" -o -name ".DS_Store" | head -5
    UNWANTED_COUNT=$((UNWANTED_COUNT + 1))
fi

if find . -type d -name "__pycache__" | grep -q .; then
    echo "⚠️  WARNING: Found __pycache__ directories"
    UNWANTED_COUNT=$((UNWANTED_COUNT + 1))
fi

if [ "$UNWANTED_COUNT" -eq 0 ]; then
    echo "✅ No unwanted files detected"
else
    WARNINGS=$((WARNINGS + 1))
fi

# GitHub Actions check
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🤖 GITHUB: Checking workflows..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if test -d .github/workflows; then
    WORKFLOW_COUNT=$(find .github/workflows -name "*.yml" | wc -l)
    echo "✅ Found $WORKFLOW_COUNT workflow files"
else
    echo "⚠️  INFO: No GitHub Actions workflows"
fi

# Final summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Errors:   $ERRORS"
echo "Warnings: $WARNINGS"
echo ""

if [ $ERRORS -gt 0 ]; then
    echo "❌ FAILED: $ERRORS critical issues must be fixed before public release"
    echo ""
    echo "📝 Next steps:"
    echo "   1. Review errors above and fix issues"
    echo "   2. Run this script again"
    echo "   3. Review manual checklist: .github/PRE_PUBLIC_CLEANUP.md"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo "⚠️  PASSED WITH WARNINGS: $WARNINGS items should be reviewed"
    echo ""
    echo "📝 Next steps:"
    echo "   1. Review warnings above"
    echo "   2. Review manual checklist: .github/PRE_PUBLIC_CLEANUP.md"
    echo "   3. Run 'bash scripts/pre_public_check.sh' again after fixes"
    exit 0
else
    echo "✅ ALL CHECKS PASSED!"
    echo ""
    echo "📝 Next steps:"
    echo "   1. Review manual checklist: .github/PRE_PUBLIC_CLEANUP.md"
    echo "   2. Test fresh installation in clean environment"
    echo "   3. Get human review before making repository public"
    echo "   4. Consider bumping to v1.0.0 for public release"
    exit 0
fi
