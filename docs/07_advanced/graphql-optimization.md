# GraphQL Optimization Guide

> **Eliminate N+1 queries and optimize GraphQL performance—milliseconds matter**

## Overview

GraphQL's flexibility creates performance challenges:
- ❌ N+1 query problem
- ❌ Over-fetching / under-fetching
- ❌ Unbounded queries
- ❌ Expensive nested resolvers

**Solutions**:
- ✅ DataLoader for batching
- ✅ Query complexity limits
- ✅ Persisted queries
- ✅ Response caching
- ✅ Database query optimization

**Goal**: Sub-100ms GraphQL response times

---

## N+1 Query Problem

### The Problem

**GraphQL Query**:
```graphql
query GetContacts {
  contacts(limit: 50) {
    id
    email
    company {      # ← N+1 problem!
      id
      name
    }
  }
}
```

**Naive Implementation** (50+ database queries):
```javascript
// Resolver for contacts
contacts: async () => {
  // Query 1: Fetch all contacts
  const contacts = await db.query('SELECT * FROM tb_contact LIMIT 50');
  return contacts;
},

// Resolver for company (called 50 times!)
company: async (contact) => {
  // Queries 2-51: Fetch company for each contact
  const company = await db.query(
    'SELECT * FROM tb_company WHERE pk_company = $1',
    [contact.fk_company]
  );
  return company;
}
```

**Result**: 1 query for contacts + 50 queries for companies = **51 queries total** 😱

---

### Solution 1: DataLoader

**Install DataLoader**:
```bash
npm install dataloader
```

**Create Company DataLoader**:
```typescript
import DataLoader from 'dataloader';

// Batch load companies by PKs
const companyLoader = new DataLoader(async (companyPks: number[]) => {
  // Single query fetching all companies at once
  const companies = await db.query(
    'SELECT * FROM crm.tb_company WHERE pk_company = ANY($1)',
    [companyPks]
  );

  // Return in same order as requested PKs
  const companyMap = new Map(companies.map(c => [c.pk_company, c]));
  return companyPks.map(pk => companyMap.get(pk));
});

// Resolver using DataLoader
const resolvers = {
  Query: {
    contacts: async () => {
      return db.query('SELECT * FROM crm.tb_contact LIMIT 50');
    }
  },
  Contact: {
    company: async (contact, args, context) => {
      // DataLoader batches these 50 calls into 1 query
      return context.loaders.companyLoader.load(contact.fk_company);
    }
  }
};
```

**Result**: 1 query for contacts + 1 batched query for companies = **2 queries total** ✅

**Performance**: 25x fewer queries!

---

### Solution 2: JOIN in Resolver

**Alternative**: Fetch everything in one query

```typescript
const resolvers = {
  Query: {
    contacts: async () => {
      // Single JOIN query
      const rows = await db.query(`
        SELECT
          c.*,
          json_build_object(
            'pk_company', co.pk_company,
            'id', co.id,
            'name', co.name,
            'website', co.website
          ) as company
        FROM crm.tb_contact c
        INNER JOIN crm.tb_company co ON c.fk_company = co.pk_company
        LIMIT 50
      `);

      return rows.map(row => ({
        ...row,
        company: row.company  // Already loaded
      }));
    }
  },
  Contact: {
    // No resolver needed - company already loaded
  }
};
```

**Result**: **1 query total** ✅

**Trade-off**: Less flexible, but faster for known query patterns

---

## Query Complexity Analysis

### The Problem

**Expensive nested query**:
```graphql
query ExpensiveQuery {
  companies {                    # 1000 companies
    contacts {                   # 50 contacts each = 50,000 contacts
      orders {                   # 100 orders each = 5,000,000 orders
        items {                  # 10 items each = 50,000,000 items
          product {              # ...
            categories {         # Exponential explosion!
              ...
            }
          }
        }
      }
    }
  }
}
```

**Potential**: 50 million database rows 😱

---

### Solution: Query Complexity Limits

**Install graphql-query-complexity**:
```bash
npm install graphql-query-complexity
```

**Configure complexity limits**:
```typescript
import { createComplexityLimitRule } from 'graphql-query-complexity';

const server = new ApolloServer({
  schema,
  validationRules: [
    createComplexityLimitRule(1000, {
      onCost: (cost) => {
        console.log('Query cost:', cost);
      },
      formatErrorMessage: (cost) =>
        `Query too complex: ${cost}. Maximum allowed: 1000`
    })
  ]
});
```

**Assign complexity scores**:
```typescript
const typeDefs = gql`
  type Query {
    contacts(limit: Int = 50): [Contact!]!  # Cost: limit * 10
    companies: [Company!]!                   # Cost: 100
  }

  type Contact {
    id: ID!                                  # Cost: 0
    email: String!                           # Cost: 0
    company: Company!                        # Cost: 10 (JOIN cost)
    orders: [Order!]!                        # Cost: 50 * 10
  }
`;

const resolvers = {
  Query: {
    contacts: {
      resolve: ...,
      complexity: ({ args, childComplexity }) => {
        return (args.limit || 50) * childComplexity;
      }
    }
  }
};
```

**Result**: Expensive queries rejected before execution

---

## Pagination Strategies

### Offset-Based Pagination

**Simple but inefficient for large offsets**:

```graphql
query GetContacts($page: Int!) {
  contacts(limit: 50, offset: $page * 50) {
    id
    email
    firstName
  }
}
```

**Problem**: `OFFSET 10000` still scans 10,000 rows

---

### Cursor-Based Pagination (Relay Style)

**Efficient for large datasets**:

```graphql
query GetContacts($after: String, $first: Int!) {
  contacts(after: $after, first: $first) {
    edges {
      node {
        id
        email
        firstName
      }
      cursor
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

**SpecQL generated resolver**:
```typescript
const resolvers = {
  Query: {
    contacts: async (parent, { after, first }) => {
      const afterCursor = after ? decodeCursor(after) : null;

      const contacts = await db.query(`
        SELECT * FROM crm.tb_contact
        WHERE created_at > $1
        ORDER BY created_at ASC
        LIMIT $2
      `, [afterCursor?.created_at || '1970-01-01', first]);

      return {
        edges: contacts.map(contact => ({
          node: contact,
          cursor: encodeCursor({ created_at: contact.created_at })
        })),
        pageInfo: {
          hasNextPage: contacts.length === first,
          endCursor: contacts.length > 0
            ? encodeCursor({ created_at: contacts[contacts.length - 1].created_at })
            : null
        }
      };
    }
  }
};

function encodeCursor(data) {
  return Buffer.from(JSON.stringify(data)).toString('base64');
}

function decodeCursor(cursor) {
  return JSON.parse(Buffer.from(cursor, 'base64').toString());
}
```

**Benefits**:
- Consistent performance regardless of page
- Handles real-time data changes gracefully
- Efficient database queries

---

## Persisted Queries

### The Problem

**Large GraphQL queries** sent on every request waste bandwidth:

```graphql
# 2KB query sent every request
query GetOrderDetails($orderId: ID!) {
  order(id: $orderId) {
    id
    total
    customer {
      id
      name
      email
      address {
        street
        city
        state
        postalCode
      }
    }
    items {
      id
      quantity
      unitPrice
      product {
        id
        name
        description
        images {
          url
          alt
        }
      }
    }
  }
}
```

---

### Solution: Automatic Persisted Queries (APQ)

**Install apollo-server-plugin-response-cache**:
```bash
npm install apollo-server-plugin-response-cache
```

**Configure APQ**:
```typescript
import { ApolloServer } from 'apollo-server';
import { ApolloServerPluginUsageReporting } from 'apollo-server-core';

const server = new ApolloServer({
  schema,
  plugins: [
    ApolloServerPluginUsageReporting({
      sendHeaders: { all: true },
    }),
  ],
  // Enable APQ
  persistedQueries: {
    cache: new Map(),  // In-memory cache (use Redis for production)
  },
});
```

**How it works**:

1. **First request**: Client sends query hash + full query
   ```json
   {
     "query": "query GetOrder($id: ID!) { ... }",
     "extensions": {
       "persistedQuery": {
         "version": 1,
         "sha256Hash": "abc123..."
       }
     }
   }
   ```

2. **Subsequent requests**: Client sends only hash
   ```json
   {
     "extensions": {
       "persistedQuery": {
         "version": 1,
         "sha256Hash": "abc123..."
       }
     },
     "variables": { "id": "550e8400..." }
   }
   ```

**Benefits**:
- 95% smaller requests
- Reduced parsing overhead
- Better CDN caching

---

## Response Caching

### Field-Level Caching

**Cache expensive fields**:

```typescript
import responseCachePlugin from 'apollo-server-plugin-response-cache';

const server = new ApolloServer({
  schema,
  plugins: [
    responseCachePlugin({
      sessionId: (requestContext) =>
        requestContext.request.http?.headers.get('session-id') || null,
    }),
  ],
});

const typeDefs = gql`
  type Query {
    # Cache for 60 seconds
    products: [Product!]! @cacheControl(maxAge: 60)

    # Don't cache (user-specific)
    me: User! @cacheControl(maxAge: 0)
  }

  type Product {
    id: ID!
    name: String!

    # Cache product details for 5 minutes
    description: String! @cacheControl(maxAge: 300)

    # Don't cache price (changes frequently)
    price: Money! @cacheControl(maxAge: 0)
  }
`;
```

---

### Full Response Caching with Redis

```typescript
import { RedisCache } from 'apollo-server-cache-redis';
import Redis from 'ioredis';

const server = new ApolloServer({
  schema,
  cache: new RedisCache({
    client: new Redis({
      host: 'localhost',
      port: 6379,
    }),
  }),
  plugins: [
    responseCachePlugin({
      shouldReadFromCache: (requestContext) => {
        // Only cache public queries
        return !requestContext.request.http?.headers.get('authorization');
      },
      shouldWriteToCache: (requestContext) => {
        // Only cache successful responses
        return !requestContext.errors;
      },
    }),
  ],
});
```

---

## Database Query Optimization

### Use Impact Metadata for Cache Invalidation

**SpecQL impact metadata** tells you what changed:

```typescript
const [qualifyLead] = useMutation(QUALIFY_LEAD, {
  update: (cache, { data }) => {
    if (data.qualifyLead.status === 'success') {
      // Impact metadata tells us what to invalidate
      data.qualifyLead._meta.impacts.forEach(impact => {
        if (impact.entity === 'Contact' && impact.operation === 'UPDATE') {
          // Invalidate contact queries
          cache.evict({
            id: `Contact:${impact.ids[0]}`
          });

          // Invalidate list queries
          cache.evict({
            fieldName: 'contacts'
          });
        }
      });

      cache.gc();
    }
  }
});
```

---

### Batch Database Queries

**Use SQL UNION or array parameters**:

```typescript
// ❌ Bad: N queries
async function getOrdersByIds(orderIds: string[]) {
  const orders = [];
  for (const id of orderIds) {
    const order = await db.query(
      'SELECT * FROM sales.tb_order WHERE id = $1',
      [id]
    );
    orders.push(order);
  }
  return orders;
}

// ✅ Good: 1 query
async function getOrdersByIds(orderIds: string[]) {
  return db.query(
    'SELECT * FROM sales.tb_order WHERE id = ANY($1)',
    [orderIds]
  );
}
```

---

## Monitoring GraphQL Performance

### Apollo Studio Integration

```typescript
import { ApolloServer } from 'apollo-server';
import { ApolloServerPluginUsageReporting } from 'apollo-server-core';

const server = new ApolloServer({
  schema,
  plugins: [
    ApolloServerPluginUsageReporting({
      sendVariableValues: { all: true },
      sendHeaders: { all: true },
    }),
  ],
});
```

**Metrics tracked**:
- Query execution time
- Resolver performance
- Cache hit rates
- Error rates
- Query complexity

---

### Custom Performance Tracking

```typescript
import { ApolloServerPlugin } from 'apollo-server-plugin-base';

const performancePlugin: ApolloServerPlugin = {
  async requestDidStart() {
    const start = Date.now();

    return {
      async willSendResponse(requestContext) {
        const duration = Date.now() - start;

        // Log slow queries
        if (duration > 1000) {
          console.warn('Slow query detected:', {
            query: requestContext.request.query,
            duration,
            variables: requestContext.request.variables,
          });
        }

        // Send to monitoring service
        await sendMetric('graphql.query.duration', duration, {
          operation: requestContext.operationName,
        });
      },
    };
  },
};

const server = new ApolloServer({
  schema,
  plugins: [performancePlugin],
});
```

---

## Best Practices Summary

### ✅ DO

1. **Use DataLoader** for batching
2. **Implement complexity limits** to prevent expensive queries
3. **Use cursor-based pagination** for large datasets
4. **Enable persisted queries** (APQ)
5. **Cache responses** with appropriate TTLs
6. **Monitor performance** with Apollo Studio
7. **Optimize database queries** (indexes, JOINs)
8. **Use impact metadata** for cache invalidation

---

### ❌ DON'T

1. **Don't ignore N+1 problems**
2. **Don't allow unbounded queries**
3. **Don't over-fetch data** (select only needed fields)
4. **Don't skip caching** for expensive operations
5. **Don't forget monitoring**
6. **Don't use offset pagination** for large tables

---

## Performance Checklist

### Development

- [ ] DataLoader implemented for all relationships
- [ ] Query complexity limits configured
- [ ] Pagination implemented (cursor-based for large datasets)
- [ ] Cache control directives added
- [ ] Performance monitoring in place

### Production

- [ ] APQ enabled
- [ ] Redis cache configured
- [ ] CDN caching for static queries
- [ ] Database indexes optimized
- [ ] Query logging enabled
- [ ] Alerts for slow queries set up

---

## Next Steps

### Learn More

- **[Caching Guide](caching.md)** - Advanced caching strategies
- **[Performance Tuning](performance-tuning.md)** - Database optimization
- **[Monitoring Guide](monitoring.md)** - Production monitoring

### Tools

- **Apollo Studio** - GraphQL monitoring
- **DataLoader** - Request batching
- **Redis** - Response caching
- **graphql-query-complexity** - Complexity analysis

---

## Summary

You've learned:
- ✅ Solving N+1 query problems with DataLoader
- ✅ Query complexity limits
- ✅ Efficient pagination strategies
- ✅ Persisted queries (APQ)
- ✅ Response caching with Redis
- ✅ Database query optimization
- ✅ Performance monitoring

**Key Takeaway**: GraphQL optimization requires both client and server strategies—batch requests, limit complexity, cache aggressively.

**Next**: Advanced caching with [Caching Guide](caching.md) →

---

**Optimize every query—GraphQL performance is about batching and caching.**
