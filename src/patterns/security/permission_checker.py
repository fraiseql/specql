"""Security utilities for permission validation and RLS generation."""

from dataclasses import dataclass
from typing import Any


@dataclass
class ValidationResult:
    """Result of permission validation."""

    errors: list[str]
    warnings: list[str] | None = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class PermissionChecker:
    """Validate permission configurations and generate security policies."""

    def __init__(self):
        self.dangerous_patterns = [
            "OR 1=1",
            "OR '1'='1'",
            "OR TRUE",
            "DROP",
            "DELETE",
            "UPDATE",
            "INSERT",
            "--",
            "/*",
            "*/",
        ]

    def validate_permission_checks(self, checks: list[dict[str, Any]]) -> ValidationResult:
        """Ensure permission checks are secure and well-formed."""
        errors = []
        warnings = []

        if not checks:
            errors.append("At least one permission check required")
            return ValidationResult(errors=errors, warnings=warnings)

        for i, check in enumerate(checks):
            check_type = check.get("type")

            if not check_type:
                errors.append(f"Check {i}: Missing 'type' field")
                continue

            if check_type not in ["ownership", "organizational_hierarchy", "role_based", "custom"]:
                errors.append(f"Check {i}: Invalid check type '{check_type}'")
                continue

            # Validate required fields for each type
            if check_type == "ownership":
                if not check.get("field"):
                    errors.append(f"Check {i}: 'field' required for ownership check")

            elif check_type == "organizational_hierarchy":
                if not check.get("field"):
                    errors.append(f"Check {i}: 'field' required for organizational_hierarchy check")

            elif check_type == "role_based":
                if not check.get("allowed_roles") or not isinstance(check["allowed_roles"], list):
                    errors.append(f"Check {i}: 'allowed_roles' array required for role_based check")
                elif not check["allowed_roles"]:
                    warnings.append(f"Check {i}: Empty allowed_roles list")

            elif check_type == "custom":
                custom_condition = check.get("custom_condition", "")
                if not custom_condition:
                    errors.append(f"Check {i}: 'custom_condition' required for custom check")
                else:
                    # Check for dangerous patterns
                    for pattern in self.dangerous_patterns:
                        if pattern.upper() in custom_condition.upper():
                            errors.append(
                                f"Check {i}: Dangerous pattern '{pattern}' detected in custom condition"
                            )

        return ValidationResult(errors=errors, warnings=warnings)

    def generate_rls_policy(
        self,
        entity: dict[str, Any],
        checks: list[dict[str, Any]],
        user_context_source: str = "CURRENT_SETTING('app.current_user_id')",
    ) -> str:
        """Generate PostgreSQL RLS policy SQL."""
        policy_conditions = []

        for check in checks:
            check_type = check["type"]

            if check_type == "ownership":
                condition = f"{entity['table']}.{check['field']} = {user_context_source}::uuid"
                policy_conditions.append(condition)

            elif check_type == "organizational_hierarchy":
                condition = f"""
                {entity["table"]}.{check["field"]} IN (
                    SELECT ou.pk_organizational_unit
                    FROM tenant.tb_organizational_unit ou
                    INNER JOIN tenant.tb_user u ON u.organizational_unit_path <@ ou.path
                    WHERE u.id = {user_context_source}::uuid
                      AND ou.deleted_at IS NULL
                      AND u.deleted_at IS NULL
                )"""
                policy_conditions.append(condition.strip())

            elif check_type == "role_based":
                roles_list = ", ".join(f"'{role}'" for role in check["allowed_roles"])
                condition = f"""
                EXISTS (
                    SELECT 1
                    FROM app.tb_user_role ur
                    WHERE ur.user_id = {user_context_source}::uuid
                      AND ur.role IN ({roles_list})
                      AND ur.deleted_at IS NULL
                )"""
                policy_conditions.append(condition.strip())

            elif check_type == "custom":
                policy_conditions.append(f"({check['custom_condition']})")

        # Combine conditions with OR
        combined_condition = " OR ".join(policy_conditions)

        policy_sql = f"""
        -- Enable RLS on the table
        ALTER TABLE {entity["schema"]}.{entity["table"]} ENABLE ROW LEVEL SECURITY;

        -- Create RLS policy
        CREATE POLICY rls_{entity["table"]}_access
        ON {entity["schema"]}.{entity["table"]}
        FOR SELECT
        USING ({combined_condition});
        """

        return policy_sql.strip()

    def analyze_permission_coverage(
        self, entity: dict[str, Any], checks: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyze how well the permission checks cover different access scenarios."""
        coverage = {
            "ownership": False,
            "organizational": False,
            "role_based": False,
            "custom": False,
            "total_checks": len(checks),
            "recommendations": [],
        }

        for check in checks:
            check_type = check["type"]
            if check_type in coverage:
                coverage[check_type] = True

        # Generate recommendations
        if not coverage["ownership"] and not coverage["organizational"]:
            coverage["recommendations"].append(
                "Consider adding ownership or organizational checks to ensure users can access their own data"
            )

        if not coverage["role_based"]:
            coverage["recommendations"].append(
                "Consider adding role-based checks for admin/superuser access"
            )

        if coverage["custom"] and not (coverage["ownership"] or coverage["organizational"]):
            coverage["recommendations"].append(
                "Custom conditions should be combined with ownership checks for security"
            )

        return coverage

    def generate_permission_test_cases(
        self, entity: dict[str, Any], checks: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Generate test cases for permission validation."""
        test_cases = []

        # Test case for no access (should return empty)
        test_cases.append(
            {
                "name": "no_permissions",
                "user_context": None,
                "expected_count": 0,
                "description": "User with no permissions should see no records",
            }
        )

        # Test ownership if present
        ownership_checks = [c for c in checks if c["type"] == "ownership"]
        if ownership_checks:
            test_cases.append(
                {
                    "name": "ownership_access",
                    "user_context": "user123",
                    "expected_condition": f"{ownership_checks[0]['field']} = 'user123'::uuid",
                    "description": "User should see records they own",
                }
            )

        # Test role-based if present
        role_checks = [c for c in checks if c["type"] == "role_based"]
        if role_checks:
            test_cases.append(
                {
                    "name": "role_based_access",
                    "user_context": "admin_user",
                    "user_roles": role_checks[0]["allowed_roles"],
                    "expected_count": "all_matching_role",
                    "description": f"User with roles {role_checks[0]['allowed_roles']} should see appropriate records",
                }
            )

        return test_cases
