# Weeks 65-66: Pattern Marketplace & Growth Engine

**Date**: 2025-11-13
**Duration**: 10 days (2 weeks)
**Status**: 🔴 Planning
**Objective**: Launch two-sided pattern marketplace with creator revenue sharing and growth features

**Prerequisites**: Week 63-64 complete (Pattern API Foundation)
**Output**: Live marketplace with pattern creators, AI recommendations, growth loops, $20k GMV

---

## 🎯 Executive Summary

Build a **two-sided marketplace** where pattern creators earn 80% revenue and SpecQL takes 20% commission:

```
Pattern Creators (Supply) ←→ SpecQL Marketplace ←→ Pattern Consumers (Demand)
        ↓                            ↓                           ↓
   Earn 80% revenue            Take 20% commission         Access patterns
   Build reputation            Scale revenue               Save dev time
   Community status            Network effects             Quality assured
```

### The Flywheel

```
More patterns → Better marketplace → More consumers →
    More revenue → Attracts creators → More patterns
```

### Success Criteria

- [ ] Pattern creator portal operational
- [ ] Pattern submission & review workflow
- [ ] Revenue sharing (80/20 Stripe Connect)
- [ ] 50+ active pattern creators
- [ ] 500+ patterns in marketplace
- [ ] $20k GMV (Gross Merchandise Value)
- [ ] $4k revenue (20% commission)
- [ ] AI-powered recommendations
- [ ] Pattern analytics dashboard

---

## Week 65: Pattern Creator Portal & Submission System

**Objective**: Enable pattern creators to submit, manage, and monetize their patterns

### Day 1: Creator Portal Design & Authentication

**Morning Block (4 hours): Creator Portal Architecture**

#### 1. Creator Portal Design (2 hours)

**Design Document**: `docs/pattern_api/CREATOR_PORTAL_DESIGN.md`

```markdown
# Pattern Creator Portal

## Creator Tiers

### Free Creator
- Upload up to 10 patterns
- Community tier patterns only
- 80% revenue share on sales
- Standard review queue

### Pro Creator ($49/month)
- Unlimited pattern uploads
- Premium tier patterns allowed
- 85% revenue share
- Priority review queue
- Analytics dashboard
- Featured placement

### Enterprise Creator (Custom)
- Private pattern libraries
- Custom pricing
- White-label options
- Dedicated support
- 90% revenue share

## Creator Dashboard

### Overview Tab
```
┌─────────────────────────────────────────┐
│ Revenue (This Month)                    │
│ $1,247.50  ↑ 23% from last month       │
├─────────────────────────────────────────┤
│ Pattern Stats                           │
│ • 15 patterns published                 │
│ • 247 total downloads                   │
│ • 4.8⭐ average rating                  │
├─────────────────────────────────────────┤
│ Recent Activity                         │
│ • "SOC2 Compliance Workflow" sold: $50 │
│ • "Multi-tenant SaaS" sold: $25        │
│ • New review: 5⭐ on "Auth Pattern"    │
└─────────────────────────────────────────┘
```

### My Patterns Tab
```
┌─────────────────────────────────────────┐
│ Pattern: "SOC2 Compliance Workflow"     │
│ Status: ✅ Published                    │
│ Price: $50                              │
│ Sales: 24 ($1,200 total)                │
│ Rating: 4.9⭐ (18 reviews)             │
│ [Edit] [Analytics] [Archive]            │
├─────────────────────────────────────────┤
│ Pattern: "Multi-step Approval"          │
│ Status: ⏳ Under Review                 │
│ Submitted: 2 days ago                   │
│ [View Feedback] [Edit]                  │
└─────────────────────────────────────────┘
```

### Analytics Tab
```
┌─────────────────────────────────────────┐
│ Downloads Over Time                     │
│ [Line chart showing trend]              │
├─────────────────────────────────────────┤
│ Top Performing Patterns                 │
│ 1. SOC2 Compliance - $1,200 revenue    │
│ 2. Auth Workflow - $800 revenue        │
│ 3. Multi-tenant - $600 revenue         │
├─────────────────────────────────────────┤
│ Geographic Distribution                 │
│ US: 45% | EU: 30% | Asia: 15% | Other │
└─────────────────────────────────────────┘
```

## Pattern Submission Workflow

```
Creator submits pattern →
    Automated validation →
        Manual review queue →
            Approved/Rejected →
                Published to marketplace
```

### Validation Steps (Automated)

1. **Code Quality**
   - Syntax validation
   - Test coverage >80%
   - Documentation present

2. **Security Scan**
   - No hardcoded secrets
   - SQL injection checks
   - XSS vulnerability checks

3. **Licensing**
   - Compatible license
   - No copyright violations

4. **Metadata Completeness**
   - Name, description, category
   - Tags, use cases
   - Example usage
   - Screenshots/demos

### Review Process (Manual)

**Fast Track** (Pro Creators, <24 hours):
- Automated checks passed
- Reputation score >4.5⭐
- Previous patterns approved

**Standard** (Free Creators, 2-5 days):
- Automated checks passed
- Manual code review
- Test execution verification

**Flagged** (Any creator, 5-10 days):
- Failed automated checks
- Potential issues found
- Detailed review required

## Revenue Sharing (Stripe Connect)

### Setup
```
1. Creator signs up
2. Connect Stripe account (Stripe Connect)
3. Set pattern pricing
4. Submit pattern
5. Pattern approved
6. Pattern sold
7. Revenue split automatically:
   - Creator: 80% → Their Stripe account
   - SpecQL: 20% → Platform fee
```

### Payout Schedule
- **Standard**: Weekly (Friday)
- **Pro**: Daily
- **Minimum payout**: $25

### Fees Breakdown
```
Pattern Price: $100
  ├─ Creator (80%): $80
  ├─ SpecQL (20%): $20
  │   ├─ Stripe fees (2.9% + $0.30): ~$3.20
  │   └─ Net platform fee: ~$16.80
  └─ Creator receives: $80 - Stripe fees
```
```

---

#### 🔴 RED: Creator Portal Tests (1 hour)

**Test File**: `tests/unit/pattern_api/test_creator_portal.py`

```python
"""Tests for pattern creator portal"""

import pytest
from src.pattern_api.creator import CreatorService, PatternSubmission
from src.pattern_api.models import User, Pattern


class TestCreatorPortal:
    """Test creator portal functionality"""

    @pytest.fixture
    def creator_service(self):
        return CreatorService(db=None, stripe=None)

    @pytest.fixture
    def creator_user(self):
        return User(
            id=1,
            email="creator@example.com",
            subscription_tier="pro_creator",
            stripe_account_id="acct_creator123"
        )

    def test_submit_pattern(self, creator_service, creator_user):
        """Test submitting new pattern"""
        # Arrange
        submission = PatternSubmission(
            name="SOC2 Compliance Workflow",
            description="Complete SOC2 compliance pattern",
            category="compliance",
            code="# Pattern code here",
            price=50.00,
            tier="premium"
        )

        # Act
        pattern = creator_service.submit_pattern(creator_user, submission)

        # Assert
        assert pattern.id is not None
        assert pattern.status == "under_review"
        assert pattern.creator_id == creator_user.id
        assert pattern.price == 50.00

    def test_validate_pattern_success(self, creator_service):
        """Test pattern validation passes"""
        # Arrange
        pattern_code = """
# Valid pattern with tests and documentation
entity: User
fields:
  email: email!
  name: text
"""

        # Act
        validation_result = creator_service.validate_pattern(pattern_code)

        # Assert
        assert validation_result.is_valid is True
        assert len(validation_result.errors) == 0

    def test_validate_pattern_missing_docs(self, creator_service):
        """Test pattern validation fails on missing docs"""
        # Arrange
        pattern_code = "entity: User"  # No description

        # Act
        validation_result = creator_service.validate_pattern(pattern_code)

        # Assert
        assert validation_result.is_valid is False
        assert "Missing description" in validation_result.errors

    def test_approve_pattern(self, creator_service, creator_user):
        """Test approving submitted pattern"""
        # Arrange
        pattern = Pattern(
            id=1,
            status="under_review",
            creator_id=creator_user.id
        )

        # Act
        approved_pattern = creator_service.approve_pattern(pattern.id)

        # Assert
        assert approved_pattern.status == "published"
        assert approved_pattern.published_at is not None

    def test_reject_pattern(self, creator_service):
        """Test rejecting submitted pattern"""
        # Arrange
        pattern_id = 1
        reason = "Missing test coverage"

        # Act
        rejected_pattern = creator_service.reject_pattern(pattern_id, reason)

        # Assert
        assert rejected_pattern.status == "rejected"
        assert rejected_pattern.rejection_reason == reason

    def test_creator_revenue_calculation(self, creator_service, creator_user):
        """Test calculating creator revenue (80% split)"""
        # Arrange
        pattern_price = 100.00

        # Act
        revenue_split = creator_service.calculate_revenue_split(pattern_price)

        # Assert
        assert revenue_split["creator_amount"] == 80.00
        assert revenue_split["platform_fee"] == 20.00
        assert revenue_split["total"] == 100.00

    def test_creator_dashboard_stats(self, creator_service, creator_user):
        """Test fetching creator dashboard statistics"""
        # Act
        stats = creator_service.get_creator_stats(creator_user.id)

        # Assert
        assert "total_revenue" in stats
        assert "pattern_count" in stats
        assert "total_downloads" in stats
        assert "average_rating" in stats
```

---

#### 🟢 GREEN: Implement Creator Service (2 hours)

**Creator Service**: `src/pattern_api/creator.py`

```python
"""
Pattern Creator Service

Handles pattern submission, validation, and creator revenue.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import stripe
from .models import User, Pattern
from .validation import PatternValidator


@dataclass
class PatternSubmission:
    """Pattern submission data"""
    name: str
    description: str
    category: str
    code: str
    price: float
    tier: str = "community"
    tags: List[str] = None
    use_cases: List[str] = None


@dataclass
class ValidationResult:
    """Pattern validation result"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class CreatorService:
    """Service for pattern creators"""

    def __init__(self, db, stripe_client):
        self.db = db
        self.stripe = stripe_client
        self.validator = PatternValidator()

    def submit_pattern(
        self,
        creator: User,
        submission: PatternSubmission
    ) -> Pattern:
        """
        Submit new pattern for review

        Args:
            creator: User submitting pattern
            submission: Pattern submission data

        Returns:
            Created Pattern object
        """
        # Validate pattern
        validation = self.validate_pattern(submission.code)

        if not validation.is_valid:
            raise ValueError(f"Pattern validation failed: {validation.errors}")

        # Check creator limits
        if not self._can_submit_pattern(creator):
            raise ValueError(
                f"Pattern limit reached for {creator.subscription_tier} tier. "
                "Upgrade to Pro Creator for unlimited patterns."
            )

        # Create pattern
        query = """
            INSERT INTO patterns (
                creator_id,
                name,
                description,
                category,
                code,
                price,
                tier,
                status,
                submitted_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            RETURNING id, pattern_id, status
        """

        result = self.db.execute(query, (
            creator.id,
            submission.name,
            submission.description,
            submission.category,
            submission.code,
            submission.price,
            submission.tier,
            "under_review"
        ))

        pattern_data = result[0]

        # Send notification to review queue
        self._notify_review_queue(pattern_data['id'])

        return Pattern(**pattern_data)

    def validate_pattern(self, pattern_code: str) -> ValidationResult:
        """
        Validate pattern code

        Args:
            pattern_code: Pattern YAML/code

        Returns:
            ValidationResult with errors/warnings
        """
        errors = []
        warnings = []

        # 1. Syntax validation
        try:
            self.validator.validate_syntax(pattern_code)
        except SyntaxError as e:
            errors.append(f"Syntax error: {str(e)}")

        # 2. Required fields
        if not self.validator.has_description(pattern_code):
            errors.append("Missing description field")

        if not self.validator.has_examples(pattern_code):
            warnings.append("No usage examples provided")

        # 3. Security checks
        security_issues = self.validator.check_security(pattern_code)
        errors.extend(security_issues)

        # 4. Test coverage
        if not self.validator.has_tests(pattern_code):
            errors.append("Missing test coverage")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def approve_pattern(self, pattern_id: int, reviewer_id: Optional[int] = None) -> Pattern:
        """
        Approve pattern for publication

        Args:
            pattern_id: Pattern to approve
            reviewer_id: Admin who approved (optional)

        Returns:
            Updated Pattern object
        """
        query = """
            UPDATE patterns
            SET
                status = 'published',
                published_at = NOW(),
                reviewed_by = %s,
                reviewed_at = NOW()
            WHERE id = %s
            RETURNING *
        """

        result = self.db.execute(query, (reviewer_id, pattern_id))

        if not result:
            raise ValueError(f"Pattern {pattern_id} not found")

        pattern = Pattern(**result[0])

        # Generate embeddings for semantic search
        self._generate_embeddings(pattern_id)

        # Notify creator
        self._notify_creator_approval(pattern.creator_id, pattern)

        return pattern

    def reject_pattern(self, pattern_id: int, reason: str) -> Pattern:
        """
        Reject pattern submission

        Args:
            pattern_id: Pattern to reject
            reason: Rejection reason

        Returns:
            Updated Pattern object
        """
        query = """
            UPDATE patterns
            SET
                status = 'rejected',
                rejection_reason = %s,
                reviewed_at = NOW()
            WHERE id = %s
            RETURNING *
        """

        result = self.db.execute(query, (reason, pattern_id))

        pattern = Pattern(**result[0])

        # Notify creator with feedback
        self._notify_creator_rejection(pattern.creator_id, pattern, reason)

        return pattern

    def calculate_revenue_split(self, pattern_price: float) -> Dict[str, float]:
        """
        Calculate revenue split (80/20)

        Args:
            pattern_price: Pattern sale price

        Returns:
            Dictionary with creator_amount, platform_fee, total
        """
        creator_amount = pattern_price * 0.80
        platform_fee = pattern_price * 0.20

        return {
            "creator_amount": creator_amount,
            "platform_fee": platform_fee,
            "total": pattern_price
        }

    def process_pattern_purchase(
        self,
        pattern_id: int,
        buyer_id: int,
        payment_intent_id: str
    ) -> Dict[str, Any]:
        """
        Process pattern purchase and split revenue

        Args:
            pattern_id: Pattern being purchased
            buyer_id: User purchasing pattern
            payment_intent_id: Stripe payment intent ID

        Returns:
            Purchase confirmation
        """
        # Get pattern and creator
        pattern = self._get_pattern(pattern_id)
        creator = self._get_user(pattern.creator_id)

        # Calculate split
        split = self.calculate_revenue_split(pattern.price)

        # Transfer to creator via Stripe Connect
        transfer = stripe.Transfer.create(
            amount=int(split["creator_amount"] * 100),  # Convert to cents
            currency="usd",
            destination=creator.stripe_account_id,
            transfer_group=f"pattern_purchase_{pattern_id}",
            metadata={
                "pattern_id": pattern_id,
                "buyer_id": buyer_id,
                "creator_id": creator.id
            }
        )

        # Record purchase
        query = """
            INSERT INTO pattern_purchases (
                pattern_id,
                buyer_id,
                creator_id,
                price,
                creator_revenue,
                platform_fee,
                stripe_payment_intent_id,
                stripe_transfer_id,
                purchased_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            RETURNING id
        """

        purchase_id = self.db.execute(query, (
            pattern_id,
            buyer_id,
            creator.id,
            pattern.price,
            split["creator_amount"],
            split["platform_fee"],
            payment_intent_id,
            transfer.id
        ))[0]['id']

        # Update pattern stats
        self._increment_pattern_sales(pattern_id)

        return {
            "purchase_id": purchase_id,
            "pattern_id": pattern_id,
            "price": pattern.price,
            "creator_revenue": split["creator_amount"],
            "platform_fee": split["platform_fee"]
        }

    def get_creator_stats(self, creator_id: int) -> Dict[str, Any]:
        """
        Get creator dashboard statistics

        Args:
            creator_id: Creator user ID

        Returns:
            Statistics dictionary
        """
        # Total revenue
        revenue_query = """
            SELECT SUM(creator_revenue) as total_revenue
            FROM pattern_purchases
            WHERE creator_id = %s
        """
        revenue = self.db.execute(revenue_query, (creator_id,))[0]['total_revenue'] or 0

        # Pattern count
        pattern_query = """
            SELECT COUNT(*) as pattern_count
            FROM patterns
            WHERE creator_id = %s AND status = 'published'
        """
        pattern_count = self.db.execute(pattern_query, (creator_id,))[0]['pattern_count']

        # Total downloads
        downloads_query = """
            SELECT COUNT(*) as total_downloads
            FROM pattern_purchases
            WHERE creator_id = %s
        """
        downloads = self.db.execute(downloads_query, (creator_id,))[0]['total_downloads']

        # Average rating
        rating_query = """
            SELECT AVG(rating) as avg_rating
            FROM pattern_reviews
            WHERE pattern_id IN (
                SELECT id FROM patterns WHERE creator_id = %s
            )
        """
        avg_rating = self.db.execute(rating_query, (creator_id,))[0]['avg_rating'] or 0

        return {
            "total_revenue": float(revenue),
            "pattern_count": pattern_count,
            "total_downloads": downloads,
            "average_rating": round(float(avg_rating), 2)
        }

    def _can_submit_pattern(self, creator: User) -> bool:
        """Check if creator can submit more patterns"""
        pattern_limits = {
            "free": 10,
            "pro_creator": float('inf'),
            "enterprise_creator": float('inf')
        }

        limit = pattern_limits.get(creator.subscription_tier, 10)

        if limit == float('inf'):
            return True

        # Count current patterns
        query = "SELECT COUNT(*) as count FROM patterns WHERE creator_id = %s"
        count = self.db.execute(query, (creator.id,))[0]['count']

        return count < limit

    def _notify_review_queue(self, pattern_id: int):
        """Notify reviewers of new pattern submission"""
        # Send email/Slack notification to review team
        pass

    def _notify_creator_approval(self, creator_id: int, pattern: Pattern):
        """Notify creator of pattern approval"""
        # Send email with pattern URL
        pass

    def _notify_creator_rejection(self, creator_id: int, pattern: Pattern, reason: str):
        """Notify creator of pattern rejection"""
        # Send email with rejection reason and improvement suggestions
        pass

    def _generate_embeddings(self, pattern_id: int):
        """Generate vector embeddings for semantic search"""
        # Use LLM to generate embeddings
        pass

    def _get_pattern(self, pattern_id: int) -> Pattern:
        """Get pattern by ID"""
        query = "SELECT * FROM patterns WHERE id = %s"
        result = self.db.execute(query, (pattern_id,))
        return Pattern(**result[0])

    def _get_user(self, user_id: int) -> User:
        """Get user by ID"""
        query = "SELECT * FROM users WHERE id = %s"
        result = self.db.execute(query, (user_id,))
        return User(**result[0])

    def _increment_pattern_sales(self, pattern_id: int):
        """Increment pattern sales count"""
        query = "UPDATE patterns SET sales_count = sales_count + 1 WHERE id = %s"
        self.db.execute(query, (pattern_id,))
```

**Run Tests**:
```bash
uv run pytest tests/unit/pattern_api/test_creator_portal.py -v
```

---

**Afternoon Block (4 hours): Creator API Endpoints**

Add FastAPI endpoints for:
- POST `/api/v1/creator/patterns` - Submit pattern
- GET `/api/v1/creator/patterns` - List my patterns
- PUT `/api/v1/creator/patterns/{id}` - Update pattern
- DELETE `/api/v1/creator/patterns/{id}` - Delete pattern
- GET `/api/v1/creator/stats` - Dashboard stats
- POST `/api/v1/creator/stripe/connect` - Connect Stripe account

**Day 1 Summary**:
- ✅ Creator portal architecture
- ✅ Pattern submission workflow
- ✅ Pattern validation
- ✅ Revenue splitting logic
- ✅ Creator API endpoints

---

### Days 2-5: Marketplace Features & Growth Engine

**Day 2**: Pattern discovery & search (featured, trending, categories)
**Day 3**: AI recommendations engine (LLM-powered)
**Day 4**: Analytics dashboard & insights
**Day 5**: Growth features (referrals, affiliates, badges)

---

## Week 65 Summary

**Achievements**:
- ✅ Creator portal operational
- ✅ Pattern submission system
- ✅ Revenue sharing (80/20)
- ✅ Stripe Connect integration
- ✅ Pattern validation pipeline
- ✅ 50+ active creators

**Revenue**:
- $20k GMV (Gross Merchandise Value)
- $4k platform fee (20%)
- $16k to creators (80%)

---

## Week 66: Growth Loops & Viral Features

**Focus**:
1. Referral program (creators refer users)
2. Affiliate system (30% commission)
3. Pattern bundles (5 patterns for discount)
4. Creator badges & leaderboards
5. Social sharing & embeds
6. First 1,000 paying customers

---

## Success Metrics

- [ ] 50+ active pattern creators
- [ ] 500+ patterns in marketplace
- [ ] $20k GMV in first month
- [ ] $4k platform revenue
- [ ] 4.5⭐ average pattern rating
- [ ] 70% creator approval rate
- [ ] <24 hour review time (Pro creators)
- [ ] 30% month-over-month growth

---

**Status**: 🔴 Ready to Execute
**Priority**: Critical (Revenue growth)
**Expected Output**: Thriving two-sided marketplace with network effects
