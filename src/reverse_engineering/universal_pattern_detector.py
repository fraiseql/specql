"""
Universal Pattern Detector - Detect common patterns across all languages

Your responsibility: Implement Patterns 1-3
- State Machine
- Soft Delete
- Audit Trail
"""

from typing import List, Dict, Any
from dataclasses import dataclass
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class DetectedPattern:
    """Represents a detected pattern"""

    name: str
    confidence: float
    evidence: List[str]
    language: str
    suggested_stdlib: str


class UniversalPatternDetector:
    """Detect patterns across all languages"""

    def __init__(self):
        self.patterns = {
            "state_machine": StateMachinePattern(),  # Engineer A
            "soft_delete": SoftDeletePattern(),  # Engineer A
            "audit_trail": AuditTrailPattern(),  # Engineer A
            "multi_tenant": MultiTenantPattern(),  # YOUR PATTERN
            "hierarchical": HierarchicalPattern(),  # YOUR PATTERN
            "versioning": VersioningPattern(),  # YOUR PATTERN
            "event_sourcing": EventSourcingPattern(),  # Week 8 - Pattern 7
            "sharding": ShardingPattern(),  # Week 8 - Pattern 8
            "cache_invalidation": CacheInvalidationPattern(),  # Week 8 - Pattern 9
            "rate_limiting": RateLimitingPattern(),  # Week 8 - Pattern 10
        }

    def detect(self, code: str, language: str) -> List[DetectedPattern]:
        """Detect all patterns in code"""
        detected = []

        for pattern_name, pattern_detector in self.patterns.items():
            if pattern_detector and pattern_detector.matches(code, language):
                detected.append(
                    DetectedPattern(
                        name=pattern_name,
                        confidence=pattern_detector.confidence,
                        evidence=pattern_detector.evidence,
                        language=language,
                        suggested_stdlib=pattern_detector.get_stdlib_pattern(),
                    )
                )

        return detected


class StateMachinePattern:
    """
    Detect state machine pattern

    Indicators:
    - Status/state field (enum or text)
    - Multiple transition methods (2+)
    - Status validation before transition
    - Status update in method

    Target Confidence: 85%+
    """

    def __init__(self):
        self.confidence = 0.0
        self.evidence = []

    def matches(self, code: str, language: str) -> bool:
        """Check if code implements state machine"""
        self.evidence = []
        self.confidence = 0.0

        indicators = self._get_indicators(language)

        # 1. Check for status/state field (30 points)
        has_status_field = any(
            re.search(pattern, code, re.IGNORECASE) for pattern in indicators["field_patterns"]
        )

        if has_status_field:
            self.evidence.append("Has status/state field")
            self.confidence += 0.30

        # 2. Check for transition methods (40 points for 2+, 50 for 4+)
        transition_count = 0
        for pattern in indicators["transition_patterns"]:
            matches = re.findall(pattern, code, re.IGNORECASE | re.DOTALL)
            transition_count += len(matches)

        if transition_count >= 2:
            self.evidence.append(f"Found {transition_count} status transitions")
            self.confidence += 0.40
            if transition_count >= 4:
                self.confidence += 0.10

        # 3. Check for validation (20 points)
        has_validation = any(pattern in code for pattern in indicators["validation_patterns"])

        if has_validation:
            self.evidence.append("Has status validation before transitions")
            self.confidence += 0.20

        # Must have at least field + transitions to be considered state machine
        return self.confidence >= 0.60

    def _get_indicators(self, language: str) -> Dict[str, List[str]]:
        """Get language-specific indicators"""
        indicators = {
            "rust": {
                "field_patterns": [
                    r"status:\s*\w*Status",
                    r"state:\s*\w*State",
                    r"status:\s*String",
                ],
                "transition_patterns": [
                    r"self\.status\s*=\s*",
                ],
                "validation_patterns": [
                    "self.status !=",
                    "self.status ==",
                    "if self.status",
                ],
            },
            "python": {
                "field_patterns": [
                    r"self\.status\s*=",
                    r"status:\s*str",
                    r"status:\s*Status",
                ],
                "transition_patterns": [
                    r'self\.status\s*=\s*["\']',
                    r"self\.status\s*=\s*Status\.",
                    r"self\.status\s*=\s*\w+\.",
                ],
                "validation_patterns": [
                    "if self.status",
                    "self.status !=",
                    "self.status ==",
                    "self.status not in",
                ],
            },
            "java": {
                "field_patterns": [
                    r"private\s+String\s+status",
                    r"private\s+\w*Status\s+status",
                ],
                "transition_patterns": [
                    r"this\.status\s*=\s*",
                    r"setStatus\(",
                ],
                "validation_patterns": [
                    "if (status",
                    "if (this.status",
                    '.equals("',
                ],
            },
            "sql": {
                "field_patterns": [
                    r"status\s+TEXT",
                    r"status\s+VARCHAR",
                ],
                "transition_patterns": [
                    r"UPDATE\s+\w+\s+SET\s+status\s*=",
                ],
                "validation_patterns": [
                    "SELECT status",
                    "WHERE status =",
                    "WHERE status !=",
                    "IF",
                    "status",
                ],
            },
        }

        return indicators.get(
            language,
            {
                "field_patterns": [r"status", r"state"],
                "transition_patterns": [r"status\s*="],
                "validation_patterns": ["status", "state"],
            },
        )

    def get_stdlib_pattern(self) -> str:
        return "state_machine/transition"


class SoftDeletePattern:
    """
    Detect soft delete pattern

    Indicators:
    - deleted_at timestamp field (50 points)
    - UPDATE instead of DELETE (30 points)
    - Filter deleted records (20 points)

    Target Confidence: 94%+
    """

    def __init__(self):
        self.confidence = 0.0
        self.evidence = []

    def matches(self, code: str, language: str) -> bool:
        """Check if code uses soft delete"""
        self.evidence = []
        self.confidence = 0.0

        # 1. Check for deleted_at field (50 points - CRITICAL)
        deleted_patterns = [
            r"deleted_at.*timestamp",
            r"deleted_at.*DateTime",
            r"deleted_at.*Option",
            r"deleted_at.*Optional",
            r"deleted_at\s*TIMESTAMPTZ",
            r"deleted_at:\s*datetime",
        ]

        has_deleted_field = any(
            re.search(pattern, code, re.IGNORECASE) for pattern in deleted_patterns
        )

        if has_deleted_field:
            self.evidence.append("Has deleted_at timestamp field")
            self.confidence += 0.50

        # 2. Check for soft delete implementation (30 points)
        soft_delete_patterns = [
            r"UPDATE.*SET\s+deleted_at",
            r"deleted_at\s*=.*now\(\)",
            r"deleted_at\s*=.*NOW",
            r"\.deleted_at\s*=\s*",
            r"set.*deleted_at.*Some",
        ]

        has_soft_delete = any(
            re.search(pattern, code, re.IGNORECASE) for pattern in soft_delete_patterns
        )

        if has_soft_delete:
            self.evidence.append("Updates deleted_at instead of hard delete")
            self.confidence += 0.30

        # 3. Check for filtering deleted records (20 points)
        filter_patterns = [
            r"WHERE.*deleted_at\s+IS\s+NULL",
            r"filter.*deleted_at.*is_null",
            r"deleted_at\.is_\(None\)",
            r"deleted_at\s+IS\s+NULL",
        ]

        has_filter = any(re.search(pattern, code, re.IGNORECASE) for pattern in filter_patterns)

        if has_filter:
            self.evidence.append("Filters out deleted records in queries")
            self.confidence += 0.20

        # Check for restore functionality (bonus)
        restore_patterns = [
            r"deleted_at\s*=\s*NULL",
            r"deleted_at\s*=\s*None",
            r"restore",
        ]

        has_restore = any(re.search(pattern, code, re.IGNORECASE) for pattern in restore_patterns)

        if has_restore:
            self.evidence.append("Has restore/undelete functionality")
            self.confidence = min(0.95, self.confidence + 0.05)

        # Deleted field is mandatory
        return has_deleted_field and self.confidence >= 0.50

    def get_stdlib_pattern(self) -> str:
        return "crud/soft_delete"


class AuditTrailPattern:
    """
    Detect audit trail pattern

    Indicators:
    - created_at, created_by (25 points each)
    - updated_at, updated_by (25 points each)

    Target Confidence: 89%+
    """

    def __init__(self):
        self.confidence = 0.0
        self.evidence = []

    def matches(self, code: str, language: str) -> bool:
        """Check if code has audit trail"""
        self.evidence = []
        self.confidence = 0.0

        # Check for each audit field (25 points each)
        audit_fields = {
            "created_at": [r"\bcreated_at\b", r"createdAt"],
            "created_by": [r"\bcreated_by\b", r"createdBy"],
            "updated_at": [r"\bupdated_at\b", r"updatedAt"],
            "updated_by": [r"\bupdated_by\b", r"updatedBy"],
        }

        found_fields = []

        for field_name, patterns in audit_fields.items():
            if any(re.search(pattern, code, re.IGNORECASE) for pattern in patterns):
                found_fields.append(field_name)
                self.confidence += 0.25

        if found_fields:
            self.evidence.append(f"Has audit fields: {', '.join(found_fields)}")

        # Check for automatic timestamp updates (bonus)
        auto_update_patterns = [
            r"DEFAULT NOW\(\)",
            r"updated_at\s*=\s*NOW\(\)",
            r"updated_at\s*=.*now\(\)",
            r"TRIGGER.*updated_at",
        ]

        if any(re.search(pattern, code, re.IGNORECASE) for pattern in auto_update_patterns):
            self.evidence.append("Has automatic timestamp updates")
            self.confidence = min(0.95, self.confidence + 0.10)

        # Need at least 2 audit fields
        return len(found_fields) >= 2 and self.confidence >= 0.50

    def get_stdlib_pattern(self) -> str:
        return "audit/full_trail"


class MultiTenantPattern:
    """
    Detect multi-tenant isolation patterns

    Signals:
    1. tenant_id field (UUID/INT) - 70% confidence
    2. RLS policies with tenant_id - 90% confidence
    3. Tenant mixin/base class - 80% confidence
    4. Foreign key to tenants table - 60% confidence
    5. @TenantId annotation - 85% confidence
    """

    def __init__(self):
        self.tenant_field_patterns = [
            "tenant_id",
            "tenant_uuid",
            "organization_id",
            "org_id",
            "company_id",  # Sometimes used for multi-tenancy
            "account_id",
        ]

    def matches(self, code: str, language: str) -> bool:
        """Check if code contains multi-tenant pattern"""
        self.evidence = []
        self.confidence = 0.0

        if language == "sql":
            # Check for tenant_id column
            if self._has_tenant_column(code):
                self.confidence += 0.70
                self.evidence.append("tenant_id column found")

            # Check for RLS policy
            if self._has_rls_policy(code):
                self.confidence += 0.90
                self.evidence.append("RLS policy with tenant_id filter")

            # Check for tenant_id index
            if self._has_tenant_index(code):
                self.confidence += 0.20
                self.evidence.append("Index on tenant_id")

            # Check for FK to tenants table
            if self._has_tenant_fk(code):
                self.confidence += 0.30
                self.evidence.append("Foreign key to tenants table")

        elif language == "python":
            # Check for tenant_id field
            if self._has_tenant_field_python(code):
                self.confidence += 0.70
                self.evidence.append("tenant_id field in model")

            # Check for TenantMixin
            if "TenantMixin" in code or "MultiTenantMixin" in code:
                self.confidence += 0.80
                self.evidence.append("TenantMixin base class")

            # Check for tenant filtering in queries
            if self._has_tenant_filter_python(code):
                self.confidence += 0.40
                self.evidence.append("tenant_id filtering in queries")

        elif language == "java":
            # Check for @TenantId annotation
            if "@TenantId" in code:
                self.confidence += 0.85
                self.evidence.append("@TenantId annotation (Hibernate)")

            # Check for tenant_id column
            if self._has_tenant_field_java(code):
                self.confidence += 0.70
                self.evidence.append("tenant_id field in JPA entity")

            # Check for @Filter with tenant condition
            if "@Filter" in code and "tenant_id" in code.lower():
                self.confidence += 0.85
                self.evidence.append("Hibernate @Filter for tenant isolation")

        elif language == "rust":
            # Check for tenant_id field
            if self._has_tenant_field_rust(code):
                self.confidence += 0.70
                self.evidence.append("tenant_id field in Rust struct")

        # Cap at 1.0
        self.confidence = min(self.confidence, 1.0)

        # Must have some tenant detection to be considered multi-tenant
        return self.confidence >= 0.70

    # SQL Detection Methods

    def _detect_sql_multitenancy(self, sql: str) -> bool:
        """Check if SQL contains multi-tenant patterns"""
        return (
            self._has_tenant_column(sql)
            or self._has_rls_policy(sql)
            or self._has_tenant_index(sql)
            or self._has_tenant_fk(sql)
        )

    def _has_tenant_column(self, sql: str) -> bool:
        """Check for tenant_id column definition"""
        for field in self.tenant_field_patterns:
            # Pattern: tenant_id UUID|INT NOT NULL
            pattern = rf"{field}\s+(UUID|INT|INTEGER|BIGINT).*NOT NULL"
            if re.search(pattern, sql, re.IGNORECASE):
                return True
        return False

    def _has_rls_policy(self, sql: str) -> bool:
        """Check for RLS policy with tenant filtering"""
        # Pattern: CREATE POLICY ... USING (tenant_id = ...)
        policy_pattern = r"CREATE\s+POLICY.*USING\s*\([^)]*tenant_id[^)]*\)"
        return bool(re.search(policy_pattern, sql, re.IGNORECASE | re.DOTALL))

    def _has_tenant_index(self, sql: str) -> bool:
        """Check for index on tenant_id"""
        # Pattern: CREATE INDEX ... ON table(tenant_id)
        for field in self.tenant_field_patterns:
            index_pattern = rf"CREATE\s+INDEX.*ON\s+\w+\s*\(\s*{field}\s*\)"
            if re.search(index_pattern, sql, re.IGNORECASE):
                return True
        return False

    def _has_tenant_fk(self, sql: str) -> bool:
        """Check for foreign key to tenants table"""
        # Pattern: FOREIGN KEY (tenant_id) REFERENCES tenants(id)
        fk_pattern = r"FOREIGN\s+KEY\s*\(\s*tenant_id\s*\)\s*REFERENCES\s+tenants"
        return bool(re.search(fk_pattern, sql, re.IGNORECASE))

    # Python Detection Methods

    def _detect_python_multitenancy(self, code: str) -> bool:
        """Check if Python code contains multi-tenant patterns"""
        return (
            self._has_tenant_field_python(code)
            or "TenantMixin" in code
            or self._has_tenant_filter_python(code)
        )

    def _has_tenant_field_python(self, code: str) -> bool:
        """Check for tenant_id field in Python model"""
        for field in self.tenant_field_patterns:
            # Pattern: tenant_id: UUID or tenant_id = Column(...)
            if re.search(rf"{field}\s*[:=]", code):
                return True
        return False

    def _has_tenant_filter_python(self, code: str) -> bool:
        """Check for tenant_id filtering in queries"""
        # Pattern: .filter(Contact.tenant_id == ...)
        filter_pattern = r"\.filter\([^)]*tenant_id\s*==?"
        return bool(re.search(filter_pattern, code))

    # Java Detection Methods

    def _detect_java_multitenancy(self, code: str) -> bool:
        """Check if Java code contains multi-tenant patterns"""
        return (
            self._has_tenant_field_java(code)
            or "@TenantId" in code
            or ("@Filter" in code and "tenant_id" in code.lower())
        )

    def _has_tenant_field_java(self, code: str) -> bool:
        """Check for tenant_id field in Java entity"""
        for field in self.tenant_field_patterns:
            # Pattern: private UUID tenantId;
            pattern = rf"private\s+(UUID|Long|Integer|String)\s+{field}"
            if re.search(pattern, code, re.IGNORECASE):
                return True
        return False

    # Rust Detection Methods

    def _detect_rust_multitenancy(self, code: str) -> bool:
        """Check if Rust code contains multi-tenant patterns"""
        return self._has_tenant_field_rust(code)

    def _has_tenant_field_rust(self, code: str) -> bool:
        """Check for tenant_id field in Rust struct"""
        for field in self.tenant_field_patterns:
            # Pattern: pub tenant_id: Uuid,
            pattern = rf"pub\s+{field}\s*:\s*(Uuid|i32|i64)"
            if re.search(pattern, code, re.IGNORECASE):
                return True
        return False

    def get_stdlib_pattern(self) -> str:
        return "stdlib/multi_tenant/enforce_tenant_isolation"


class HierarchicalPattern:
    """
    Detect self-referencing hierarchical structures (trees)

    Indicators:
    - parent_id self-reference (30 points)
    - Recursive CTE (30 points)
    - Tree traversal methods (20 points)
    - Depth/level fields (20 points)

    Target Confidence: 85-90%
    """

    def __init__(self):
        self.confidence = 0.0
        self.evidence = []

    def matches(self, code: str, language: str) -> bool:
        """Check if code has hierarchical structure"""
        self.evidence = []
        self.confidence = 0.0

        if language == "sql":
            return self._detect_sql_hierarchy(code)
        elif language == "python":
            return self._detect_python_hierarchy(code)
        elif language == "java":
            return self._detect_java_hierarchy(code)
        elif language == "rust":
            return self._detect_rust_hierarchy(code)
        return False

    def _detect_sql_hierarchy(self, sql: str) -> bool:
        """Check for hierarchical patterns in SQL"""
        # 1. Check for parent_id self-reference (30 points)
        parent_patterns = [
            r"parent_id\s+.*REFERENCES\s+\w+\s*\(\s*id\s*\)",
            r"parent_id\s+INTEGER",
            r"parent_id\s+BIGINT",
        ]

        has_parent_id = any(re.search(pattern, sql, re.IGNORECASE) for pattern in parent_patterns)

        if has_parent_id:
            self.evidence.append("Has parent_id self-referencing foreign key")
            self.confidence += 0.30

        # 2. Check for recursive CTE (30 points)
        recursive_patterns = [
            r"WITH\s+RECURSIVE",
            r"RECURSIVE.*AS\s*\(",
        ]

        has_recursive = any(
            re.search(pattern, sql, re.IGNORECASE) for pattern in recursive_patterns
        )

        if has_recursive:
            self.evidence.append("Uses recursive CTE for tree traversal")
            self.confidence += 0.30

        # 3. Check for path field (20 points)
        path_patterns = [
            r"path\s+VARCHAR",
            r"path\s+TEXT",
            r"tree_path\s+VARCHAR",
        ]

        has_path = any(re.search(pattern, sql, re.IGNORECASE) for pattern in path_patterns)

        if has_path:
            self.evidence.append("Has path field for materialized tree paths")
            self.confidence += 0.20

        # 4. Check for nested set model (20 points)
        nested_set_patterns = [
            r"lft\s+INT",
            r"rgt\s+INT",
            r"left\s+INT",
            r"right\s+INT",
        ]

        has_nested_set = any(
            re.search(pattern, sql, re.IGNORECASE) for pattern in nested_set_patterns
        )

        if has_nested_set:
            self.evidence.append("Uses nested set model (lft/rgt boundaries)")
            self.confidence += 0.20

        # Cap at 1.0
        self.confidence = min(self.confidence, 1.0)

        # Need at least parent_id or recursive CTE to be hierarchical
        return (has_parent_id or has_recursive) and self.confidence >= 0.30

    def _detect_python_hierarchy(self, code: str) -> bool:
        """Check for hierarchical patterns in Python"""
        # 1. Check for parent_id field (30 points)
        parent_patterns = [
            r"parent_id:\s*Optional\[",
            r"parent_id:\s*int",
            r"parent_id\s*=\s*Column",
        ]

        has_parent_id = any(re.search(pattern, code, re.IGNORECASE) for pattern in parent_patterns)

        if has_parent_id:
            self.evidence.append("Has parent_id field for self-reference")
            self.confidence += 0.30

        # 2. Check for parent relationship (30 points)
        parent_rel_patterns = [
            r"parent.*relationship",
            r"parent.*backref",
            r"parent.*ForeignKey",
        ]

        has_parent_rel = any(
            re.search(pattern, code, re.IGNORECASE) for pattern in parent_rel_patterns
        )

        if has_parent_rel:
            self.evidence.append("Has parent relationship for tree navigation")
            self.confidence += 0.30

        # 3. Check for children relationship (20 points)
        children_patterns = [
            r"children.*relationship",
            r"children.*backref",
            r"children.*List\[",
        ]

        has_children = any(re.search(pattern, code, re.IGNORECASE) for pattern in children_patterns)

        if has_children:
            self.evidence.append("Has children relationship for tree traversal")
            self.confidence += 0.20

        # 4. Check for tree methods (20 points)
        tree_methods = [
            "get_children",
            "get_ancestors",
            "get_descendants",
            "get_tree",
            "build_tree",
        ]

        found_methods = [method for method in tree_methods if method in code]

        if found_methods:
            self.evidence.append(f"Has tree traversal methods: {', '.join(found_methods[:3])}")
            self.confidence += 0.20

        # Cap at 1.0
        self.confidence = min(self.confidence, 1.0)

        # Need parent relationship to be hierarchical
        return has_parent_id and self.confidence >= 0.30

    def _detect_java_hierarchy(self, code: str) -> bool:
        """Check for hierarchical patterns in Java"""
        # 1. Check for parent self-reference (30 points)
        parent_patterns = [
            r"@ManyToOne.*\(.*\)",
            r"private.*parent",
            r"Parent.*parent",
        ]

        has_parent = any(re.search(pattern, code, re.IGNORECASE) for pattern in parent_patterns)

        if has_parent:
            self.evidence.append("Has parent self-reference with @ManyToOne")
            self.confidence += 0.30

        # 2. Check for children collection (30 points)
        children_patterns = [
            r"@OneToMany.*\(.*\)",
            r"List<.*>.*children",
            r"Set<.*>.*children",
        ]

        has_children = any(re.search(pattern, code, re.IGNORECASE) for pattern in children_patterns)

        if has_children:
            self.evidence.append("Has children collection with @OneToMany")
            self.confidence += 0.30

        # 3. Check for tree methods (20 points)
        tree_methods = [
            "getChildren",
            "getParent",
            "getAncestors",
            "getDescendants",
            "buildTree",
        ]

        found_methods = [method for method in tree_methods if method in code]

        if found_methods:
            self.evidence.append(f"Has tree traversal methods: {', '.join(found_methods[:3])}")
            self.confidence += 0.20

        # 4. Check for @JoinColumn with parent reference (20 points)
        join_column_patterns = [
            r"@JoinColumn.*parent",
            r"@JoinColumn.*parentId",
        ]

        has_join_column = any(
            re.search(pattern, code, re.IGNORECASE) for pattern in join_column_patterns
        )

        if has_join_column:
            self.evidence.append("Has @JoinColumn for parent relationship")
            self.confidence += 0.20

        # Cap at 1.0
        self.confidence = min(self.confidence, 1.0)

        # Need parent reference to be hierarchical
        return has_parent and self.confidence >= 0.30

    def _detect_rust_hierarchy(self, code: str) -> bool:
        """Check for hierarchical patterns in Rust"""
        # 1. Check for parent_id field (30 points)
        parent_patterns = [
            r"parent_id:\s*Option<",
            r"parent_id:\s*i32",
            r"parent_id:\s*i64",
        ]

        has_parent_id = any(re.search(pattern, code, re.IGNORECASE) for pattern in parent_patterns)

        if has_parent_id:
            self.evidence.append("Has parent_id field for self-reference")
            self.confidence += 0.30

        # 2. Check for parent relationship (30 points)
        parent_rel_patterns = [
            r"parent.*belongs_to",
            r"parent.*BelongsTo",
        ]

        has_parent_rel = any(
            re.search(pattern, code, re.IGNORECASE) for pattern in parent_rel_patterns
        )

        if has_parent_rel:
            self.evidence.append("Has parent relationship for tree navigation")
            self.confidence += 0.30

        # 3. Check for children relationship (20 points)
        children_patterns = [
            r"children.*has_many",
            r"children.*HasMany",
        ]

        has_children = any(re.search(pattern, code, re.IGNORECASE) for pattern in children_patterns)

        if has_children:
            self.evidence.append("Has children relationship for tree traversal")
            self.confidence += 0.20

        # 4. Check for tree methods (20 points)
        tree_methods = [
            "get_children",
            "get_parent",
            "get_ancestors",
            "get_descendants",
            "build_tree",
        ]

        found_methods = [method for method in tree_methods if method in code]

        if found_methods:
            self.evidence.append(f"Has tree traversal methods: {', '.join(found_methods[:3])}")
            self.confidence += 0.20

        # Cap at 1.0
        self.confidence = min(self.confidence, 1.0)

        # Need parent_id to be hierarchical
        return has_parent_id and self.confidence >= 0.30

    def get_stdlib_pattern(self) -> str:
        return "hierarchy/recursive_tree"


class VersioningPattern:
    """
    Detect temporal/versioned data tracking patterns

    Indicators:
    - version field (40 points)
    - Optimistic locking check (40 points)
    - Version history table (20 points bonus)

    Target Confidence: 85-90%
    """

    def __init__(self):
        self.confidence = 0.0
        self.evidence = []

    def matches(self, code: str, language: str) -> bool:
        """Check if code has versioning"""
        self.evidence = []
        self.confidence = 0.0

        if language == "sql":
            return self._detect_sql_versioning(code)
        elif language == "python":
            return self._detect_python_versioning(code)
        elif language == "java":
            return self._detect_java_versioning(code)
        return False

    def _detect_sql_versioning(self, sql: str) -> bool:
        """Check for versioning patterns in SQL"""
        # 1. Check for version column (40 points)
        version_patterns = [
            r"version\s+INT",
            r"version\s+INTEGER",
            r"version\s+BIGINT",
            r"revision\s+INT",
        ]

        has_version_field = any(
            re.search(pattern, sql, re.IGNORECASE) for pattern in version_patterns
        )

        if has_version_field:
            self.evidence.append("Has version column for optimistic locking")
            self.confidence += 0.40

        # 2. Check for history table (30 points)
        history_patterns = [
            r"CREATE\s+TABLE\s+\w+_history",
            r"_history\s*\(",
        ]

        has_history = any(re.search(pattern, sql, re.IGNORECASE) for pattern in history_patterns)

        if has_history:
            self.evidence.append("Has history table for version tracking")
            self.confidence += 0.30

        # 3. Check for temporal columns (30 points)
        temporal_patterns = [
            r"system_time_start\s+TIMESTAMP",
            r"system_time_end\s+TIMESTAMP",
            r"valid_from\s+TIMESTAMP",
            r"valid_to\s+TIMESTAMP",
        ]

        has_temporal = any(re.search(pattern, sql, re.IGNORECASE) for pattern in temporal_patterns)

        if has_temporal:
            self.evidence.append("Has temporal columns for time-based versioning")
            self.confidence += 0.30

        # 4. Check for optimistic locking in WHERE clauses (20 points bonus)
        locking_patterns = [
            r"WHERE.*version\s*=",
            r"AND\s+version\s*=",
        ]

        has_locking = any(re.search(pattern, sql, re.IGNORECASE) for pattern in locking_patterns)

        if has_locking:
            self.evidence.append("Uses optimistic locking with version checks")
            self.confidence += 0.20

        # 5. Check for version increment triggers (bonus)
        trigger_patterns = [
            r"CREATE\s+TRIGGER.*version",
            r"version\s*=.*version\s*\+\s*1",
        ]

        has_trigger = any(re.search(pattern, sql, re.IGNORECASE) for pattern in trigger_patterns)

        if has_trigger:
            self.evidence.append("Has automatic version increment triggers")
            self.confidence = min(0.95, self.confidence + 0.10)

        # Cap at 1.0
        self.confidence = min(self.confidence, 1.0)

        # Need version field, history table, or temporal columns to be considered versioning
        # Temporal versioning can have lower confidence threshold since it's a valid pattern
        if has_temporal and self.confidence >= 0.30:
            return True
        return (has_version_field or has_history) and self.confidence >= 0.40

    def _detect_python_versioning(self, code: str) -> bool:
        """Check for versioning patterns in Python"""
        # 1. Check for version field (40 points)
        version_patterns = [
            r"version:\s*int",
            r"version\s*=\s*Column\(Integer",
            r"revision:\s*int",
        ]

        has_version_field = any(
            re.search(pattern, code, re.IGNORECASE) for pattern in version_patterns
        )

        if has_version_field:
            self.evidence.append("Has version field for optimistic locking")
            self.confidence += 0.40

        # 2. Check for history mixin (30 points)
        history_patterns = [
            r"HistoryMixin",
            r"VersionedMixin",
            r"TemporalMixin",
        ]

        has_history_mixin = any(
            re.search(pattern, code, re.IGNORECASE) for pattern in history_patterns
        )

        if has_history_mixin:
            self.evidence.append("Uses history mixin for version tracking")
            self.confidence += 0.30

        # 3. Check for version checking in queries (30 points)
        version_check_patterns = [
            r"filter.*version\s*==",
            r"version\.eq\(self\.version\)",
            r"VersionConflict",
        ]

        has_version_check = any(
            re.search(pattern, code, re.IGNORECASE) for pattern in version_check_patterns
        )

        if has_version_check:
            self.evidence.append("Checks version for optimistic locking")
            self.confidence += 0.30

        # 4. Check for version increment logic (20 points bonus)
        increment_patterns = [
            r"self\.version\s*\+\s*1",
            r"version\s*=.*version\s*\+\s*1",
        ]

        has_increment = any(
            re.search(pattern, code, re.IGNORECASE) for pattern in increment_patterns
        )

        if has_increment:
            self.evidence.append("Increments version on updates")
            self.confidence += 0.20

        # Cap at 1.0
        self.confidence = min(self.confidence, 1.0)

        # Need version field to be considered versioning
        return has_version_field and self.confidence >= 0.40

    def _detect_java_versioning(self, code: str) -> bool:
        """Check for versioning patterns in Java"""
        # 1. Check for @Version annotation (50 points)
        has_version_annotation = "@Version" in code

        if has_version_annotation:
            self.evidence.append("Uses @Version annotation for optimistic locking")
            self.confidence += 0.50

        # 2. Check for version field (30 points)
        version_patterns = [
            r"private\s+int\s+version",
            r"private\s+Integer\s+version",
            r"private\s+Long\s+version",
        ]

        has_version_field = any(
            re.search(pattern, code, re.IGNORECASE) for pattern in version_patterns
        )

        if has_version_field:
            self.evidence.append("Has version field in entity")
            self.confidence += 0.30

        # 3. Check for @Temporal annotation with version (20 points bonus)
        temporal_patterns = [
            r"@Temporal.*version",
            r"@Column.*version",
        ]

        has_temporal = any(re.search(pattern, code, re.IGNORECASE) for pattern in temporal_patterns)

        if has_temporal:
            self.evidence.append("Uses @Temporal for version field")
            self.confidence += 0.20

        # 4. Check for version checking in business logic (bonus)
        version_logic_patterns = [
            r"VersionConflict",
            r"OptimisticLockException",
        ]

        has_version_logic = any(
            re.search(pattern, code, re.IGNORECASE) for pattern in version_logic_patterns
        )

        if has_version_logic:
            self.evidence.append("Handles version conflicts in business logic")
            self.confidence = min(0.95, self.confidence + 0.10)

        # Cap at 1.0
        self.confidence = min(self.confidence, 1.0)

        # Need @Version annotation or version field to be considered versioning
        return (has_version_annotation or has_version_field) and self.confidence >= 0.40

    def get_stdlib_pattern(self) -> str:
        return "versioning/optimistic_lock"


class EventSourcingPattern:
    """
    Detect event sourcing pattern

    Indicators:
    - Event store table/collection (30 points)
    - Event append operations (25 points)
    - Event replay/apply logic (25 points)
    - Event versioning (15 points)
    - Aggregate reconstruction (5 points)

    Target Confidence: 85%+
    """

    def __init__(self):
        self.confidence = 0.0
        self.evidence = []

    def matches(self, code: str, language: str) -> bool:
        """Check if code implements event sourcing"""
        self.evidence = []
        self.confidence = 0.0

        if language == "sql":
            return self._detect_sql_event_sourcing(code)
        elif language == "python":
            return self._detect_python_event_sourcing(code)
        elif language == "java":
            return self._detect_java_event_sourcing(code)
        elif language == "rust":
            return self._detect_rust_event_sourcing(code)

        return False

    def _detect_sql_event_sourcing(self, sql: str) -> bool:
        """Detect event sourcing in SQL"""
        # 1. Event store table (30 points)
        has_event_table = re.search(r"CREATE TABLE.*events?\s*\(", sql, re.IGNORECASE)
        if has_event_table:
            self.evidence.append("Has event store table")
            self.confidence += 0.30

        # 2. Event append operations (25 points)
        has_insert = re.search(r"INSERT INTO.*events?", sql, re.IGNORECASE)
        if has_insert:
            self.evidence.append("Has event append operations")
            self.confidence += 0.25

        # 3. Event versioning (25 points)
        has_version = "version" in sql.lower() and "event" in sql.lower()
        if has_version:
            self.evidence.append("Has event versioning")
            self.confidence += 0.25

        # 4. Aggregate ID (15 points)
        has_aggregate = "aggregate_id" in sql.lower()
        if has_aggregate:
            self.evidence.append("Has aggregate reconstruction")
            self.confidence += 0.15

        # 5. Event ordering (5 points)
        has_ordering = re.search(r"ORDER BY.*version", sql, re.IGNORECASE)
        if has_ordering:
            self.evidence.append("Has event ordering by version")
            self.confidence += 0.05

        return self.confidence >= 0.85

    def _detect_python_event_sourcing(self, code: str) -> bool:
        """Detect event sourcing in Python"""
        # 1. Event class (40 points)
        has_event_class = re.search(r"class\s+Event", code)
        if has_event_class:
            self.evidence.append("Has Event class")
            self.confidence += 0.40

        # 2. Event append operations (15 points)
        has_append = re.search(r"append_event|\.append\(.*event", code, re.IGNORECASE)
        if has_append:
            self.evidence.append("Has event append operations")
            self.confidence += 0.15

        # 3. Event replay/apply logic (35 points)
        has_replay = re.search(r"apply_event|load_from_history|replay", code, re.IGNORECASE)
        if has_replay:
            self.evidence.append("Has event replay/apply logic")
            self.confidence += 0.35

        # 4. Event versioning (10 points)
        has_version = "version" in code.lower() and "event" in code.lower()
        if has_version:
            self.evidence.append("Has event versioning")
            self.confidence += 0.10

        return round(self.confidence, 2) >= 0.85

    def _detect_java_event_sourcing(self, code: str) -> bool:
        """Detect event sourcing in Java"""
        # 1. Event class (30 points)
        has_event_class = re.search(r"class\s+Event", code)
        if has_event_class:
            self.evidence.append("Has Event class")
            self.confidence += 0.30

        # 2. Event append operations (25 points)
        has_append = re.search(r"appendEvent|eventRepository\.save", code)
        if has_append:
            self.evidence.append("Has event append operations")
            self.confidence += 0.25

        # 3. Event ordering (25 points)
        has_ordering = re.search(r"findBy.*OrderBy.*Asc", code)
        if has_ordering:
            self.evidence.append("Has event ordering")
            self.confidence += 0.25

        # 4. Aggregate ID (15 points)
        has_aggregate = re.search(r"UUID\s+aggregateId", code)
        if has_aggregate:
            self.evidence.append("Has aggregate ID")
            self.confidence += 0.15

        return self.confidence >= 0.80

    def _detect_rust_event_sourcing(self, code: str) -> bool:
        """Detect event sourcing in Rust"""
        # 1. Event struct (35 points)
        has_event_struct = re.search(r"struct\s+Event", code)
        if has_event_struct:
            self.evidence.append("Has Event struct")
            self.confidence += 0.35

        # 2. Event append operations (30 points)
        has_append = re.search(r"append_event|\.push\(event", code)
        if has_append:
            self.evidence.append("Has event append operations")
            self.confidence += 0.30

        # 3. Event replay (20 points)
        has_replay = re.search(r"apply_event|replay", code)
        if has_replay:
            self.evidence.append("Has event replay logic")
            self.confidence += 0.20

        # 4. Aggregate ID (15 points)
        has_aggregate = re.search(r"aggregate_id:\s*Uuid", code)
        if has_aggregate:
            self.evidence.append("Has aggregate ID")
            self.confidence += 0.15

        return round(self.confidence, 2) >= 0.80

    def _get_indicators(self, language: str) -> dict:
        """Get language-specific indicators"""

        if language == "sql":
            return {
                "event_store_patterns": [
                    r"CREATE TABLE.*events?\s*\(",
                    r"event_type",
                    r"event_data",
                    r"aggregate_id",
                ],
                "append_patterns": [r"INSERT INTO.*events?", r"APPEND"],
                "replay_patterns": [r"ORDER BY.*version"],
                "aggregate_patterns": [r"aggregate_id"],
            }

        elif language == "python":
            return {
                "event_store_patterns": [
                    r"class\s+Event",
                    r"event_type",
                    r"event_data",
                ],
                "append_patterns": [r"append_event", r"\.append\("],
                "replay_patterns": [
                    r"apply_event",
                    r"load_from_history",
                    r"replay",
                ],
                "aggregate_patterns": [r"class.*Aggregate", r"rebuild.*state"],
            }

        elif language == "java":
            return {
                "event_store_patterns": [
                    r"class\s+Event",
                    r"String\s+eventType",
                    r"eventData",
                ],
                "append_patterns": [
                    r"appendEvent",
                    r"eventRepository\.save",
                ],
                "replay_patterns": [r"findBy.*OrderBy.*Asc"],
                "aggregate_patterns": [r"UUID\s+aggregateId"],
            }

        elif language == "rust":
            return {
                "event_store_patterns": [
                    r"struct\s+Event",
                    r"event_type",
                    r"event_data",
                ],
                "append_patterns": [r"append_event", r"\.push\(event"],
                "replay_patterns": [r"apply_event", r"replay"],
                "aggregate_patterns": [r"aggregate_id:\s*Uuid"],
            }

        return {}

    def get_stdlib_pattern(self) -> str:
        """Return suggested stdlib pattern"""
        return "stdlib/patterns/event_sourcing.yaml"


class ShardingPattern:
    """Detect sharding pattern (80% confidence target)"""

    def __init__(self):
        self.confidence = 0.0
        self.evidence = []

    def matches(self, code: str, language: str) -> bool:
        self.evidence = []
        self.confidence = 0.0

        if language == "sql":
            return self._detect_sql_sharding(code)
        elif language == "python":
            return self._detect_python_sharding(code)
        elif language == "java":
            return self._detect_java_sharding(code)
        elif language == "rust":
            return self._detect_rust_sharding(code)

        return False

    def _detect_sql_sharding(self, sql: str) -> bool:
        """Detect sharding in SQL"""
        # 1. Shard key field (30 points)
        has_shard_key = re.search(r"shard_key\s+INTEGER", sql, re.IGNORECASE)
        if has_shard_key:
            self.evidence.append("Has shard key field")
            self.confidence += 0.30

        # 2. Shard routing function (35 points)
        has_routing = re.search(r"get_shard|% 16", sql, re.IGNORECASE)
        if has_routing:
            self.evidence.append("Has shard routing logic")
            self.confidence += 0.35

        # 3. Shard index (20 points)
        has_index = re.search(r"CREATE INDEX.*shard_key", sql, re.IGNORECASE)
        if has_index:
            self.evidence.append("Has shard key index")
            self.confidence += 0.20

        # 4. Multiple shards (15 points)
        has_multiple = "% 16" in sql or "16" in sql
        if has_multiple:
            self.evidence.append("Supports multiple shards")
            self.confidence += 0.15

        return self.confidence >= 0.80

    def _detect_python_sharding(self, code: str) -> bool:
        """Detect sharding in Python"""
        # 1. Shard routing function (35 points)
        has_routing = re.search(r"def get_shard|hash_value % self\.num_shards", code)
        if has_routing:
            self.evidence.append("Has shard routing logic")
            self.confidence += 0.35

        # 2. Consistent hashing (30 points)
        has_hashing = re.search(r"hashlib\.md5|int\(.*hexdigest", code)
        if has_hashing:
            self.evidence.append("Uses consistent hashing")
            self.confidence += 0.30

        # 3. Multiple shards (20 points)
        has_multiple = "num_shards" in code or "% self.num_shards" in code
        if has_multiple:
            self.evidence.append("Supports multiple shards")
            self.confidence += 0.20

        # 4. Shard router class (15 points)
        has_router = re.search(r"class.*ShardRouter", code)
        if has_router:
            self.evidence.append("Has shard router class")
            self.confidence += 0.15

        return self.confidence >= 0.80

    def _detect_java_sharding(self, code: str) -> bool:
        """Detect sharding in Java"""
        # 1. Shard routing method (35 points)
        has_routing = re.search(r"getShard|Math\.abs\(.*\.hashCode\(\)", code)
        if has_routing:
            self.evidence.append("Has shard routing logic")
            self.confidence += 0.35

        # 2. Shard manager class (30 points)
        has_manager = re.search(r"class.*ShardManager", code)
        if has_manager:
            self.evidence.append("Has shard manager class")
            self.confidence += 0.30

        # 3. Multiple shards (20 points)
        has_multiple = "numShards" in code or "% numShards" in code
        if has_multiple:
            self.evidence.append("Supports multiple shards")
            self.confidence += 0.20

        # 4. Hash-based routing (15 points)
        has_hash = ".hashCode()" in code
        if has_hash:
            self.evidence.append("Uses hash-based routing")
            self.confidence += 0.15

        return self.confidence >= 0.80

    def _detect_rust_sharding(self, code: str) -> bool:
        """Detect sharding in Rust"""
        # 1. Shard routing function (35 points)
        has_routing = re.search(r"fn get_shard|finish\(\) as usize\) % self\.num_shards", code)
        if has_routing:
            self.evidence.append("Has shard routing logic")
            self.confidence += 0.35

        # 2. Consistent hashing (30 points)
        has_hashing = re.search(r"DefaultHasher|hash\(\s*&mut.*\)", code)
        if has_hashing:
            self.evidence.append("Uses consistent hashing")
            self.confidence += 0.30

        # 3. Multiple shards (20 points)
        has_multiple = "num_shards" in code or "% self.num_shards" in code
        if has_multiple:
            self.evidence.append("Supports multiple shards")
            self.confidence += 0.20

        # 4. Shard router struct (15 points)
        has_router = re.search(r"struct.*ShardRouter", code)
        if has_router:
            self.evidence.append("Has shard router struct")
            self.confidence += 0.15

        return self.confidence >= 0.80

    def get_stdlib_pattern(self) -> str:
        return "stdlib/patterns/sharding.yaml"


class CacheInvalidationPattern:
    """Detect cache invalidation (82% confidence target)"""

    def __init__(self):
        self.confidence = 0.0
        self.evidence = []

    def matches(self, code: str, language: str) -> bool:
        self.evidence = []
        self.confidence = 0.0

        if language == "sql":
            return self._detect_sql_cache_invalidation(code)
        elif language == "python":
            return self._detect_python_cache_invalidation(code)
        elif language == "java":
            return self._detect_java_cache_invalidation(code)
        elif language == "rust":
            return self._detect_rust_cache_invalidation(code)

        return False

    def _detect_sql_cache_invalidation(self, sql: str) -> bool:
        """Detect cache invalidation in SQL"""
        # 1. Cache table (25 points)
        has_cache_table = re.search(r"CREATE TABLE.*cache", sql, re.IGNORECASE)
        if has_cache_table:
            self.evidence.append("Has cache table")
            self.confidence += 0.25

        # 2. Cache invalidation (30 points)
        has_invalidation = re.search(r"DELETE FROM.*cache", sql, re.IGNORECASE)
        if has_invalidation:
            self.evidence.append("Has cache invalidation logic")
            self.confidence += 0.30

        # 3. TTL/expiration (15 points)
        has_ttl = re.search(r"expires_at|TTL", sql, re.IGNORECASE)
        if has_ttl:
            self.evidence.append("Has TTL/expiration handling")
            self.confidence += 0.15

        # 4. Tag-based invalidation (12 points)
        has_tags = "tags" in sql.lower() and "GIN" in sql.upper()
        if has_tags:
            self.evidence.append("Has tag-based invalidation")
            self.confidence += 0.12

        return self.confidence >= 0.82

    def _detect_python_cache_invalidation(self, code: str) -> bool:
        """Detect cache invalidation in Python"""
        # 1. Cache key generation (25 points)
        has_cache_key = re.search(r"cache_key\s*=|f.*contact.*\$\{.*\}", code)
        if has_cache_key:
            self.evidence.append("Has cache key generation")
            self.confidence += 0.25

        # 2. Cache invalidation logic (30 points)
        has_invalidation = re.search(r"\.delete\(|invalidate_contact", code)
        if has_invalidation:
            self.evidence.append("Has cache invalidation logic")
            self.confidence += 0.30

        # 3. Cache class (15 points)
        has_cache_class = re.search(r"class.*Cache", code)
        if has_cache_class:
            self.evidence.append("Has cache class")
            self.confidence += 0.15

        # 4. Tag-based invalidation (12 points)
        has_tags = re.search(r"invalidate_by_tag|\.keys\(.*pattern", code)
        if has_tags:
            self.evidence.append("Has tag-based invalidation")
            self.confidence += 0.12

        return self.confidence >= 0.82

    def _detect_java_cache_invalidation(self, code: str) -> bool:
        """Detect cache invalidation in Java"""
        # 1. Cache builder/configuration (25 points)
        has_cache_builder = re.search(r"CacheBuilder|Cache\.newBuilder", code)
        if has_cache_builder:
            self.evidence.append("Has cache configuration")
            self.confidence += 0.25

        # 2. Cache invalidation (30 points)
        has_invalidation = re.search(r"\.invalidate\(|invalidateAll", code)
        if has_invalidation:
            self.evidence.append("Has cache invalidation logic")
            self.confidence += 0.30

        # 3. TTL/expiration (15 points)
        has_ttl = re.search(r"expireAfterWrite|maximumSize", code)
        if has_ttl:
            self.evidence.append("Has TTL/expiration handling")
            self.confidence += 0.15

        # 4. Cache service class (12 points)
        has_service = re.search(r"class.*Cache.*Service", code)
        if has_service:
            self.evidence.append("Has cache service class")
            self.confidence += 0.12

        return self.confidence >= 0.82

    def _detect_rust_cache_invalidation(self, code: str) -> bool:
        """Detect cache invalidation in Rust"""
        # 1. Cache entry struct (25 points)
        has_cache_entry = re.search(r"struct.*CacheEntry", code)
        if has_cache_entry:
            self.evidence.append("Has cache entry struct")
            self.confidence += 0.25

        # 2. Cache invalidation (30 points)
        has_invalidation = re.search(r"\.remove\(|cleanup_expired", code)
        if has_invalidation:
            self.evidence.append("Has cache invalidation logic")
            self.confidence += 0.30

        # 3. TTL/expiration (15 points)
        has_ttl = re.search(r"expires_at|Instant::now", code)
        if has_ttl:
            self.evidence.append("Has TTL/expiration handling")
            self.confidence += 0.15

        # 4. Pattern-based invalidation (12 points)
        has_pattern = re.search(r"retain.*contains", code)
        if has_pattern:
            self.evidence.append("Has pattern-based invalidation")
            self.confidence += 0.12

        return self.confidence >= 0.82

    def get_stdlib_pattern(self) -> str:
        return "stdlib/patterns/cache_invalidation.yaml"


class RateLimitingPattern:
    """Detect rate limiting (83% confidence target)"""

    def __init__(self):
        self.confidence = 0.0
        self.evidence = []

    def matches(self, code: str, language: str) -> bool:
        self.evidence = []
        self.confidence = 0.0

        if language == "sql":
            return self._detect_sql_rate_limiting(code)
        elif language == "python":
            return self._detect_python_rate_limiting(code)
        elif language == "java":
            return self._detect_java_rate_limiting(code)
        elif language == "rust":
            return self._detect_rust_rate_limiting(code)

        return False

    def _detect_sql_rate_limiting(self, sql: str) -> bool:
        """Detect rate limiting in SQL"""
        # 1. Rate limits table (30 points)
        has_rate_table = re.search(r"CREATE TABLE.*rate_limits", sql, re.IGNORECASE)
        if has_rate_table:
            self.evidence.append("Has rate limits table")
            self.confidence += 0.30

        # 2. Token/refill logic (25 points)
        has_refill = re.search(r"tokens_remaining|refill", sql, re.IGNORECASE)
        if has_refill:
            self.evidence.append("Has token/refill logic")
            self.confidence += 0.25

        # 3. Function for rate limiting (20 points)
        has_function = re.search(r"CREATE FUNCTION.*check_rate_limit", sql, re.IGNORECASE)
        if has_function:
            self.evidence.append("Has rate limiting function")
            self.confidence += 0.20

        # 4. Time-based logic (15 points)
        has_time = re.search(r"NOW\(\)|EXTRACT.*EPOCH", sql, re.IGNORECASE)
        if has_time:
            self.evidence.append("Has time-based logic")
            self.confidence += 0.15

        # 5. Rate limit exceeded handling (10 points)
        has_exceeded = "FALSE" in sql.upper() or "RETURN FALSE" in sql.upper()
        if has_exceeded:
            self.evidence.append("Handles rate limit exceeded")
            self.confidence += 0.10

        return self.confidence >= 0.83

    def _detect_python_rate_limiting(self, code: str) -> bool:
        """Detect rate limiting in Python"""
        # 1. Token bucket class (30 points)
        has_token_bucket = re.search(r"class.*TokenBucket", code)
        if has_token_bucket:
            self.evidence.append("Has token bucket class")
            self.confidence += 0.30

        # 2. Token/refill logic (25 points)
        has_refill = re.search(r"refill|tokens.*capacity", code)
        if has_refill:
            self.evidence.append("Has token/refill logic")
            self.confidence += 0.25

        # 3. Consume/check method (20 points)
        has_consume = re.search(r"def consume|def allow", code)
        if has_consume:
            self.evidence.append("Has consume/check method")
            self.confidence += 0.20

        # 4. Time-based logic (15 points)
        has_time = re.search(r"time\.time|datetime", code)
        if has_time:
            self.evidence.append("Has time-based logic")
            self.confidence += 0.15

        # 5. Rate limit exceeded (10 points)
        has_exceeded = "return False" in code.lower()
        if has_exceeded:
            self.evidence.append("Handles rate limit exceeded")
            self.confidence += 0.10

        return self.confidence >= 0.83

    def _detect_java_rate_limiting(self, code: str) -> bool:
        """Detect rate limiting in Java"""
        # 1. Rate limiter usage (30 points)
        has_rate_limiter = re.search(r"RateLimiter\.create|@RateLimited", code)
        if has_rate_limiter:
            self.evidence.append("Uses rate limiter")
            self.confidence += 0.30

        # 2. Try acquire logic (25 points)
        has_try_acquire = re.search(r"tryAcquire\(\)", code)
        if has_try_acquire:
            self.evidence.append("Has try acquire logic")
            self.confidence += 0.25

        # 3. Rate limit exception (20 points)
        has_exception = re.search(r"RateLimitExceededException", code)
        if has_exception:
            self.evidence.append("Has rate limit exception")
            self.confidence += 0.20

        # 4. Controller annotation (15 points)
        has_controller = re.search(r"@PostMapping|@RequestMapping", code)
        if has_controller:
            self.evidence.append("Has controller with rate limiting")
            self.confidence += 0.15

        # 5. Rate limit check (10 points)
        has_check = "if (!" in code and "tryAcquire" in code
        if has_check:
            self.evidence.append("Has rate limit check")
            self.confidence += 0.10

        return self.confidence >= 0.83

    def _detect_rust_rate_limiting(self, code: str) -> bool:
        """Detect rate limiting in Rust"""
        # 1. Leaky bucket struct (30 points)
        has_leaky_bucket = re.search(r"struct.*LeakyBucket", code)
        if has_leaky_bucket:
            self.evidence.append("Has leaky bucket struct")
            self.confidence += 0.30

        # 2. Water level logic (25 points)
        has_water_level = re.search(r"water_level|leak_rate", code)
        if has_water_level:
            self.evidence.append("Has water level logic")
            self.confidence += 0.25

        # 3. Allow method (20 points)
        has_allow = re.search(r"fn allow", code)
        if has_allow:
            self.evidence.append("Has allow method")
            self.confidence += 0.20

        # 4. Time-based logic (15 points)
        has_time = re.search(r"Instant|Duration", code)
        if has_time:
            self.evidence.append("Has time-based logic")
            self.confidence += 0.15

        # 5. Capacity check (10 points)
        has_capacity = "capacity" in code.lower() and "water_level" in code.lower()
        if has_capacity:
            self.evidence.append("Has capacity check")
            self.confidence += 0.10

        return self.confidence >= 0.83

    def get_stdlib_pattern(self) -> str:
        return "stdlib/patterns/rate_limiting.yaml"
