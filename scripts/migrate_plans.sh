#!/bin/bash
# Migrate implementation plans to new structure

set -e

cd docs/implementation_plans

echo "Migrating implementation plans to new structure..."
echo ""

# 00_master_plan - Move from MASTER_PLAN/
echo "📁 00_master_plan (9 files)"
mv MASTER_PLAN/*.md 00_master_plan/ 2>/dev/null || true
mv 20251112_THREE_MONTH_MASTER_PLAN.md 00_master_plan/ 2>/dev/null || true
rmdir MASTER_PLAN 2>/dev/null || true

# 01_architecture
echo "📁 01_architecture (3 files)"
mv DATA_STORAGE_CONSOLIDATION_PLAN.md 01_architecture/ 2>/dev/null || true
mv 20251110_010952_REPOSITORY_CLEANUP_PLAN.md 01_architecture/ 2>/dev/null || true
mv 20251110_093102_repository_cleanup_and_docs_rewrite.md 01_architecture/ 2>/dev/null || true

# 02_infrastructure - Move from team_f_deployment/
echo "📁 02_infrastructure (8 files)"
mv team_f_deployment/*.md 02_infrastructure/ 2>/dev/null || true
mv SPECQL_POSTGRESQL_BOOTSTRAP.md 02_infrastructure/ 2>/dev/null || true
mv POSTGRESQL_GROK_IMPLEMENTATION_PLAN.md 02_infrastructure/ 2>/dev/null || true
rmdir team_f_deployment 2>/dev/null || true

# 03_frameworks
echo "📁 03_frameworks (9 files)"
mv 20251109_182139_EXECUTIVE_SUMMARY_CONFITURE_INTEGRATION.md 03_frameworks/ 2>/dev/null || true
mv 20251109_182139_REGISTRY_CLI_CONFITURE_INTEGRATION.md 03_frameworks/ 2>/dev/null || true
mv 20251109_232003_MISSING_FRAISEQL_SCALARS_IMPLEMENTATION_PLAN.md 03_frameworks/ 2>/dev/null || true
mv 20251108_121150_AUTOFRAISEQL_REQUIREMENTS.md 03_frameworks/ 2>/dev/null || true
mv 20251109_232003_STDLIB_INTEGRATION_PHASED_PLAN.md 03_frameworks/ 2>/dev/null || true
mv 20251109_182139_CONFITURE_FEATURE_REQUESTS.md 03_frameworks/ 2>/dev/null || true
mv 20251109_182139_CLEANUP_OPPORTUNITY_POST_CONFITURE.md 03_frameworks/ 2>/dev/null || true
mv 20251108_122613_AUTOFRAISEQL_PHASED_IMPLEMENTATION_PLAN.md 03_frameworks/ 2>/dev/null || true
mv 20251109_164216_CONFITURE_PATTERN_CORRECTION.md 03_frameworks/ 2>/dev/null || true

# 04_pattern_library
echo "📁 04_pattern_library (3 files)"
mv 20251112_universal_pattern_library.md 04_pattern_library/ 2>/dev/null || true
mv 20251112_three_tier_pattern_hierarchy.md 04_pattern_library/ 2>/dev/null || true
mv LLM_ENHANCED_PATTERN_LIBRARY_IMPLEMENTATION_PLAN.md 04_pattern_library/ 2>/dev/null || true

# 05_code_generation
echo "📁 05_code_generation (1 file)"
mv 20251112_universal_sql_expression_expansion.md 05_code_generation/ 2>/dev/null || true

# 06_reverse_engineering
echo "📁 06_reverse_engineering (5 files)"
mv X270_GROK_POC_IMPLEMENTATION_PLAN.md 06_reverse_engineering/ 2>/dev/null || true
mv 20251112_algorithmic_reverse_engineering_analysis.md 06_reverse_engineering/ 2>/dev/null || true
mv 20251112_reverse_engineering_and_comparison_cli.md 06_reverse_engineering/ 2>/dev/null || true
mv 20251112_local_llm_for_reverse_engineering.md 06_reverse_engineering/ 2>/dev/null || true
mv 20251112_reverse_engineering_balanced_assessment.md 06_reverse_engineering/ 2>/dev/null || true

# 07_numbering_systems
echo "📁 07_numbering_systems (4 files)"
mv 20251112_SEVENTH_DIGIT_UNIFIED_NUMBERING.md 07_numbering_systems/ 2>/dev/null || true
mv 20251112_SIX_DIGIT_UNIFIED_NUMBERING.md 07_numbering_systems/ 2>/dev/null || true
mv 20251110_093102_issue_001_hex_hierarchical_explicit_table_codes.md 07_numbering_systems/ 2>/dev/null || true
mv 20251109_111921_IDENTIFIER_CALCULATION_PATTERNS.md 07_numbering_systems/ 2>/dev/null || true

# 08_testing - Move from testing-and-seed-generation/
echo "📁 08_testing (10 files)"
mv testing-and-seed-generation/*.md 08_testing/ 2>/dev/null || true
mv 20251109_111921_SCHEMA_REGISTRY_TEST_FIX_PLAN.md 08_testing/ 2>/dev/null || true
mv TEST_FAILURES_FIX_PLAN.md 08_testing/ 2>/dev/null || true
mv 20251110_005926_TEST_SUITE_FIX_PHASED_PLAN.md 08_testing/ 2>/dev/null || true
rmdir testing-and-seed-generation 2>/dev/null || true

# 09_naming_conventions - Move from naming-conventions-registry/
echo "📁 09_naming_conventions (2 files)"
mv naming-conventions-registry/*.md 09_naming_conventions/ 2>/dev/null || true
rmdir naming-conventions-registry 2>/dev/null || true

# 10_phases_6_7_8
echo "📁 10_phases_6_7_8 (1 file)"
mv PHASES_6_7_8_DETAILED_PLAN.md 10_phases_6_7_8/ 2>/dev/null || true

# Move remaining files to archive (review these manually)
echo "📁 archive (remaining files)"
mv *.md archive/completed/ 2>/dev/null || true

echo ""
echo "✅ Migration complete!"
echo ""
echo "Summary:"
ls -d */| while read dir; do
    count=$(find "$dir" -name "*.md" -type f | wc -l)
    echo "  $dir - $count files"
done
