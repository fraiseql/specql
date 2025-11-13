# GraphQL Schema Design for Registry Operations

**Date**: 2025-11-12
**Purpose**: Design GraphQL API for domain registry operations
**Pattern**: GraphQL Schema with resolvers calling application services

---

## GraphQL Schema Overview

### Core Types

```graphql
# Enums
enum SchemaType {
  FRAMEWORK
  MULTI_TENANT
  SHARED
}

enum PatternCategory {
  WORKFLOW
  VALIDATION
  AUDIT
  SECURITY
  PERFORMANCE
  INTEGRATION
}

# Domain Types
type Domain {
  domainNumber: Int!
  domainName: String!
  schemaType: SchemaType!
  identifier: String!
  description: String
  subdomains: [Subdomain!]!
  createdAt: DateTime
  updatedAt: DateTime
}

type Subdomain {
  subdomainNumber: Int!
  subdomainName: String!
  parentDomainNumber: Int!
  identifier: String!
  description: String
  entities: [Entity!]!
  nextEntitySequence: Int!
  createdAt: DateTime
  updatedAt: DateTime
}

# Pattern Types
type Pattern {
  patternId: String!
  patternName: String!
  category: PatternCategory!
  description: String!
  patternType: String!
  usageCount: Int!
  popularityScore: Float!
  parameters: JSONObject
  implementation: JSONObject
  sourceType: String!
  isActive: Boolean!
  createdAt: DateTime
  updatedAt: DateTime
}

# Search & Recommendation Types
type PatternSearchResult {
  pattern: Pattern!
  similarity: Float!
  relevanceScore: Float!
}

type PatternRecommendation {
  pattern: Pattern!
  confidence: Float!
  reasoning: String!
}

# Mutation Results
type DomainRegistrationResult {
  success: Boolean!
  domain: Domain
  error: String
}

type SubdomainRegistrationResult {
  success: Boolean!
  subdomain: Subdomain
  error: String
}

# Scalars
scalar DateTime
scalar JSONObject
```

---

## Query Operations

### Domain Queries

```graphql
type Query {
  # Domain operations
  domains(schemaType: SchemaType): [Domain!]!
  domain(domainNumber: Int!): Domain

  # Subdomain operations
  subdomains(parentDomainNumber: Int): [Subdomain!]!
  subdomain(domainNumber: Int!, subdomainNumber: Int!): Subdomain

  # Pattern operations
  patterns(category: PatternCategory, activeOnly: Boolean): [Pattern!]!
  pattern(patternId: String!): Pattern

  # Search operations
  searchPatterns(
    query: String!
    limit: Int = 10
    minSimilarity: Float = 0.5
    category: PatternCategory
  ): [PatternSearchResult!]!

  findSimilarPatterns(
    patternId: String!
    limit: Int = 5
    minSimilarity: Float = 0.5
  ): [PatternSearchResult!]!

  recommendPatterns(
    entityDescription: String!
    fieldNames: [String!]!
    limit: Int = 5
  ): [PatternRecommendation!]!
}
```

---

## Mutation Operations

### Domain Mutations

```graphql
type Mutation {
  # Domain management
  registerDomain(
    domainNumber: Int!
    domainName: String!
    schemaType: SchemaType!
    description: String
  ): DomainRegistrationResult!

  # Subdomain management
  registerSubdomain(
    parentDomainNumber: Int!
    subdomainNumber: Int!
    subdomainName: String!
    description: String
  ): SubdomainRegistrationResult!

  # Pattern management (future)
  createPatternFromDescription(
    description: String!
    category: PatternCategory
    save: Boolean = false
  ): Pattern

  approvePattern(patternId: String!, reviewer: String!): Boolean!
  rejectPattern(patternId: String!, reason: String!, reviewer: String!): Boolean!
}
```

---

## Resolver Implementation

### Domain Resolvers

```python
# src/presentation/graphql/resolvers/domain_resolvers.py

from src.application.services.domain_service_factory import get_domain_service_with_fallback

class DomainResolvers:
    """GraphQL resolvers for domain operations"""

    def resolve_domains(self, info, schema_type=None):
        """Resolve domains query"""
        service = get_domain_service_with_fallback()
        return service.list_domains(schema_type=schema_type)

    def resolve_domain(self, info, domain_number):
        """Resolve single domain query"""
        service = get_domain_service_with_fallback()
        try:
            return service.get_domain(domain_number)
        except DomainNotFoundError:
            return None

    async def resolve_register_domain(
        self, info,
        domain_number, domain_name, schema_type, description=None
    ):
        """Resolve register domain mutation"""
        service = get_domain_service_with_fallback()
        try:
            domain = service.register_domain(
                domain_number=domain_number,
                domain_name=domain_name,
                schema_type=schema_type.lower()
            )
            return {
                "success": True,
                "domain": domain,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "domain": None,
                "error": str(e)
            }
```

### Subdomain Resolvers

```python
# src/presentation/graphql/resolvers/subdomain_resolvers.py

from src.application.services.subdomain_service import SubdomainService
from src.application.services.domain_service_factory import get_domain_service_with_fallback

class SubdomainResolvers:
    """GraphQL resolvers for subdomain operations"""

    def resolve_subdomains(self, info, parent_domain_number=None):
        """Resolve subdomains query"""
        # For now, delegate to domain service
        # TODO: Use dedicated SubdomainService when implemented
        service = get_domain_service_with_fallback()
        # This would need to be implemented in DomainService
        return []

    def resolve_subdomain(self, info, domain_number, subdomain_number):
        """Resolve single subdomain query"""
        # TODO: Implement
        return None

    async def resolve_register_subdomain(
        self, info,
        parent_domain_number, subdomain_number, subdomain_name, description=None
    ):
        """Resolve register subdomain mutation"""
        # TODO: Use SubdomainService
        return {
            "success": False,
            "subdomain": None,
            "error": "Not implemented yet"
        }
```

### Pattern Resolvers

```python
# src/presentation/graphql/resolvers/pattern_resolvers.py

from src.application.services.pattern_service_factory import get_pattern_service_with_fallback

class PatternResolvers:
    """GraphQL resolvers for pattern operations"""

    def resolve_patterns(self, info, category=None, active_only=False):
        """Resolve patterns query"""
        service = get_pattern_service_with_fallback()
        patterns = service.list_all_patterns()

        if category:
            patterns = [p for p in patterns if p.category.value == category]
        if active_only:
            patterns = [p for p in patterns if p.is_active]

        return patterns

    def resolve_pattern(self, info, pattern_id):
        """Resolve single pattern query"""
        service = get_pattern_service_with_fallback()
        return service.get_pattern(pattern_id)

    def resolve_search_patterns(
        self, info, query, limit=10, min_similarity=0.5, category=None
    ):
        """Resolve pattern search query"""
        service = get_pattern_service_with_fallback()
        results = service.search_patterns_semantic(
            query=query,
            limit=limit,
            min_similarity=min_similarity,
            category=category
        )
        return results

    def resolve_find_similar_patterns(
        self, info, pattern_id, limit=5, min_similarity=0.5
    ):
        """Resolve similar patterns query"""
        service = get_pattern_service_with_fallback()
        pattern = service.get_pattern(pattern_id)
        if not pattern or not pattern.id:
            return []

        results = service.find_similar_patterns(
            pattern_id=pattern.id,
            limit=limit,
            min_similarity=min_similarity
        )
        return results

    def resolve_recommend_patterns(
        self, info, entity_description, field_names, limit=5
    ):
        """Resolve pattern recommendations query"""
        service = get_pattern_service_with_fallback()
        recommendations = service.recommend_patterns_for_entity(
            entity_description=entity_description,
            field_names=field_names,
            limit=limit
        )
        return recommendations
```

---

## Schema Registration

### GraphQL App Setup

```python
# src/presentation/graphql/app.py

import graphene
from .resolvers.domain_resolvers import DomainResolvers
from .resolvers.subdomain_resolvers import SubdomainResolvers
from .resolvers.pattern_resolvers import PatternResolvers

class Query(
    DomainResolvers,
    SubdomainResolvers,
    PatternResolvers,
    graphene.ObjectType
):
    """Root GraphQL Query"""
    pass

class Mutation(
    DomainResolvers,
    SubdomainResolvers,
    graphene.ObjectType
):
    """Root GraphQL Mutation"""
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)
```

---

## Example Queries

### Domain Operations

```graphql
# List all domains
query {
  domains {
    domainNumber
    domainName
    schemaType
    identifier
    subdomains {
      subdomainNumber
      subdomainName
    }
  }
}

# Get specific domain
query {
  domain(domainNumber: 1) {
    domainNumber
    domainName
    schemaType
    subdomains {
      subdomainNumber
      subdomainName
      entities {
        name
        tableCode
      }
    }
  }
}

# Register new domain
mutation {
  registerDomain(
    domainNumber: 5
    domainName: "analytics"
    schemaType: MULTI_TENANT
    description: "Analytics and reporting domain"
  ) {
    success
    domain {
      domainNumber
      domainName
      identifier
    }
    error
  }
}
```

### Pattern Operations

```graphql
# Search patterns
query {
  searchPatterns(
    query: "validate email addresses"
    limit: 5
    minSimilarity: 0.7
  ) {
    pattern {
      patternId
      patternName
      category
      description
      usageCount
    }
    similarity
  }
}

# Get pattern recommendations
query {
  recommendPatterns(
    entityDescription: "Customer contact information"
    fieldNames: ["email", "phone", "address"]
    limit: 3
  ) {
    pattern {
      patternId
      patternName
      description
    }
    confidence
    reasoning
  }
}
```

---

## Benefits of GraphQL API

### 1. Type Safety
**Strong typing** with GraphQL schema provides compile-time guarantees

### 2. Flexible Queries
**Client-driven queries** - clients request exactly what they need

### 3. Single Endpoint
**REST-like operations** over single `/graphql` endpoint

### 4. Real-time Updates
**Subscriptions support** for real-time registry updates

### 5. API Evolution
**Backwards compatibility** through schema versioning

### 6. Developer Experience
**Introspection** enables auto-generated documentation and client libraries

---

## Implementation Roadmap

### Phase 1: Core Domain Operations
- ✅ Domain listing and registration
- ✅ Basic GraphQL schema
- ⏳ Subdomain operations
- ⏳ Pattern search and recommendations

### Phase 2: Advanced Features
- ⏳ Real-time subscriptions
- ⏳ Schema versioning
- ⏳ Authentication/authorization
- ⏳ Rate limiting

### Phase 3: Production Ready
- ⏳ Performance optimization
- ⏳ Caching strategies
- ⏳ Monitoring and logging
- ⏳ API documentation

---

**Status**: GraphQL schema designed
**Next**: Implement GraphQL resolvers (Day 5)