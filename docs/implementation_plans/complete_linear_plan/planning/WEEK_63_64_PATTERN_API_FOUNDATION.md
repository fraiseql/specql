# Weeks 63-64: Pattern API Foundation & Monetization Infrastructure

**Date**: 2025-11-13
**Duration**: 10 days (2 weeks)
**Status**: 🔴 Planning
**Objective**: Build hosted Pattern Library API with authentication, billing, and semantic search

**Prerequisites**: Week 60-62 complete (Universal Security Expression)
**Output**: Production-ready Pattern API with Stripe integration, multi-tier pricing, usage tracking

---

## 🎯 Executive Summary

Transform the open-source pattern library into a **monetizable SaaS API** that provides:

1. **Hosted Pattern Library** → Cloud-hosted patterns with 99.9% uptime
2. **Semantic Search API** → pgvector-powered pattern discovery
3. **Authentication & Authorization** → API keys, JWT, rate limiting
4. **Billing Infrastructure** → Stripe integration with usage-based pricing
5. **Analytics & Insights** → Pattern usage tracking and recommendations

### Core Philosophy

```yaml
# Open Source (Free Forever)
self_hosted_pattern_library:
  features:
    - All pattern storage code
    - Local semantic search
    - Pattern discovery
    - Community patterns (100 free)

# Pattern API (Paid SaaS)
hosted_api:
  developer_tier: $29/month
    - 1,000 API calls/month
    - 1,000 basic patterns
    - Semantic search
    - Community support

  team_tier: $199/month
    - 10,000 API calls/month
    - 5,000 premium patterns
    - AI recommendations
    - Team collaboration
    - Priority support

  enterprise_tier: $999-9,999/month
    - Unlimited API calls
    - All 10,000+ patterns
    - Private pattern library
    - Custom patterns
    - SLA guarantees
    - Dedicated support
```

### Success Criteria

- [ ] Pattern API deployed to production (multi-region)
- [ ] Stripe integration complete (subscriptions + usage-based)
- [ ] 3-tier pricing implemented (Developer, Team, Enterprise)
- [ ] API authentication with JWT tokens
- [ ] Rate limiting per tier
- [ ] Usage analytics dashboard
- [ ] 100 paying customers in first month
- [ ] $5k MRR by end of Week 64

---

## Week 63: Pattern API Backend & Authentication

**Objective**: Build production-ready Pattern API with authentication and multi-tier access control

### Day 1: API Architecture & Authentication System

**Morning Block (4 hours): API Design**

#### 1. Design API Architecture (2 hours)

**Architecture Document**: `docs/pattern_api/API_ARCHITECTURE.md`

```markdown
# Pattern API Architecture

## API Endpoints

### Pattern Discovery
```
GET /api/v1/patterns
GET /api/v1/patterns/{pattern_id}
GET /api/v1/patterns/search?q={query}
POST /api/v1/patterns/search/semantic (with embedding)
```

### Pattern Management (Creators)
```
POST /api/v1/patterns (create)
PUT /api/v1/patterns/{pattern_id} (update)
DELETE /api/v1/patterns/{pattern_id}
GET /api/v1/patterns/mine (my patterns)
```

### Usage Analytics
```
GET /api/v1/usage/stats
GET /api/v1/usage/quota
GET /api/v1/usage/history
```

### Account Management
```
GET /api/v1/account
PUT /api/v1/account
GET /api/v1/account/subscription
POST /api/v1/account/upgrade
```

## Authentication Flows

### API Key Authentication (Primary)
```
Headers:
  Authorization: Bearer sk_live_abc123...
```

### JWT Token Authentication (Web/Mobile)
```
Headers:
  Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

## Rate Limiting by Tier

| Tier | Requests/min | Requests/month | Patterns Access |
|------|--------------|----------------|-----------------|
| Free | 10 | 1,000 | 100 community |
| Developer ($29) | 60 | 10,000 | 1,000 patterns |
| Team ($199) | 300 | 100,000 | 5,000 patterns |
| Enterprise ($999+) | Unlimited | Unlimited | All 10,000+ |

## Multi-Region Deployment

```
┌─────────────────────────────────────────┐
│         Global Load Balancer            │
│         (CloudFlare / AWS Global)       │
└─────────────────────────────────────────┘
              ↓
    ┌─────────┴─────────┐
    ↓                   ↓
┌─────────┐       ┌─────────┐
│ US-EAST │       │ EU-WEST │
│ Primary │       │ Replica │
└─────────┘       └─────────┘
    ↓                   ↓
PostgreSQL          PostgreSQL
+ pgvector          + pgvector
(Read Replica)      (Read Replica)
```

## Caching Strategy

```
Level 1: CloudFlare CDN (static patterns)
  ↓
Level 2: Redis Cache (popular patterns, 1-hour TTL)
  ↓
Level 3: PostgreSQL (source of truth)
```

## Security

1. **API Key Management**
   - Format: `sk_live_` (production) or `sk_test_` (sandbox)
   - Hashed with bcrypt before storage
   - Rotation support
   - Scopes: read, write, admin

2. **Rate Limiting**
   - Redis-based (token bucket algorithm)
   - Per API key
   - 429 response with Retry-After header

3. **DDoS Protection**
   - CloudFlare DDoS protection
   - Geographic blocking (optional)
   - Bot detection
```

---

#### 🔴 RED: Authentication Tests (1 hour)

**Test File**: `tests/unit/pattern_api/test_authentication.py`

```python
"""Tests for Pattern API authentication"""

import pytest
from src.pattern_api.auth import APIKeyAuth, JWTAuth, RateLimiter
from src.pattern_api.models import User, Subscription, APIKey


class TestAPIKeyAuthentication:
    """Test API key authentication"""

    @pytest.fixture
    def auth(self):
        return APIKeyAuth()

    def test_valid_api_key(self, auth):
        """Test authentication with valid API key"""
        # Arrange
        api_key = "sk_live_abc123def456"
        user = User(
            id=1,
            email="test@example.com",
            subscription_tier="developer"
        )

        # Act
        authenticated_user = auth.authenticate(api_key)

        # Assert
        assert authenticated_user is not None
        assert authenticated_user.id == user.id
        assert authenticated_user.subscription_tier == "developer"

    def test_invalid_api_key(self, auth):
        """Test authentication with invalid API key"""
        # Arrange
        api_key = "sk_live_invalid"

        # Act & Assert
        with pytest.raises(AuthenticationError):
            auth.authenticate(api_key)

    def test_expired_api_key(self, auth):
        """Test authentication with expired API key"""
        # Arrange
        api_key = "sk_live_expired123"

        # Act & Assert
        with pytest.raises(AuthenticationError, match="API key expired"):
            auth.authenticate(api_key)

    def test_revoked_api_key(self, auth):
        """Test authentication with revoked API key"""
        # Arrange
        api_key = "sk_live_revoked123"

        # Act & Assert
        with pytest.raises(AuthenticationError, match="API key revoked"):
            auth.authenticate(api_key)


class TestRateLimiting:
    """Test rate limiting by tier"""

    @pytest.fixture
    def limiter(self):
        return RateLimiter(redis_client=None)  # Mock Redis

    def test_developer_tier_rate_limit(self, limiter):
        """Test rate limiting for developer tier"""
        # Arrange
        user = User(id=1, subscription_tier="developer")

        # Act - Make 60 requests (limit for developer)
        for i in range(60):
            allowed = limiter.check_rate_limit(user, endpoint="/api/v1/patterns")
            assert allowed is True

        # 61st request should be denied
        allowed = limiter.check_rate_limit(user, endpoint="/api/v1/patterns")
        assert allowed is False

    def test_team_tier_higher_limit(self, limiter):
        """Test that team tier has higher rate limit"""
        # Arrange
        user = User(id=2, subscription_tier="team")

        # Act - Make 300 requests (limit for team)
        for i in range(300):
            allowed = limiter.check_rate_limit(user, endpoint="/api/v1/patterns")
            assert allowed is True

    def test_enterprise_unlimited(self, limiter):
        """Test that enterprise tier has no rate limit"""
        # Arrange
        user = User(id=3, subscription_tier="enterprise")

        # Act - Make 1000 requests
        for i in range(1000):
            allowed = limiter.check_rate_limit(user, endpoint="/api/v1/patterns")
            assert allowed is True


class TestPatternAccessControl:
    """Test pattern access based on subscription tier"""

    def test_free_tier_access(self):
        """Test free tier can only access community patterns"""
        # Arrange
        user = User(id=1, subscription_tier="free")
        pattern = Pattern(id=1, tier="community")

        # Act
        has_access = user.can_access_pattern(pattern)

        # Assert
        assert has_access is True

    def test_free_tier_cannot_access_premium(self):
        """Test free tier cannot access premium patterns"""
        # Arrange
        user = User(id=1, subscription_tier="free")
        pattern = Pattern(id=2, tier="premium")

        # Act
        has_access = user.can_access_pattern(pattern)

        # Assert
        assert has_access is False

    def test_developer_tier_access(self):
        """Test developer tier can access up to 1,000 patterns"""
        # Arrange
        user = User(id=2, subscription_tier="developer")

        # Act
        accessible_patterns = user.get_accessible_patterns()

        # Assert
        assert len(accessible_patterns) <= 1000
        assert all(p.tier in ["community", "basic"] for p in accessible_patterns)

    def test_enterprise_tier_full_access(self):
        """Test enterprise tier can access all patterns"""
        # Arrange
        user = User(id=3, subscription_tier="enterprise")

        # Act
        accessible_patterns = user.get_accessible_patterns()

        # Assert
        assert len(accessible_patterns) >= 10000  # All patterns
```

**Run Tests (Should Fail)**:
```bash
uv run pytest tests/unit/pattern_api/test_authentication.py -v
# Expected: ImportError or test failures
```

---

#### 🟢 GREEN: Implement Authentication (2 hours)

**Authentication System**: `src/pattern_api/auth.py`

```python
"""
Pattern API Authentication

Handles API key authentication, JWT tokens, and rate limiting.
"""

import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
import redis
from dataclasses import dataclass


@dataclass
class User:
    """User with subscription tier"""
    id: int
    email: str
    subscription_tier: str  # free, developer, team, enterprise
    api_key_hash: Optional[str] = None
    created_at: Optional[datetime] = None

    def can_access_pattern(self, pattern: 'Pattern') -> bool:
        """Check if user can access pattern based on tier"""
        tier_access = {
            "free": ["community"],
            "developer": ["community", "basic"],
            "team": ["community", "basic", "premium"],
            "enterprise": ["community", "basic", "premium", "enterprise"]
        }

        allowed_tiers = tier_access.get(self.subscription_tier, [])
        return pattern.tier in allowed_tiers

    def get_rate_limit(self) -> int:
        """Get rate limit (requests per minute) for user's tier"""
        rate_limits = {
            "free": 10,
            "developer": 60,
            "team": 300,
            "enterprise": float('inf')
        }
        return rate_limits.get(self.subscription_tier, 10)

    def get_monthly_quota(self) -> int:
        """Get monthly API call quota for user's tier"""
        quotas = {
            "free": 1000,
            "developer": 10000,
            "team": 100000,
            "enterprise": float('inf')
        }
        return quotas.get(self.subscription_tier, 1000)


class AuthenticationError(Exception):
    """Authentication failed"""
    pass


class APIKeyAuth:
    """API Key authentication"""

    def __init__(self, db_connection):
        self.db = db_connection
        self.secret_key = self._load_secret_key()

    def _load_secret_key(self) -> str:
        """Load secret key from environment"""
        import os
        return os.getenv("API_SECRET_KEY", "change-me-in-production")

    def authenticate(self, api_key: str) -> User:
        """
        Authenticate user by API key

        Args:
            api_key: API key (format: sk_live_abc123...)

        Returns:
            Authenticated User object

        Raises:
            AuthenticationError if invalid/expired/revoked
        """
        # Validate format
        if not api_key.startswith("sk_live_") and not api_key.startswith("sk_test_"):
            raise AuthenticationError("Invalid API key format")

        # Hash API key for lookup
        api_key_hash = self._hash_api_key(api_key)

        # Query database
        query = """
            SELECT
                u.id,
                u.email,
                u.subscription_tier,
                ak.revoked,
                ak.expires_at
            FROM users u
            JOIN api_keys ak ON ak.user_id = u.id
            WHERE ak.key_hash = %s
        """

        result = self.db.execute(query, (api_key_hash,))

        if not result:
            raise AuthenticationError("Invalid API key")

        user_data = result[0]

        # Check if revoked
        if user_data['revoked']:
            raise AuthenticationError("API key revoked")

        # Check if expired
        if user_data['expires_at'] and user_data['expires_at'] < datetime.now():
            raise AuthenticationError("API key expired")

        return User(
            id=user_data['id'],
            email=user_data['email'],
            subscription_tier=user_data['subscription_tier'],
            api_key_hash=api_key_hash
        )

    def _hash_api_key(self, api_key: str) -> str:
        """Hash API key with secret for storage/lookup"""
        return hmac.new(
            self.secret_key.encode(),
            api_key.encode(),
            hashlib.sha256
        ).hexdigest()

    def generate_api_key(self, user_id: int, prefix: str = "sk_live_") -> str:
        """
        Generate new API key for user

        Args:
            user_id: User ID
            prefix: Key prefix (sk_live_ or sk_test_)

        Returns:
            New API key
        """
        import secrets

        # Generate random key
        random_part = secrets.token_urlsafe(32)
        api_key = f"{prefix}{random_part}"

        # Hash and store
        api_key_hash = self._hash_api_key(api_key)

        query = """
            INSERT INTO api_keys (user_id, key_hash, created_at)
            VALUES (%s, %s, NOW())
        """
        self.db.execute(query, (user_id, api_key_hash))

        return api_key


class JWTAuth:
    """JWT token authentication (for web/mobile apps)"""

    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def create_token(self, user: User, expires_in: int = 3600) -> str:
        """
        Create JWT token for user

        Args:
            user: User object
            expires_in: Token expiration in seconds (default: 1 hour)

        Returns:
            JWT token string
        """
        payload = {
            "user_id": user.id,
            "email": user.email,
            "tier": user.subscription_tier,
            "exp": datetime.utcnow() + timedelta(seconds=expires_in),
            "iat": datetime.utcnow()
        }

        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def verify_token(self, token: str) -> User:
        """
        Verify JWT token and return user

        Args:
            token: JWT token string

        Returns:
            User object

        Raises:
            AuthenticationError if invalid/expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])

            return User(
                id=payload["user_id"],
                email=payload["email"],
                subscription_tier=payload["tier"]
            )

        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")


class RateLimiter:
    """Rate limiting using Redis token bucket algorithm"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def check_rate_limit(
        self,
        user: User,
        endpoint: str,
        cost: int = 1
    ) -> bool:
        """
        Check if request is within rate limit

        Args:
            user: User making request
            endpoint: API endpoint
            cost: Cost of request (default: 1)

        Returns:
            True if allowed, False if rate limited
        """
        if user.subscription_tier == "enterprise":
            return True  # Unlimited for enterprise

        # Rate limit key
        key = f"rate_limit:{user.id}:{endpoint}"

        # Get user's rate limit
        limit = user.get_rate_limit()

        # Token bucket algorithm
        now = time.time()

        # Get current tokens
        bucket = self.redis.get(key)

        if bucket is None:
            # Initialize bucket
            tokens = limit - cost
            self.redis.setex(key, 60, tokens)  # 60 second window
            return True

        tokens = int(bucket)

        if tokens >= cost:
            # Consume tokens
            self.redis.decr(key, cost)
            return True
        else:
            # Rate limited
            return False

    def check_monthly_quota(self, user: User) -> bool:
        """
        Check if user is within monthly quota

        Args:
            user: User making request

        Returns:
            True if within quota, False if exceeded
        """
        if user.subscription_tier == "enterprise":
            return True  # Unlimited for enterprise

        # Monthly quota key
        key = f"monthly_quota:{user.id}:{datetime.now().strftime('%Y-%m')}"

        # Get current usage
        usage = self.redis.get(key)
        usage = int(usage) if usage else 0

        # Check quota
        quota = user.get_monthly_quota()

        if usage < quota:
            # Increment usage
            self.redis.incr(key)
            self.redis.expire(key, 60 * 60 * 24 * 31)  # 31 days
            return True
        else:
            return False
```

**Run Tests (Should Pass)**:
```bash
uv run pytest tests/unit/pattern_api/test_authentication.py -v
# Expected: All tests pass
```

---

**Afternoon Block (4 hours): Pattern API Endpoints**

#### 🔴 RED: API Endpoint Tests (1.5 hours)

**Test File**: `tests/unit/pattern_api/test_endpoints.py`

```python
"""Tests for Pattern API endpoints"""

import pytest
from fastapi.testclient import TestClient
from src.pattern_api.main import app


class TestPatternEndpoints:
    """Test Pattern API endpoints"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        return {"Authorization": "Bearer sk_test_abc123"}

    def test_list_patterns(self, client, auth_headers):
        """Test listing patterns"""
        # Act
        response = client.get("/api/v1/patterns", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "patterns" in data
        assert "total" in data
        assert "page" in data

    def test_list_patterns_with_pagination(self, client, auth_headers):
        """Test listing patterns with pagination"""
        # Act
        response = client.get(
            "/api/v1/patterns?page=2&per_page=20",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert len(data["patterns"]) <= 20

    def test_get_pattern_by_id(self, client, auth_headers):
        """Test getting specific pattern"""
        # Act
        response = client.get("/api/v1/patterns/123", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        pattern = response.json()
        assert pattern["id"] == 123
        assert "name" in pattern
        assert "description" in pattern
        assert "code" in pattern

    def test_search_patterns(self, client, auth_headers):
        """Test searching patterns by text"""
        # Act
        response = client.get(
            "/api/v1/patterns/search?q=approval+workflow",
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 200
        results = response.json()
        assert "patterns" in results
        assert "total" in results

    def test_semantic_search(self, client, auth_headers):
        """Test semantic search with embeddings"""
        # Arrange
        search_request = {
            "query": "multi-step approval process with notifications",
            "limit": 10
        }

        # Act
        response = client.post(
            "/api/v1/patterns/search/semantic",
            headers=auth_headers,
            json=search_request
        )

        # Assert
        assert response.status_code == 200
        results = response.json()
        assert len(results["patterns"]) <= 10
        # Results should be ordered by relevance
        assert results["patterns"][0]["similarity_score"] >= results["patterns"][1]["similarity_score"]

    def test_unauthorized_access(self, client):
        """Test accessing API without authentication"""
        # Act
        response = client.get("/api/v1/patterns")

        # Assert
        assert response.status_code == 401
        assert "Unauthorized" in response.json()["detail"]

    def test_rate_limit_exceeded(self, client, auth_headers):
        """Test rate limiting"""
        # Act - Make requests until rate limited
        responses = []
        for i in range(100):
            response = client.get("/api/v1/patterns", headers=auth_headers)
            responses.append(response.status_code)

        # Assert - Should eventually get 429 (Too Many Requests)
        assert 429 in responses

    def test_tier_access_control(self, client):
        """Test that free tier cannot access premium patterns"""
        # Arrange
        free_headers = {"Authorization": "Bearer sk_test_free_user"}

        # Act
        response = client.get(
            "/api/v1/patterns/premium-pattern-id",
            headers=free_headers
        )

        # Assert
        assert response.status_code == 403
        assert "Upgrade to access premium patterns" in response.json()["detail"]
```

---

#### 🟢 GREEN: Implement API Endpoints (2.5 hours)

**FastAPI Application**: `src/pattern_api/main.py`

```python
"""
Pattern API - FastAPI Application

Production-ready Pattern Library API with authentication, rate limiting, and billing.
"""

from fastapi import FastAPI, Depends, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import redis
from .auth import APIKeyAuth, RateLimiter, User, AuthenticationError
from .models import Pattern, PatternSearchRequest, PatternSearchResponse
from .database import get_db_connection


# Initialize FastAPI app
app = FastAPI(
    title="SpecQL Pattern API",
    description="Hosted Pattern Library with semantic search and AI recommendations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize dependencies
db = get_db_connection()
redis_client = redis.Redis(host='localhost', port=6379, db=0)
auth_service = APIKeyAuth(db)
rate_limiter = RateLimiter(redis_client)


# Dependency: Authenticate user
async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> User:
    """Authenticate user from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization format")

    api_key = authorization[7:]  # Remove "Bearer " prefix

    try:
        user = auth_service.authenticate(api_key)
        return user
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))


# Dependency: Check rate limit
async def check_rate_limit(
    user: User = Depends(get_current_user)
):
    """Check if user is within rate limit"""
    if not rate_limiter.check_rate_limit(user, endpoint="/api/v1/patterns"):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {user.get_rate_limit()} requests/minute for {user.subscription_tier} tier."
        )

    if not rate_limiter.check_monthly_quota(user):
        raise HTTPException(
            status_code=429,
            detail=f"Monthly quota exceeded. Upgrade your plan for more API calls."
        )


# ============================================================================
# Pattern Endpoints
# ============================================================================

@app.get("/api/v1/patterns")
async def list_patterns(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    user: User = Depends(get_current_user),
    _: None = Depends(check_rate_limit)
):
    """
    List accessible patterns for user's tier

    - **page**: Page number (default: 1)
    - **per_page**: Patterns per page (default: 20, max: 100)
    - **category**: Filter by category (optional)
    """
    offset = (page - 1) * per_page

    # Build query based on user's tier
    tier_filter = {
        "free": "WHERE p.tier = 'community'",
        "developer": "WHERE p.tier IN ('community', 'basic')",
        "team": "WHERE p.tier IN ('community', 'basic', 'premium')",
        "enterprise": ""  # No filter - access all
    }

    where_clause = tier_filter.get(user.subscription_tier, "WHERE p.tier = 'community'")

    if category:
        if where_clause:
            where_clause += f" AND p.category = '{category}'"
        else:
            where_clause = f"WHERE p.category = '{category}'"

    # Query patterns
    query = f"""
        SELECT
            p.id,
            p.pattern_id,
            p.name,
            p.description,
            p.category,
            p.tier,
            p.usage_count,
            p.created_at
        FROM patterns p
        {where_clause}
        ORDER BY p.usage_count DESC, p.created_at DESC
        LIMIT {per_page} OFFSET {offset}
    """

    patterns = db.execute(query)

    # Count total
    count_query = f"SELECT COUNT(*) as total FROM patterns p {where_clause}"
    total = db.execute(count_query)[0]['total']

    return {
        "patterns": patterns,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page
    }


@app.get("/api/v1/patterns/{pattern_id}")
async def get_pattern(
    pattern_id: str,
    user: User = Depends(get_current_user),
    _: None = Depends(check_rate_limit)
):
    """
    Get specific pattern by ID

    - **pattern_id**: Pattern identifier
    """
    # Query pattern
    query = """
        SELECT
            p.id,
            p.pattern_id,
            p.name,
            p.description,
            p.category,
            p.tier,
            p.code,
            p.usage_count,
            p.created_at,
            p.updated_at
        FROM patterns p
        WHERE p.pattern_id = %s
    """

    result = db.execute(query, (pattern_id,))

    if not result:
        raise HTTPException(status_code=404, detail="Pattern not found")

    pattern = result[0]

    # Check access control
    if not user.can_access_pattern(Pattern(**pattern)):
        raise HTTPException(
            status_code=403,
            detail=f"Upgrade to {pattern['tier']} tier to access this pattern"
        )

    # Increment usage count
    db.execute(
        "UPDATE patterns SET usage_count = usage_count + 1 WHERE pattern_id = %s",
        (pattern_id,)
    )

    return pattern


@app.get("/api/v1/patterns/search")
async def search_patterns(
    q: str = Query(..., min_length=3),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    _: None = Depends(check_rate_limit)
):
    """
    Search patterns by text query

    - **q**: Search query
    - **limit**: Maximum results (default: 20, max: 100)
    """
    # Build tier filter
    tier_filter = {
        "free": "AND p.tier = 'community'",
        "developer": "AND p.tier IN ('community', 'basic')",
        "team": "AND p.tier IN ('community', 'basic', 'premium')",
        "enterprise": ""
    }

    tier_where = tier_filter.get(user.subscription_tier, "AND p.tier = 'community'")

    # Full-text search query
    query = f"""
        SELECT
            p.id,
            p.pattern_id,
            p.name,
            p.description,
            p.category,
            p.tier,
            ts_rank(p.search_vector, plainto_tsquery('english', %s)) as rank
        FROM patterns p
        WHERE p.search_vector @@ plainto_tsquery('english', %s)
        {tier_where}
        ORDER BY rank DESC
        LIMIT %s
    """

    patterns = db.execute(query, (q, q, limit))

    return {
        "patterns": patterns,
        "total": len(patterns),
        "query": q
    }


@app.post("/api/v1/patterns/search/semantic")
async def semantic_search(
    request: PatternSearchRequest,
    user: User = Depends(get_current_user),
    _: None = Depends(check_rate_limit)
):
    """
    Semantic search using vector embeddings

    - **query**: Natural language search query
    - **limit**: Maximum results (default: 10)
    """
    from .embeddings import generate_embedding

    # Generate embedding for query
    query_embedding = generate_embedding(request.query)

    # Build tier filter
    tier_filter = {
        "free": "AND p.tier = 'community'",
        "developer": "AND p.tier IN ('community', 'basic')",
        "team": "AND p.tier IN ('community', 'basic', 'premium')",
        "enterprise": ""
    }

    tier_where = tier_filter.get(user.subscription_tier, "")

    # Vector similarity search using pgvector
    query = f"""
        SELECT
            p.id,
            p.pattern_id,
            p.name,
            p.description,
            p.category,
            p.tier,
            1 - (p.embedding <=> %s::vector) as similarity_score
        FROM patterns p
        WHERE p.embedding IS NOT NULL
        {tier_where}
        ORDER BY p.embedding <=> %s::vector
        LIMIT %s
    """

    patterns = db.execute(query, (query_embedding, query_embedding, request.limit))

    return {
        "patterns": patterns,
        "total": len(patterns),
        "query": request.query
    }


# ============================================================================
# Usage & Analytics Endpoints
# ============================================================================

@app.get("/api/v1/usage/stats")
async def get_usage_stats(
    user: User = Depends(get_current_user)
):
    """Get API usage statistics for current user"""
    # Get current month usage
    month_key = f"monthly_quota:{user.id}:{datetime.now().strftime('%Y-%m')}"
    monthly_usage = redis_client.get(month_key)
    monthly_usage = int(monthly_usage) if monthly_usage else 0

    # Get quota
    monthly_quota = user.get_monthly_quota()

    # Get rate limit
    rate_limit = user.get_rate_limit()

    return {
        "subscription_tier": user.subscription_tier,
        "monthly_usage": monthly_usage,
        "monthly_quota": monthly_quota if monthly_quota != float('inf') else "unlimited",
        "quota_remaining": monthly_quota - monthly_usage if monthly_quota != float('inf') else "unlimited",
        "rate_limit_per_minute": rate_limit if rate_limit != float('inf') else "unlimited"
    }


@app.get("/api/v1/usage/quota")
async def check_quota(
    user: User = Depends(get_current_user)
):
    """Check if user is within quota"""
    within_quota = rate_limiter.check_monthly_quota(user)

    return {
        "within_quota": within_quota,
        "subscription_tier": user.subscription_tier
    }


# ============================================================================
# Health & Status
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "SpecQL Pattern API",
        "version": "1.0.0",
        "documentation": "/docs",
        "status": "operational"
    }
```

**Run Tests (Should Pass)**:
```bash
uv run pytest tests/unit/pattern_api/test_endpoints.py -v
```

---

**Day 1 Summary**:
- ✅ API architecture designed
- ✅ Authentication system (API keys + JWT)
- ✅ Rate limiting per tier
- ✅ Pattern endpoints with access control
- ✅ Semantic search integration
- ✅ Usage tracking

---

### Day 2: Stripe Billing Integration

**Objective**: Integrate Stripe for subscription management and usage-based billing

**Morning Block (4 hours): Stripe Setup**

#### 🔴 RED: Billing Tests (2 hours)

**Test File**: `tests/unit/pattern_api/test_billing.py`

```python
"""Tests for Stripe billing integration"""

import pytest
from src.pattern_api.billing import StripeService, Subscription


class TestStripeBilling:
    """Test Stripe integration"""

    @pytest.fixture
    def stripe_service(self):
        return StripeService(api_key="sk_test_...")

    def test_create_customer(self, stripe_service):
        """Test creating Stripe customer"""
        # Arrange
        email = "test@example.com"

        # Act
        customer = stripe_service.create_customer(email)

        # Assert
        assert customer.id.startswith("cus_")
        assert customer.email == email

    def test_create_subscription_developer_tier(self, stripe_service):
        """Test creating developer tier subscription"""
        # Arrange
        customer_id = "cus_test123"

        # Act
        subscription = stripe_service.create_subscription(
            customer_id=customer_id,
            price_id="price_developer_monthly"
        )

        # Assert
        assert subscription.id.startswith("sub_")
        assert subscription.status == "active"
        assert subscription.items[0].price.id == "price_developer_monthly"

    def test_upgrade_subscription(self, stripe_service):
        """Test upgrading from developer to team tier"""
        # Arrange
        subscription_id = "sub_test123"

        # Act
        updated_subscription = stripe_service.upgrade_subscription(
            subscription_id=subscription_id,
            new_price_id="price_team_monthly"
        )

        # Assert
        assert updated_subscription.items[0].price.id == "price_team_monthly"

    def test_cancel_subscription(self, stripe_service):
        """Test canceling subscription"""
        # Arrange
        subscription_id = "sub_test123"

        # Act
        canceled = stripe_service.cancel_subscription(subscription_id)

        # Assert
        assert canceled.status == "canceled"

    def test_webhook_payment_succeeded(self, stripe_service):
        """Test handling successful payment webhook"""
        # Arrange
        webhook_data = {
            "type": "invoice.payment_succeeded",
            "data": {
                "object": {
                    "customer": "cus_test123",
                    "amount_paid": 2900,  # $29.00
                    "subscription": "sub_test123"
                }
            }
        }

        # Act
        result = stripe_service.handle_webhook(webhook_data)

        # Assert
        assert result["status"] == "success"

    def test_usage_based_billing(self, stripe_service):
        """Test recording usage for metered billing"""
        # Arrange
        subscription_item_id = "si_test123"
        quantity = 100  # 100 API calls

        # Act
        usage_record = stripe_service.record_usage(
            subscription_item_id=subscription_item_id,
            quantity=quantity
        )

        # Assert
        assert usage_record.quantity == quantity
```

---

#### 🟢 GREEN: Implement Stripe Integration (2 hours)

**Billing Service**: `src/pattern_api/billing.py`

```python
"""
Stripe Billing Integration

Handles subscriptions, payments, and usage-based billing.
"""

import stripe
from typing import Optional, Dict, Any
from datetime import datetime
from .models import User


class StripeService:
    """Stripe billing service"""

    def __init__(self, api_key: str):
        stripe.api_key = api_key

        # Price IDs (set these in Stripe dashboard)
        self.price_ids = {
            "developer_monthly": "price_developer_monthly",
            "developer_annual": "price_developer_annual",
            "team_monthly": "price_team_monthly",
            "team_annual": "price_team_annual",
            "enterprise_monthly": "price_enterprise_monthly",
        }

    def create_customer(self, email: str, name: Optional[str] = None) -> stripe.Customer:
        """
        Create Stripe customer

        Args:
            email: Customer email
            name: Customer name (optional)

        Returns:
            Stripe Customer object
        """
        return stripe.Customer.create(
            email=email,
            name=name,
            metadata={"source": "specql_pattern_api"}
        )

    def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        trial_days: int = 14
    ) -> stripe.Subscription:
        """
        Create subscription for customer

        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID
            trial_days: Free trial days (default: 14)

        Returns:
            Stripe Subscription object
        """
        return stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            trial_period_days=trial_days,
            metadata={"source": "specql_pattern_api"}
        )

    def upgrade_subscription(
        self,
        subscription_id: str,
        new_price_id: str
    ) -> stripe.Subscription:
        """
        Upgrade subscription to new tier

        Args:
            subscription_id: Existing subscription ID
            new_price_id: New price ID

        Returns:
            Updated Stripe Subscription object
        """
        subscription = stripe.Subscription.retrieve(subscription_id)

        return stripe.Subscription.modify(
            subscription_id,
            items=[{
                "id": subscription["items"]["data"][0].id,
                "price": new_price_id,
            }],
            proration_behavior="create_prorations"
        )

    def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True
    ) -> stripe.Subscription:
        """
        Cancel subscription

        Args:
            subscription_id: Subscription to cancel
            at_period_end: Cancel at end of billing period (default: True)

        Returns:
            Canceled Stripe Subscription object
        """
        if at_period_end:
            return stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
        else:
            return stripe.Subscription.delete(subscription_id)

    def record_usage(
        self,
        subscription_item_id: str,
        quantity: int,
        action: str = "increment"
    ) -> stripe.UsageRecord:
        """
        Record usage for metered billing

        Args:
            subscription_item_id: Subscription item ID
            quantity: Usage quantity
            action: "increment" or "set" (default: increment)

        Returns:
            Stripe UsageRecord object
        """
        return stripe.UsageRecord.create(
            subscription_item=subscription_item_id,
            quantity=quantity,
            action=action,
            timestamp=int(datetime.now().timestamp())
        )

    def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle Stripe webhook events

        Args:
            payload: Webhook payload from Stripe

        Returns:
            Response dictionary
        """
        event_type = payload.get("type")

        if event_type == "invoice.payment_succeeded":
            return self._handle_payment_succeeded(payload["data"]["object"])

        elif event_type == "invoice.payment_failed":
            return self._handle_payment_failed(payload["data"]["object"])

        elif event_type == "customer.subscription.deleted":
            return self._handle_subscription_deleted(payload["data"]["object"])

        elif event_type == "customer.subscription.updated":
            return self._handle_subscription_updated(payload["data"]["object"])

        else:
            return {"status": "ignored", "event": event_type}

    def _handle_payment_succeeded(self, invoice: Dict) -> Dict:
        """Handle successful payment"""
        customer_id = invoice["customer"]
        subscription_id = invoice["subscription"]
        amount_paid = invoice["amount_paid"]

        # Update user subscription status in database
        # (Implementation depends on your database schema)

        return {
            "status": "success",
            "customer_id": customer_id,
            "subscription_id": subscription_id,
            "amount_paid": amount_paid
        }

    def _handle_payment_failed(self, invoice: Dict) -> Dict:
        """Handle failed payment"""
        customer_id = invoice["customer"]
        subscription_id = invoice["subscription"]

        # Send email notification
        # Downgrade user to free tier after grace period

        return {
            "status": "payment_failed",
            "customer_id": customer_id,
            "subscription_id": subscription_id
        }

    def _handle_subscription_deleted(self, subscription: Dict) -> Dict:
        """Handle subscription cancellation"""
        customer_id = subscription["customer"]
        subscription_id = subscription["id"]

        # Downgrade user to free tier

        return {
            "status": "subscription_deleted",
            "customer_id": customer_id,
            "subscription_id": subscription_id
        }

    def _handle_subscription_updated(self, subscription: Dict) -> Dict:
        """Handle subscription update (upgrade/downgrade)"""
        customer_id = subscription["customer"]
        subscription_id = subscription["id"]
        new_price_id = subscription["items"]["data"][0]["price"]["id"]

        # Update user tier in database

        return {
            "status": "subscription_updated",
            "customer_id": customer_id,
            "subscription_id": subscription_id,
            "new_price_id": new_price_id
        }
```

---

**Afternoon Block (4 hours): Webhook Handler & Subscription Management**

Create FastAPI endpoints for:
- Stripe webhooks
- Subscription management (create, upgrade, cancel)
- Checkout session creation
- Customer portal

**Day 2 Summary**:
- ✅ Stripe integration complete
- ✅ Subscription creation/management
- ✅ Webhook handling
- ✅ Usage-based billing
- ✅ Customer portal integration

---

### Days 3-5: Multi-Region Deployment & Launch Prep

**Day 3**: Deploy to AWS (US-EAST-1 + EU-WEST-1)
**Day 4**: Monitoring, analytics dashboard, admin panel
**Day 5**: Load testing, documentation, marketing site

---

## Week 63 Summary

**Achievements**:
- ✅ Pattern API deployed to production
- ✅ Authentication system (API keys + JWT)
- ✅ Rate limiting per tier
- ✅ Stripe billing integration
- ✅ Multi-region deployment
- ✅ Usage analytics
- ✅ Ready for first customers

**Lines of Code**:
- Authentication: ~800 lines
- API endpoints: ~1,200 lines
- Billing: ~600 lines
- Deployment configs: ~400 lines
- Tests: ~1,000 lines
- **Total: ~4,000 lines**

---

## Week 64: Pattern Marketplace & Growth Features

**Focus**:
1. Pattern creator portal
2. Pattern submission & review workflow
3. Revenue sharing (80/20 split)
4. AI-powered pattern recommendations
5. Analytics dashboard
6. First 100 paying customers

---

## Success Metrics

- [ ] Pattern API live in production
- [ ] 1,000+ free tier users
- [ ] 100+ paying customers
- [ ] $5k MRR by end of Week 64
- [ ] 99.9% uptime
- [ ] <100ms API response time (p95)
- [ ] Pattern marketplace operational
- [ ] First pattern sales ($10k GMV)

---

**Status**: 🔴 Ready to Execute
**Priority**: Critical (Monetization infrastructure)
**Expected Output**: Production Pattern API with paying customers
