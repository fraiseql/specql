"""KPI Builder Utilities for Metric Calculations"""

from typing import Dict, Any, List
import re


class KPIBuilder:
    """Build KPI calculation views with formula parsing and validation"""

    def __init__(self):
        self.formula_parser = FormulaParser()
        self.join_detector = JoinDetector()

    def parse_formula(self, formula: str) -> Dict[str, Any]:
        """Parse SQL formula into AST for analysis"""
        return self.formula_parser.parse(formula)

    def detect_required_joins(self, formula: str, base_entity: str) -> List[Dict[str, Any]]:
        """Detect which tables need to be joined based on formula"""
        return self.join_detector.detect_joins(formula, base_entity)

    def generate_threshold_checks(self, metric: Dict[str, Any]) -> str:
        """Generate CASE statement for threshold status"""
        thresholds = metric.get("thresholds", {})
        if not thresholds:
            return ""

        critical = thresholds.get("critical")
        warning = thresholds.get("warning")

        if critical is None and warning is None:
            return ""

        conditions = []
        if critical is not None:
            conditions.append(f"WHEN {metric['name']} >= {critical} THEN 'CRITICAL'")
        if warning is not None:
            conditions.append(f"WHEN {metric['name']} >= {warning} THEN 'WARNING'")

        conditions.append("ELSE 'OK'")

        return f"""
        CASE
            {"\n            ".join(conditions)}
        END AS {metric["name"]}_status
        """

    def generate_formatter(self, metric: Dict[str, Any]) -> str:
        """Generate formatting expression"""
        format_type = metric.get("format", "decimal")
        name = metric["name"]

        formats = {
            "percentage": f"ROUND(({name} * 100)::numeric, 2)",
            "currency": f"TO_CHAR({name}, 'FM$999,999,999.00')",
            "integer": f"ROUND({name})::integer",
            "decimal": f"ROUND({name}::numeric, 2)",
        }

        formatted = formats.get(format_type, f"ROUND({name}::numeric, 2)")
        return f"{formatted} AS {name}_formatted" if format_type != "decimal" else ""

    def validate_metric_config(self, metric: Dict[str, Any]) -> List[str]:
        """Validate metric configuration"""
        errors = []

        if "name" not in metric:
            errors.append("Metric must have a 'name' field")

        if "formula" not in metric:
            errors.append("Metric must have a 'formula' field")

        formula = metric.get("formula", "")
        if not self._is_valid_sql_formula(formula):
            errors.append(f"Invalid SQL formula: {formula}")

        thresholds = metric.get("thresholds", {})
        if thresholds:
            if "critical" in thresholds and "warning" in thresholds:
                if thresholds["critical"] <= thresholds["warning"]:
                    errors.append("Critical threshold must be greater than warning threshold")

        return errors

    def _is_valid_sql_formula(self, formula: str) -> bool:
        """Basic validation for SQL formula"""
        # This is a simplified check - in practice would use proper SQL parsing
        if not formula or not isinstance(formula, str):
            return False

        # Check for basic SQL injection patterns (very basic)
        dangerous_patterns = [
            r";\s*drop\s+table",
            r";\s*delete\s+from",
            r"union\s+select.*--",
            r"/\*.*\*/",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, formula, re.IGNORECASE):
                return False

        return True


class FormulaParser:
    """Parse SQL formulas for analysis"""

    def parse(self, formula: str) -> Dict[str, Any]:
        """Parse formula into components"""
        # Simplified parser - in practice would use sqlparse or similar
        return {
            "original": formula,
            "functions": self._extract_functions(formula),
            "tables": self._extract_table_references(formula),
            "columns": self._extract_column_references(formula),
        }

    def _extract_functions(self, formula: str) -> List[str]:
        """Extract function calls from formula"""
        # Simple regex for function detection
        func_pattern = r"\b(\w+)\s*\("
        return re.findall(func_pattern, formula)

    def _extract_table_references(self, formula: str) -> List[str]:
        """Extract table references (alias.table format)"""
        # Look for alias.table patterns
        table_pattern = r"\b(\w+)\.(\w+)\b"
        matches = re.findall(table_pattern, formula)
        return [f"{alias}.{column}" for alias, column in matches]

    def _extract_column_references(self, formula: str) -> List[str]:
        """Extract column references"""
        # Simple extraction - could be improved
        return re.findall(r"\b\w+\.\w+\b", formula)


class JoinDetector:
    """Detect required joins from formulas"""

    def __init__(self):
        self.known_joins = {
            "a.allocation_date": {
                "table": "tenant.tb_allocation",
                "alias": "a",
                "condition": "a.fk_machine = m.pk_machine",
                "date_field": "allocation_date",
            },
            "mc.cost": {
                "table": "tenant.tb_maintenance_cost",
                "alias": "mc",
                "condition": "mc.fk_machine = m.pk_machine",
                "date_field": "date",
            },
            "r.page_count": {
                "table": "tenant.tb_reading",
                "alias": "r",
                "condition": "r.fk_machine = m.pk_machine",
                "date_field": "reading_date",
            },
        }

    def detect_joins(self, formula: str, base_entity: str) -> List[Dict[str, Any]]:
        """Detect joins needed for formula"""
        joins = []
        entity_alias = base_entity[0].lower()  # First letter as alias

        for indicator, join_info in self.known_joins.items():
            if indicator in formula:
                # Adapt join condition for the actual base entity
                adapted_join = dict(join_info)
                adapted_join["condition"] = join_info["condition"].replace(
                    "m.pk_machine", f"{entity_alias}.pk_{base_entity.lower()}"
                )
                joins.append(adapted_join)

        # Remove duplicates
        seen = set()
        unique_joins = []
        for join in joins:
            key = (join["alias"], join["condition"])
            if key not in seen:
                seen.add(key)
                unique_joins.append(join)

        return unique_joins
