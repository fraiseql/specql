#!/bin/bash
# Regenerate all benchmark datasets

set -e

echo "🔄 Regenerating benchmark datasets..."

python tests/performance/benchmark_data_generator.py --entities 10 --output tests/performance/datasets/benchmark_010.sql
echo "✅ Generated 10-entity dataset"

python tests/performance/benchmark_data_generator.py --entities 50 --output tests/performance/datasets/benchmark_050.sql
echo "✅ Generated 50-entity dataset"

python tests/performance/benchmark_data_generator.py --entities 100 --output tests/performance/datasets/benchmark_100.sql
echo "✅ Generated 100-entity dataset"

python tests/performance/benchmark_data_generator.py --entities 500 --output tests/performance/datasets/benchmark_500.sql
echo "✅ Generated 500-entity dataset"

python tests/performance/benchmark_data_generator.py --entities 1000 --output tests/performance/datasets/benchmark_1000.sql
echo "✅ Generated 1000-entity dataset"

echo "🎉 All datasets regenerated successfully"