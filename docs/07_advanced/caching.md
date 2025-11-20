# Caching Guide

> **Multi-layer caching strategy for SpecQL applications—reduce database load by 95%**

## Overview

Effective caching requires multiple layers:
- ✅ **Application Cache** (Redis) - Query results, sessions
- ✅ **Database Cache** (PostgreSQL) - Query plans, shared buffers
- ✅ **CDN Cache** - Static GraphQL queries
- ✅ **Browser Cache** - Client-side Apollo cache

**Goal**: Sub-10ms response times for cached data

---

## Quick Start

### Redis Setup

```bash
# Install Redis
docker run -d -p 6379:6379 redis:7-alpine

# Install Node.js client
npm install ioredis
```

**Basic usage**:
```typescript
import Redis from 'ioredis';

const redis = new Redis({
  host: 'localhost',
  port: 6379,
});

// Cache a query result
await redis.setex(
  'contacts:qualified',
  300,  // 5 minute TTL
  JSON.stringify(contacts)
);

// Retrieve cached result
const cached = await redis.get('contacts:qualified');
if (cached) {
  return JSON.parse(cached);
}
```

---

## Application-Level Caching

### Cache Strategy Patterns

#### 1. Cache-Aside (Lazy Loading)

**Most common pattern**:

```typescript
async function getContact(contactId: string) {
  const cacheKey = `contact:${contactId}`;

  // Try cache first
  const cached = await redis.get(cacheKey);
  if (cached) {
    return JSON.parse(cached);
  }

  // Cache miss: fetch from database
  const contact = await db.query(
    'SELECT * FROM crm.tb_contact WHERE id = $1',
    [contactId]
  );

  // Store in cache (5 min TTL)
  await redis.setex(cacheKey, 300, JSON.stringify(contact));

  return contact;
}
```

**Benefits**:
- Simple to implement
- Only caches requested data
- Resilient to cache failures

**Drawbacks**:
- Initial request is slow (cache miss)
- Potential cache stampede

---

#### 2. Write-Through

**Update cache on write**:

```typescript
async function updateContact(contactId: string, updates: any) {
  // Update database
  const updatedContact = await db.query(
    'UPDATE crm.tb_contact SET ... WHERE id = $1 RETURNING *',
    [contactId]
  );

  // Update cache immediately
  const cacheKey = `contact:${contactId}`;
  await redis.setex(cacheKey, 300, JSON.stringify(updatedContact));

  return updatedContact;
}
```

**Benefits**:
- Cache always consistent with DB
- No cache stampede
- Read performance optimal

**Drawbacks**:
- Extra write overhead
- Cache populated even if rarely read

---

#### 3. Write-Behind (Lazy Write)

**Defer writes to database**:

```typescript
async function updateContactCached(contactId: string, updates: any) {
  const cacheKey = `contact:${contactId}`;

  // Update cache immediately
  const cachedContact = await redis.get(cacheKey);
  const contact = cachedContact ? JSON.parse(cachedContact) : {};
  const updatedContact = { ...contact, ...updates };

  await redis.setex(cacheKey, 300, JSON.stringify(updatedContact));

  // Queue database write (async)
  await queue.add('update-contact', { contactId, updates });

  return updatedContact;
}
```

**Benefits**:
- Fast writes
- Batch database updates
- Reduced DB load

**Drawbacks**:
- Risk of data loss (if cache fails)
- Eventual consistency

---

### Cache Invalidation

#### Time-Based Invalidation

**Set TTL based on data volatility**:

```typescript
// Frequently changing data (short TTL)
await redis.setex('dashboard:stats', 60, JSON.stringify(stats));  // 1 min

// Slowly changing data (medium TTL)
await redis.setex('product:details', 3600, JSON.stringify(product));  // 1 hour

// Rarely changing data (long TTL)
await redis.setex('category:tree', 86400, JSON.stringify(categories));  // 24 hours
```

---

#### Event-Based Invalidation

**Invalidate on mutation**:

```typescript
// SpecQL action with cache invalidation
async function qualifyLead(contactId: string) {
  // Execute action
  const result = await db.query(
    'SELECT * FROM app.qualify_lead($1)',
    [contactId]
  );

  if (result.status === 'success') {
    // Invalidate related caches
    await invalidateContactCache(contactId);
    await invalidateLeadListCache();
  }

  return result;
}

async function invalidateContactCache(contactId: string) {
  await redis.del(`contact:${contactId}`);
}

async function invalidateLeadListCache() {
  // Invalidate all lead-related lists
  const keys = await redis.keys('contacts:lead:*');
  if (keys.length > 0) {
    await redis.del(...keys);
  }
}
```

---

#### Tag-Based Invalidation

**Group related cache entries**:

```typescript
// Cache with tags
async function cacheWithTags(key: string, value: any, ttl: number, tags: string[]) {
  // Store value
  await redis.setex(key, ttl, JSON.stringify(value));

  // Store tags
  for (const tag of tags) {
    await redis.sadd(`tag:${tag}`, key);
    await redis.expire(`tag:${tag}`, ttl);
  }
}

// Invalidate by tag
async function invalidateByTag(tag: string) {
  const keys = await redis.smembers(`tag:${tag}`);
  if (keys.length > 0) {
    await redis.del(...keys);
  }
  await redis.del(`tag:${tag}`);
}

// Usage
await cacheWithTags(
  'contact:550e8400-...',
  contact,
  300,
  ['contact', 'company:acme', 'status:lead']
);

// Invalidate all contacts for company ACME
await invalidateByTag('company:acme');
```

---

## Database-Level Caching

### PostgreSQL Shared Buffers

**Tune shared_buffers** (PostgreSQL's internal cache):

```sql
-- postgresql.conf
shared_buffers = 4GB          -- 25% of available RAM
effective_cache_size = 12GB   -- 75% of available RAM
```

**Check cache hit ratio**:
```sql
SELECT
  'index hit rate' AS name,
  (sum(idx_blks_hit)) / nullif(sum(idx_blks_hit + idx_blks_read), 0) AS ratio
FROM pg_stat_user_indexes
UNION ALL
SELECT
  'table hit rate' AS name,
  sum(heap_blks_hit) / nullif(sum(heap_blks_hit) + sum(heap_blks_read), 0) AS ratio
FROM pg_stat_user_tables;
```

**Target**: 99%+ hit ratio

---

### Materialized Views

**Cache expensive aggregations**:

```yaml
table_view: OrderSummaryByCustomer
schema: sales
refresh: hourly

query: |
  SELECT
    fk_customer,
    COUNT(*) as total_orders,
    SUM(total_amount) as total_spent,
    AVG(total_amount) as avg_order_value,
    MAX(created_at) as last_order_date
  FROM sales.tb_order
  WHERE status != 'cancelled'
  GROUP BY fk_customer
```

**Generated SQL**:
```sql
CREATE MATERIALIZED VIEW sales.tv_order_summary_by_customer AS
SELECT ...;

CREATE UNIQUE INDEX ON sales.tv_order_summary_by_customer (fk_customer);

-- Refresh function
CREATE FUNCTION sales.refresh_order_summary()
RETURNS VOID AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY sales.tv_order_summary_by_customer;
END;
$$ LANGUAGE plpgsql;
```

**Refresh schedule** (using pg_cron):
```sql
-- Install pg_cron extension
CREATE EXTENSION pg_cron;

-- Schedule hourly refresh
SELECT cron.schedule(
  'refresh-order-summary',
  '0 * * * *',  -- Every hour
  'SELECT sales.refresh_order_summary()'
);
```

---

### Query Result Caching

**Cache at database level** (using table):

```sql
CREATE TABLE core.query_cache (
    cache_key TEXT PRIMARY KEY,
    result JSONB NOT NULL,
    cached_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_query_cache_expires ON core.query_cache (expires_at);

-- Auto-cleanup expired entries
CREATE FUNCTION core.cleanup_query_cache()
RETURNS VOID AS $$
BEGIN
    DELETE FROM core.query_cache
    WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Schedule cleanup (every 5 minutes)
SELECT cron.schedule(
    'cleanup-query-cache',
    '*/5 * * * *',
    'SELECT core.cleanup_query_cache()'
);
```

**Usage in actions**:
```sql
CREATE FUNCTION app.get_dashboard_stats()
RETURNS JSONB AS $$
DECLARE
    v_cache_key TEXT := 'dashboard:stats';
    v_cached JSONB;
BEGIN
    -- Check cache
    SELECT result INTO v_cached
    FROM core.query_cache
    WHERE cache_key = v_cache_key
      AND expires_at > NOW();

    IF v_cached IS NOT NULL THEN
        RETURN v_cached;
    END IF;

    -- Cache miss: compute result
    v_cached := (
        SELECT json_build_object(
            'total_orders', COUNT(*),
            'total_revenue', SUM(total_amount),
            'avg_order_value', AVG(total_amount)
        )
        FROM sales.tb_order
        WHERE created_at > NOW() - INTERVAL '30 days'
    );

    -- Store in cache (5 min TTL)
    INSERT INTO core.query_cache (cache_key, result, expires_at)
    VALUES (v_cache_key, v_cached, NOW() + INTERVAL '5 minutes')
    ON CONFLICT (cache_key) DO UPDATE
    SET result = EXCLUDED.result,
        cached_at = NOW(),
        expires_at = EXCLUDED.expires_at;

    RETURN v_cached;
END;
$$ LANGUAGE plpgsql;
```

---

## CDN Caching

### Cache GraphQL Responses

**Cloudflare Workers example**:

```typescript
// cloudflare-worker.js
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  const url = new URL(request.url);

  // Only cache GET requests
  if (request.method !== 'GET') {
    return fetch(request);
  }

  // Check if persisted query
  const queryId = url.searchParams.get('id');
  if (!queryId) {
    return fetch(request);
  }

  // Cache key
  const cacheKey = `graphql:${queryId}`;

  // Try CDN cache
  const cache = caches.default;
  let response = await cache.match(cacheKey);

  if (!response) {
    // Cache miss: fetch from origin
    response = await fetch(request);

    // Cache for 1 hour if successful
    if (response.ok) {
      response = new Response(response.body, response);
      response.headers.set('Cache-Control', 'public, max-age=3600');
      await cache.put(cacheKey, response.clone());
    }
  }

  return response;
}
```

---

## Client-Side Caching

### Apollo Client Cache

**Configure normalized cache**:

```typescript
import { InMemoryCache } from '@apollo/client';

const cache = new InMemoryCache({
  typePolicies: {
    Query: {
      fields: {
        contacts: {
          // Merge paginated results
          keyArgs: ['where', 'orderBy'],
          merge(existing = [], incoming) {
            return [...existing, ...incoming];
          },
        },
      },
    },
    Contact: {
      // Cache key strategy
      keyFields: ['id'],
      fields: {
        company: {
          // Always fetch company (not cached separately)
          merge: false,
        },
      },
    },
  },
});

const client = new ApolloClient({
  uri: 'http://localhost:5000/graphql',
  cache,
});
```

---

### Impact-Based Cache Updates

**Use SpecQL impact metadata**:

```typescript
const [qualifyLead] = useMutation(QUALIFY_LEAD, {
  update: (cache, { data }) => {
    if (data.qualifyLead.status === 'success') {
      // Impact metadata tells us what changed
      data.qualifyLead._meta.impacts.forEach(impact => {
        if (impact.entity === 'Contact' && impact.operation === 'UPDATE') {
          // Update cache for modified contact
          cache.writeFragment({
            id: `Contact:${impact.ids[0]}`,
            fragment: gql`
              fragment UpdatedContact on Contact {
                status
                updatedAt
              }
            `,
            data: {
              status: 'qualified',
              updatedAt: new Date().toISOString(),
            },
          });

          // Evict lead list queries (status changed)
          cache.evict({
            fieldName: 'contacts',
            args: { where: { status: { eq: 'lead' } } },
          });
        }
      });

      cache.gc();
    }
  },
});
```

---

## Cache Warming

### Pre-populate Cache

**Warm cache on deployment**:

```typescript
async function warmCache() {
  console.log('Warming cache...');

  // Pre-fetch frequently accessed data
  const queries = [
    { key: 'products:featured', query: 'SELECT * FROM catalog.tb_product WHERE featured = true' },
    { key: 'categories:tree', query: 'SELECT * FROM catalog.tv_category_tree' },
    { key: 'dashboard:stats', query: 'SELECT * FROM sales.tv_dashboard_stats' },
  ];

  for (const { key, query } of queries) {
    const result = await db.query(query);
    await redis.setex(key, 3600, JSON.stringify(result));
    console.log(`Cached ${key}`);
  }

  console.log('Cache warmed successfully');
}

// Run on startup
warmCache().catch(console.error);
```

---

### Progressive Cache Warming

**Warm cache based on access patterns**:

```typescript
// Track cache misses
async function getCached(key: string, fetcher: () => Promise<any>) {
  const cached = await redis.get(key);

  if (cached) {
    return JSON.parse(cached);
  }

  // Log cache miss
  await redis.incr(`cache_miss:${key}`);

  // Fetch and cache
  const value = await fetcher();
  await redis.setex(key, 300, JSON.stringify(value));

  return value;
}

// Warm frequently missed keys
async function warmFrequentMisses() {
  const keys = await redis.keys('cache_miss:*');

  const misses = await Promise.all(
    keys.map(async (key) => ({
      key: key.replace('cache_miss:', ''),
      count: parseInt(await redis.get(key) || '0'),
    }))
  );

  // Sort by miss count
  misses.sort((a, b) => b.count - a.count);

  // Warm top 10
  for (const miss of misses.slice(0, 10)) {
    console.log(`Warming ${miss.key} (${miss.count} misses)`);
    // TODO: Fetch and cache
  }
}
```

---

## Monitoring Cache Performance

### Redis Metrics

```bash
# Connect to Redis CLI
redis-cli

# Get cache stats
INFO stats

# Key metrics:
# - keyspace_hits: Cache hits
# - keyspace_misses: Cache misses
# - evicted_keys: Keys evicted (memory pressure)
# - expired_keys: Keys expired (TTL)

# Calculate hit ratio
redis-cli INFO stats | grep keyspace
# keyspace_hits:1000000
# keyspace_misses:50000
# Hit ratio: 1000000 / (1000000 + 50000) = 95.2%
```

**Target**: 95%+ hit ratio

---

### Application Metrics

```typescript
import { Counter, Histogram } from 'prom-client';

const cacheHits = new Counter({
  name: 'cache_hits_total',
  help: 'Total cache hits',
  labelNames: ['cache_key'],
});

const cacheMisses = new Counter({
  name: 'cache_misses_total',
  help: 'Total cache misses',
  labelNames: ['cache_key'],
});

const cacheDuration = new Histogram({
  name: 'cache_operation_duration_seconds',
  help: 'Cache operation duration',
  labelNames: ['operation', 'cache_key'],
});

async function getCachedWithMetrics(key: string, fetcher: () => Promise<any>) {
  const timer = cacheDuration.startTimer({ operation: 'get', cache_key: key });

  const cached = await redis.get(key);

  if (cached) {
    cacheHits.inc({ cache_key: key });
    timer();
    return JSON.parse(cached);
  }

  cacheMisses.inc({ cache_key: key });

  const value = await fetcher();
  await redis.setex(key, 300, JSON.stringify(value));

  timer();
  return value;
}
```

---

## Best Practices

### ✅ DO

1. **Cache immutable data** aggressively (long TTL)
2. **Use tag-based invalidation** for complex dependencies
3. **Monitor hit ratio** (target 95%+)
4. **Set appropriate TTLs** based on data volatility
5. **Warm cache** on deployment
6. **Use Redis pipelining** for batch operations
7. **Implement circuit breakers** (fallback if cache fails)

---

### ❌ DON'T

1. **Don't cache user-specific data** in shared cache
2. **Don't set infinite TTLs** (always expire eventually)
3. **Don't ignore cache failures** (implement fallbacks)
4. **Don't cache large objects** (>1MB) without compression
5. **Don't skip monitoring** (blind caching is dangerous)

---

## Caching Checklist

### Development

- [ ] Cache strategy defined (cache-aside, write-through, etc.)
- [ ] Invalidation strategy implemented
- [ ] TTLs set based on data volatility
- [ ] Fallback logic for cache failures
- [ ] Metrics tracking implemented

### Production

- [ ] Redis configured with persistence
- [ ] Cache warming on deployment
- [ ] Monitoring and alerting set up
- [ ] Hit ratio > 95%
- [ ] Eviction policy configured (LRU recommended)

---

## Next Steps

### Learn More

- **[Performance Tuning](performance-tuning.md)** - Database optimization
- **[GraphQL Optimization](graphql-optimization.md)** - API caching
- **[Monitoring Guide](monitoring.md)** - Cache monitoring

### Tools

- **Redis** - In-memory cache
- **Memcached** - Alternative cache
- **Varnish** - HTTP cache
- **Cloudflare** - CDN caching

---

## Summary

You've learned:
- ✅ Multi-layer caching strategy
- ✅ Application-level caching with Redis
- ✅ Database-level caching (materialized views)
- ✅ CDN caching for GraphQL
- ✅ Client-side Apollo cache
- ✅ Cache warming and monitoring

**Key Takeaway**: Effective caching requires layering—application, database, CDN, and client caches working together.

**Next**: Monitor your caches with [Monitoring Guide](monitoring.md) →

---

**Cache aggressively, invalidate precisely—95% hit ratio is achievable.**
