# FraiseQL Server - Quick Fix Guide

**TL;DR**: The PyPI package is missing vector modules. Install from source instead.

---

## Problem

Team struggling to get FraiseQL server working with vector search because the pip-installed package (`fraiseql==1.5.0`) doesn't include vector modules.

## Solution

Install FraiseQL from local source code where all vector features exist.

---

## Quick Fix (5 minutes)

### Step 1: Install from Source

```bash
cd ~/code/specql

# Remove PyPI package
pip uninstall fraiseql

# Install from local FraiseQL source
pip install -e ~/code/fraiseql
```

### Step 2: Verify Installation

```bash
python -c "from fraiseql.types.scalars.vector import VectorScalar; print('✓ Vector support works!')"
```

Expected output: `✓ Vector support works!`

### Step 3: Update Server Config

Edit `src/presentation/graphql/server.py`:

```python
import os
from fraiseql.fastapi import create_fraiseql_app, FraiseQLConfig

def create_app():
    config = FraiseQLConfig(
        database_url=os.getenv("DATABASE_URL", "postgresql://specql:specql@localhost:5432/specql"),
        auto_camel_case=True,
    )

    app = create_fraiseql_app(
        types=[],
        queries=[],
        config=config,
        auto_discover=True,  # ← Auto-discovers vector columns!
    )
    return app

app = create_app()
```

### Step 4: Start Server

```bash
DATABASE_URL="postgresql://specql:specql@localhost:5432/specql" \
  python -m uvicorn src.presentation.graphql.server:app --host 127.0.0.1 --port 4000
```

### Step 5: Test in Browser

Open: http://localhost:4000/graphql

Run this query:
```graphql
query TestVectorFilter {
  __type(name: "DomainPatternWhereInput") {
    inputFields {
      name
      type { name }
    }
  }
}
```

Should see `embedding` field with `VectorFilter` type!

---

## What This Fixes

✅ FraiseQL now has vector support
✅ Auto-discovers vector columns from PostgreSQL
✅ Provides GraphQL `VectorFilter` with 6 distance operators
✅ Server starts and works correctly

---

## Why This Happened

The PyPI package `fraiseql==1.5.0` is compiled and doesn't export Python vector modules. The source code at `~/code/fraiseql/` has everything but needs to be installed locally.

---

## Next Steps

1. ✅ Server works with vector search
2. Simplify SpecQL generators (remove custom functions)
3. Update pattern library to use GraphQL
4. Test end-to-end semantic search

See full guide: `docs/implementation_plans/FRAISEQL_SERVER_INTEGRATION_GUIDE.md`

---

**Time to fix**: 5 minutes
**Status**: Ready to implement
**Impact**: Unblocks FraiseQL server development
