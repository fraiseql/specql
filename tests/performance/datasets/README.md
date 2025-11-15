# Benchmark Datasets

This directory contains pre-generated benchmark datasets for performance testing.

## Datasets

| File | Entities | Fields | Foreign Keys | Actions | Purpose |
|------|----------|--------|--------------|---------|---------|
| `benchmark_010.sql` | 10 | ~118 | ~9 | ~27 | Quick iteration |
| `benchmark_050.sql` | 50 | ~571 | ~42 | ~152 | Medium-scale testing |
| `benchmark_100.sql` | 100 | ~1,124 | ~94 | ~300 | **Standard benchmark** |
| `benchmark_500.sql` | 500 | ~5,696 | ~451 | ~1,552 | Large-scale testing |
| `benchmark_1000.sql` | 1000 | ~11,338 | ~908 | ~3,094 | Extreme stress test |

## Regenerating Datasets

To regenerate (e.g., after improving generator):

```bash
./regenerate_datasets.sh
```

## Dataset Characteristics

All datasets include:
- 80% Trinity pattern entities
- 90% audit fields
- 20% deduplication fields
- 30% relationship density (avg 0.9 FKs per entity)
- 3 actions per entity (average)

These percentages mirror real-world SpecQL usage patterns.</content>
</xai:function_call">The script will regenerate all datasets with the current generator version.