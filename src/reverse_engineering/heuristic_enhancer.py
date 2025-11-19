"""
Heuristic Enhancer: Improve SQL → SpecQL conversion with pattern detection and heuristics

Improves confidence from 85% → 90% through:
- Variable purpose inference (total/count/flag/temp)
- Pattern detection (state machines, audit trails, etc.)
- Control flow simplification
- Variable naming improvements
"""

from dataclasses import dataclass

from src.reverse_engineering.ast_to_specql_mapper import ConversionResult
from src.reverse_engineering.cte_parser import CTEParser
from src.reverse_engineering.universal_pattern_detector import (
    DetectedPattern as UniversalDetectedPattern,
)
from src.reverse_engineering.universal_pattern_detector import (
    UniversalPatternDetector,
)


@dataclass
class VariablePurpose:
    """Inferred purpose of a variable"""

    name: str
    purpose: str  # 'total', 'count', 'flag', 'temp', 'accumulator', 'result', 'unknown'
    confidence: float
    evidence: list[str]


@dataclass
class DetectedPattern:
    """Detected domain pattern"""

    name: str
    confidence: float
    description: str
    evidence: list[str]


class HeuristicEnhancer:
    """
    Enhance conversion results with heuristics

    Improves algorithmic conversion through pattern detection and inference
    Integrates with UniversalPatternDetector for cross-language pattern detection
    """

    def __init__(self):
        self.variable_purposes = {}
        self.detected_patterns = []
        self.cte_parser = CTEParser()
        self.universal_pattern_detector = UniversalPatternDetector()

    def enhance(
        self,
        result: ConversionResult,
        source_code: str | None = None,
        language: str = "sql",
    ) -> ConversionResult:
        """
        Enhance conversion result with heuristics

        Args:
            result: ConversionResult from algorithmic parser
            source_code: Optional raw source code for universal pattern detection
            language: Programming language ('sql', 'python', 'java', 'rust')

        Returns:
            Enhanced ConversionResult with improved confidence
        """
        # Reset state
        self.variable_purposes = {}
        self.detected_patterns = []

        # Apply universal pattern detection if source code is provided
        universal_patterns = []
        if source_code:
            universal_patterns = self.universal_pattern_detector.detect(source_code, language)

        # Apply SQL-specific enhancements (if SQL)
        if language == "sql":
            result = self._infer_variable_purposes(result)
            result = self._detect_patterns(result)
            result = self._simplify_control_flow(result)
            result = self._improve_naming(result)

        # Merge universal patterns with SQL-specific patterns
        if universal_patterns:
            result = self._merge_universal_patterns(result, universal_patterns)

        # Update confidence based on enhancements
        initial_confidence = result.confidence
        confidence_boost = self._calculate_confidence_boost(result, universal_patterns)
        result.confidence = min(initial_confidence + confidence_boost, 0.90)
        # Don't decrease confidence below initial value
        result.confidence = max(result.confidence, initial_confidence)

        # Add metadata
        if not hasattr(result, "metadata"):
            result.metadata = {}
        result.metadata["detected_patterns"] = [p.name for p in self.detected_patterns]
        result.metadata["variable_purposes"] = {
            name: purpose.purpose for name, purpose in self.variable_purposes.items()
        }
        if universal_patterns:
            result.metadata["universal_patterns"] = [
                {"name": p.name, "confidence": p.confidence, "evidence": p.evidence}
                for p in universal_patterns
            ]

        return result

    def _infer_variable_purposes(self, result: ConversionResult) -> ConversionResult:
        """Infer the purpose of variables based on usage patterns"""
        variables = self._extract_variables(result)

        for var_name in variables:
            purpose = self._infer_variable_purpose(var_name, result)
            if purpose:
                self.variable_purposes[var_name] = purpose

        return result

    def _extract_variables(self, result: ConversionResult) -> set[str]:
        """Extract all variable names from the conversion result"""
        variables = set()

        for step in result.steps:
            if step.type == "declare" and hasattr(step, "variable_name"):
                variables.add(step.variable_name)

            # Check for variable usage in expressions
            if hasattr(step, "expression") and step.expression:
                variables.update(self._extract_vars_from_expression(step.expression))

            if hasattr(step, "condition") and step.condition:
                variables.update(self._extract_vars_from_expression(step.condition))

        return variables

    def _extract_vars_from_expression(self, expression: str) -> set[str]:
        """Extract variable names from SQL expression"""
        variables = set()

        # Simple heuristic: look for v_ prefixed variables
        import re

        var_matches = re.findall(r"\bv_\w+", expression)
        variables.update(var_matches)

        # Also look for parameter references
        param_matches = re.findall(r"\bp_\w+", expression)
        variables.update(param_matches)

        return variables

    def _infer_variable_purpose(
        self, var_name: str, result: ConversionResult
    ) -> VariablePurpose | None:
        """
        Infer the purpose of a variable based on naming and usage patterns

        Args:
            var_name: Variable name to analyze
            result: Full conversion result for context

        Returns:
            VariablePurpose if inference successful, None otherwise
        """
        evidence = []
        confidence = 0.0
        purpose = "unknown"

        # Analyze variable name patterns
        name_lower = var_name.lower()

        # Total/accumulator patterns
        if any(keyword in name_lower for keyword in ["total", "sum", "amount", "balance"]):
            purpose = "total"
            confidence = 0.8
            evidence.append(
                f"Name contains '{[k for k in ['total', 'sum', 'amount', 'balance'] if k in name_lower][0]}'"
            )

        # Count patterns
        elif any(keyword in name_lower for keyword in ["count", "cnt", "num", "qty", "quantity"]):
            purpose = "count"
            confidence = 0.8
            evidence.append(
                f"Name contains '{[k for k in ['count', 'cnt', 'num', 'qty', 'quantity'] if k in name_lower][0]}'"
            )

        # Flag/boolean patterns
        elif any(
            keyword in name_lower for keyword in ["flag", "is_", "has_", "can_", "should_", "valid"]
        ):
            purpose = "flag"
            confidence = 0.7
            evidence.append(f"Name suggests boolean flag: '{var_name}'")

        # Result patterns
        elif any(keyword in name_lower for keyword in ["result", "output", "ret"]):
            purpose = "result"
            confidence = 0.6
            evidence.append(f"Name suggests result/output: '{var_name}'")

        # Analyze usage patterns
        usage_evidence = self._analyze_variable_usage(var_name, result)
        evidence.extend(usage_evidence)

        # Boost confidence based on usage evidence
        if "initialized to 0" in usage_evidence:
            if purpose in ["total", "count"]:
                confidence += 0.1
            elif purpose == "unknown":
                purpose = "accumulator"
                confidence = 0.6

        if "used in SUM()" in usage_evidence and purpose == "unknown":
            purpose = "total"
            confidence = 0.7

        if "used in COUNT()" in usage_evidence and purpose == "unknown":
            purpose = "count"
            confidence = 0.7

        # Only return if we have reasonable confidence
        if confidence >= 0.5:
            return VariablePurpose(
                name=var_name, purpose=purpose, confidence=min(confidence, 1.0), evidence=evidence
            )

        return None

    def _analyze_variable_usage(self, var_name: str, result: ConversionResult) -> list[str]:
        """Analyze how a variable is used throughout the function"""
        evidence = []

        for step in result.steps:
            if step.type == "declare" and getattr(step, "variable_name", None) == var_name:
                # Check initialization
                if hasattr(step, "default_value"):
                    if step.default_value == "0":
                        evidence.append("initialized to 0")
                    elif str(step.default_value).upper() in ["TRUE", "FALSE"]:
                        evidence.append("initialized to boolean")

            elif (
                step.type == "assign"
                and hasattr(step, "variable_name")
                and step.variable_name == var_name
            ):
                # Check assignment expressions
                expr = getattr(step, "expression", "").upper()
                if "SUM(" in expr:
                    evidence.append("used in SUM()")
                if "COUNT(" in expr:
                    evidence.append("used in COUNT()")
                if "AVG(" in expr:
                    evidence.append("used in AVG()")

            elif (
                step.type == "query"
                and hasattr(step, "into_variable")
                and step.into_variable == var_name
            ):
                # Check SELECT INTO
                query = getattr(step, "expression", "").upper()
                if "SUM(" in query:
                    evidence.append("assigned from SUM() query")
                if "COUNT(" in query:
                    evidence.append("assigned from COUNT() query")

        return evidence

    def _detect_patterns(self, result: ConversionResult) -> ConversionResult:
        """Detect common domain patterns in the function"""
        patterns = []

        # State machine pattern
        state_pattern = self._detect_state_machine_pattern(result)
        if state_pattern:
            patterns.append(state_pattern)

        # Audit trail pattern
        audit_pattern = self._detect_audit_trail_pattern(result)
        if audit_pattern:
            patterns.append(audit_pattern)

        # Soft delete pattern
        soft_delete_pattern = self._detect_soft_delete_pattern(result)
        if soft_delete_pattern:
            patterns.append(soft_delete_pattern)

        # Validation chain pattern
        validation_pattern = self._detect_validation_chain_pattern(result)
        if validation_pattern:
            patterns.append(validation_pattern)

        # Recursive pattern
        recursive_pattern = self._detect_recursive_pattern(result)
        if recursive_pattern:
            patterns.append(recursive_pattern)

        # Window function pattern
        window_pattern = self._detect_window_function_pattern(result)
        if window_pattern:
            patterns.append(window_pattern)

        # Aggregate pattern
        aggregate_pattern = self._detect_aggregate_pattern(result)
        if aggregate_pattern:
            patterns.append(aggregate_pattern)

        # Exception handler pattern
        exception_pattern = self._detect_exception_handler_pattern(result)
        if exception_pattern:
            patterns.append(exception_pattern)

        # Dynamic SQL pattern
        dynamic_sql_pattern = self._detect_dynamic_sql_pattern(result)
        if dynamic_sql_pattern:
            patterns.append(dynamic_sql_pattern)

        # Cursor operations pattern
        cursor_pattern = self._detect_cursor_operations_pattern(result)
        if cursor_pattern:
            patterns.append(cursor_pattern)

        # Control flow pattern
        control_flow_pattern = self._detect_control_flow_pattern(result)
        if control_flow_pattern:
            patterns.append(control_flow_pattern)

        # Window function pattern
        window_function_pattern = self._detect_window_function_pattern(result)
        if window_function_pattern:
            patterns.append(window_function_pattern)

        # Aggregate filter pattern
        aggregate_filter_pattern = self._detect_aggregate_filter_pattern(result)
        if aggregate_filter_pattern:
            patterns.append(aggregate_filter_pattern)

        self.detected_patterns = patterns
        return result

    def _detect_state_machine_pattern(self, result: ConversionResult) -> DetectedPattern | None:
        """Detect state machine pattern (status transitions)"""
        evidence = []

        # Look for status/state variables
        status_vars = []
        for var_name in self.variable_purposes:
            if self.variable_purposes[var_name].purpose == "flag":
                var_lower = var_name.lower()
                if any(state in var_lower for state in ["status", "state", "phase", "stage"]):
                    status_vars.append(var_name)
                    evidence.append(f"Found status variable: {var_name}")

        # Look for status transitions in queries
        status_transitions = 0
        for step in result.steps:
            if step.type == "query":
                # Check both expression and sql attributes
                query_text = getattr(step, "expression", "") or getattr(step, "sql", "") or ""
                if query_text and isinstance(query_text, str):
                    query_upper = query_text.upper()
                    if "UPDATE" in query_upper and "STATUS" in query_upper:
                        status_transitions += 1
                        evidence.append("Found status update query")

        if len(status_vars) >= 1 and status_transitions >= 1:
            confidence = min(0.8 + (len(status_vars) * 0.1) + (status_transitions * 0.1), 0.95)
            return DetectedPattern(
                name="state_machine",
                confidence=confidence,
                description="Function implements state/status transitions",
                evidence=evidence,
            )

        return None

    def _detect_audit_trail_pattern(self, result: ConversionResult) -> DetectedPattern | None:
        """Detect audit trail pattern (logging changes)"""
        evidence = []

        # Look for audit-related operations
        audit_operations = 0
        for step in result.steps:
            if step.type == "query":
                query_text = getattr(step, "expression", "") or getattr(step, "sql", "") or ""
                if query_text and isinstance(query_text, str):
                    query_upper = query_text.upper()
                    audit_keywords = ["INSERT INTO", "AUDIT", "LOG", "HISTORY", "TRAIL"]
                    if any(keyword in query_upper for keyword in audit_keywords):
                        audit_operations += 1
                        evidence.append(f"Found audit operation: {query_text[:50]}...")

        # Look for timestamp/user tracking
        timestamp_vars = [
            v
            for v in self.variable_purposes
            if "time" in self.variable_purposes[v].purpose or "user" in v.lower()
        ]
        if timestamp_vars:
            evidence.append(f"Found timestamp/user variables: {timestamp_vars}")

        if audit_operations >= 1:
            confidence = min(0.7 + (audit_operations * 0.1), 0.9)
            return DetectedPattern(
                name="audit_trail",
                confidence=confidence,
                description="Function implements audit trail logging",
                evidence=evidence,
            )

        return None

    def _detect_soft_delete_pattern(self, result: ConversionResult) -> DetectedPattern | None:
        """Detect soft delete pattern (setting deleted flags)"""
        evidence = []

        # Look for deleted/deleted_at updates
        soft_delete_ops = 0
        for step in result.steps:
            if step.type == "query":
                query_text = getattr(step, "expression", "") or getattr(step, "sql", "") or ""
                if query_text and isinstance(query_text, str):
                    query_upper = query_text.upper()
                    if "UPDATE" in query_upper and (
                        "DELETED" in query_upper or "DELETED_AT" in query_upper
                    ):
                        soft_delete_ops += 1
                        evidence.append("Found soft delete operation")

        if soft_delete_ops >= 1:
            return DetectedPattern(
                name="soft_delete",
                confidence=0.85,
                description="Function implements soft delete pattern",
                evidence=evidence,
            )

        return None

    def _detect_validation_chain_pattern(self, result: ConversionResult) -> DetectedPattern | None:
        """Detect validation chain pattern (multiple checks)"""
        evidence = []

        # Count validation operations
        validation_checks = 0
        if_statements = 0

        for step in result.steps:
            if step.type == "if":
                if_statements += 1
                condition = getattr(step, "condition", "") or ""
                if condition and isinstance(condition, str):
                    condition_upper = condition.upper()
                    # Look for validation keywords
                    if any(
                        keyword in condition_upper
                        for keyword in ["NULL", "EMPTY", "VALID", "EXISTS"]
                    ):
                        validation_checks += 1
                        evidence.append(f"Found validation check: {condition[:30]}...")

        if validation_checks >= 2 and if_statements >= 2:
            confidence = min(0.75 + (validation_checks * 0.05), 0.9)
            return DetectedPattern(
                name="exception_handling",
                confidence=confidence,
                description="Function implements exception handling with try/catch blocks",
                evidence=evidence,
            )

        return None

    def _detect_recursive_pattern(self, result: ConversionResult) -> DetectedPattern | None:
        """Detect recursive CTEs and hierarchy traversal"""
        evidence = []

        # Get all CTE steps
        cte_steps = [step for step in result.steps if step.type == "cte"]

        if not cte_steps:
            return None

        # Use CTEParser to detect patterns
        patterns = self.cte_parser.detect_patterns(cte_steps)

        if "recursive_hierarchy" in patterns:
            evidence.append("CTEParser detected recursive hierarchy pattern")

        # Additional evidence from step analysis
        for step in cte_steps:
            evidence.append(f"Found CTE: {step.cte_name}")

            # Check for hierarchy keywords in the CTE query
            if step.cte_query and any(
                kw in step.cte_query.upper() for kw in ["UNION", "PARENT", "CHILD", "LEVEL"]
            ):
                evidence.append("Detected hierarchy traversal pattern")

            # Check if this looks like a recursive pattern (has UNION and references itself)
            if step.cte_query and "UNION" in step.cte_query.upper():
                # Look for self-reference in the query
                if step.cte_name and step.cte_name in step.cte_query:
                    evidence.append(f"Detected recursive self-reference in {step.cte_name}")

        if evidence and len(evidence) >= 2:  # Need at least CTE + one pattern indicator
            return DetectedPattern(
                name="recursive_hierarchy",
                confidence=0.85,
                description="Function implements recursive hierarchy traversal",
                evidence=evidence,
            )

        return None

    def _detect_window_function_pattern(self, result: ConversionResult) -> DetectedPattern | None:
        """Detect window functions with complex frames"""
        evidence = []

        window_functions = [
            "ROW_NUMBER",
            "RANK",
            "DENSE_RANK",
            "NTILE",
            "LAG",
            "LEAD",
            "FIRST_VALUE",
            "LAST_VALUE",
        ]

        for step in result.steps:
            if step.type in ["query", "return_table"]:
                # Check both expression and sql attributes
                query_text = (
                    getattr(step, "expression", "")
                    or getattr(step, "sql", "")
                    or getattr(step, "return_table_query", "")
                    or ""
                )
                if query_text and isinstance(query_text, str):
                    query_upper = query_text.upper()
                    for func in window_functions:
                        if f"{func}(" in query_upper:
                            evidence.append(f"Found window function: {func}")
                            break

                    # Check for OVER clause with complex framing
                    if "OVER (" in query_upper and any(
                        kw in query_upper for kw in ["ROWS", "RANGE", "GROUPS"]
                    ):
                        evidence.append("Detected complex window framing")

        if evidence:
            confidence = min(0.8 + (len(evidence) * 0.05), 0.9)
            return DetectedPattern(
                name="window_functions",
                confidence=confidence,
                description="Function uses window functions for analytical queries",
                evidence=evidence,
            )

        return None

    def _detect_aggregate_pattern(self, result: ConversionResult) -> DetectedPattern | None:
        """Detect aggregate functions with FILTER/OVER clauses"""
        evidence = []

        aggregate_functions = ["COUNT", "SUM", "AVG", "MIN", "MAX", "STDDEV", "VARIANCE"]

        for step in result.steps:
            if step.type in ["query", "return_table"]:
                # Check both expression and sql attributes
                query_text = (
                    getattr(step, "expression", "")
                    or getattr(step, "sql", "")
                    or getattr(step, "return_table_query", "")
                    or ""
                )
                if query_text and isinstance(query_text, str):
                    query_upper = query_text.upper()

                    # Check for aggregate functions with FILTER
                    for func in aggregate_functions:
                        if f"{func}(" in query_upper and "FILTER (" in query_upper:
                            evidence.append(f"Found filtered aggregate: {func} WITH FILTER")
                            break

                    # Check for aggregate functions with OVER (window aggregates)
                    if (
                        any(f"{func}(" in query_upper for func in aggregate_functions)
                        and "OVER (" in query_upper
                    ):
                        evidence.append("Detected window aggregates")

        if evidence:
            confidence = min(0.75 + (len(evidence) * 0.05), 0.85)
            return DetectedPattern(
                name="complex_aggregates",
                confidence=confidence,
                description="Function uses complex aggregate operations",
                evidence=evidence,
            )

        return None

    def _simplify_control_flow(self, result: ConversionResult) -> ConversionResult:
        """Simplify unnecessary control flow structures"""
        # For now, just detect potential simplifications
        # Future: actually modify the AST to simplify

        simplified_steps = []
        for step in result.steps:
            # Detect simple IF-THEN-RETURN patterns that could be simplified
            if (
                step.type == "if"
                and len(step.then_steps) == 1
                and step.then_steps[0].type == "return"
            ):
                # This is a guard clause - could potentially be simplified
                # For now, just pass through
                pass

            simplified_steps.append(step)

        result.steps = simplified_steps
        return result

    def _improve_naming(self, result: ConversionResult) -> ConversionResult:
        """Improve variable naming conventions"""
        # Apply naming improvements based on inferred purposes
        for step in result.steps:
            if step.type == "declare" and hasattr(step, "variable_name"):
                improved_name = self._improve_variable_name(step.variable_name)
                if improved_name != step.variable_name:
                    step.variable_name = improved_name

        return result

    def _improve_variable_name(self, var_name: str) -> str:
        """Improve a single variable name"""
        # Remove common prefixes
        if var_name.startswith("v_"):
            return var_name[2:]  # Remove 'v_' prefix
        elif var_name.startswith("p_"):
            return var_name[2:]  # Remove 'p_' prefix for parameters

        return var_name

    def _merge_universal_patterns(
        self, result: ConversionResult, universal_patterns: list[UniversalDetectedPattern]
    ) -> ConversionResult:
        """Merge universal patterns with SQL-specific patterns"""
        # Convert universal patterns to DetectedPattern format
        for universal_pattern in universal_patterns:
            # Check if we already have this pattern from SQL-specific detection
            existing_pattern = next(
                (p for p in self.detected_patterns if p.name == universal_pattern.name), None
            )

            if existing_pattern:
                # Merge evidence and take higher confidence
                existing_pattern.confidence = max(
                    existing_pattern.confidence, universal_pattern.confidence
                )
                existing_pattern.evidence.extend(
                    [e for e in universal_pattern.evidence if e not in existing_pattern.evidence]
                )
            else:
                # Add new pattern
                self.detected_patterns.append(
                    DetectedPattern(
                        name=universal_pattern.name,
                        confidence=universal_pattern.confidence,
                        description=f"Cross-language pattern: {universal_pattern.name}",
                        evidence=universal_pattern.evidence,
                    )
                )

        return result

    def _calculate_confidence_boost(
        self, result: ConversionResult, universal_patterns: list[UniversalDetectedPattern] = []
    ) -> float:
        """Calculate confidence boost from heuristics"""
        boost = 0.0

        # Boost from variable purpose inference
        if self.variable_purposes:
            avg_var_confidence = sum(p.confidence for p in self.variable_purposes.values()) / len(
                self.variable_purposes
            )
            boost += avg_var_confidence * 0.02  # Small boost per variable

        # Boost from universal pattern detection
        for universal_pattern in universal_patterns:
            # Universal patterns provide strong confidence boost
            pattern_boost = universal_pattern.confidence * 0.05  # 5% max boost per pattern
            boost += pattern_boost

        # Boost from pattern detection
        for pattern in self.detected_patterns:
            if pattern.name == "recursive_hierarchy":
                # Significant boost for complex recursive patterns
                boost += 0.15  # Boost confidence significantly for recursive CTEs
            elif pattern.name == "window_functions":
                boost += 0.12  # Good boost for window functions
            elif pattern.name == "complex_aggregates":
                boost += 0.10  # Moderate boost for complex aggregates
            elif pattern.name == "exception_handling":
                boost += 0.13  # Good boost for exception handling patterns
            elif pattern.name == "dynamic_sql":
                boost += 0.12  # Good boost for dynamic SQL patterns
            elif pattern.name == "control_flow":
                boost += 0.11  # Good boost for control flow patterns
            elif pattern.name == "window_functions":
                boost += 0.12  # Good boost for window function patterns
            elif pattern.name == "complex_aggregates":
                boost += 0.10  # Good boost for aggregate filter patterns
            else:
                boost += pattern.confidence * 0.03  # Boost per detected pattern

        # Cap the total boost - allow reaching 90% from algorithmic 85%
        return min(boost, 0.25)  # Allow higher boost for complex patterns

    def _detect_exception_handler_pattern(self, result: ConversionResult) -> DetectedPattern | None:
        """Detect exception handler pattern (try/catch blocks)"""
        evidence = []

        # Look for try_except steps
        try_except_steps = [step for step in result.steps if step.type == "try_except"]
        if try_except_steps:
            evidence.append(f"Found {len(try_except_steps)} try/except construct(s)")

        # Look for exception-related keywords in SQL
        for step in result.steps:
            if hasattr(step, "sql") and step.sql:
                sql_upper = step.sql.upper()
                if "WHEN" in sql_upper and "THEN" in sql_upper:
                    evidence.append("Found WHEN/THEN exception handling syntax")
                if "OTHERS" in sql_upper:
                    evidence.append("Found WHEN OTHERS clause")
                if "RAISE" in sql_upper:
                    evidence.append("Found RAISE statements in exception handling")

        if evidence:
            confidence = min(len(evidence) * 0.15, 0.25)  # Up to 25% confidence from evidence
            return DetectedPattern(
                name="exception_handling",
                confidence=confidence,
                description="Function implements exception handling with try/catch blocks",
                evidence=evidence,
            )

        return None

    def _detect_dynamic_sql_pattern(self, result: ConversionResult) -> DetectedPattern | None:
        """Detect dynamic SQL pattern (EXECUTE statements)"""
        evidence = []

        # Look for execute steps
        execute_steps = [step for step in result.steps if step.type == "execute"]
        if execute_steps:
            evidence.append(f"Found {len(execute_steps)} EXECUTE statement(s)")

        # Look for dynamic SQL keywords in steps
        for step in result.steps:
            if hasattr(step, "sql") and step.sql:
                sql_lower = step.sql.lower()
                if "dynamic" in sql_lower:
                    evidence.append("Found dynamic SQL execution")
                if "execute" in sql_lower:
                    evidence.append("Found EXECUTE keyword usage")
                if "using" in sql_lower:
                    evidence.append("Found parameterized EXECUTE with USING clause")

        if evidence:
            confidence = min(len(evidence) * 0.15, 0.25)  # Up to 25% confidence from evidence
            return DetectedPattern(
                name="dynamic_sql",
                confidence=confidence,
                description="Function implements dynamic SQL execution",
                evidence=evidence,
            )

        return None

    def _detect_cursor_operations_pattern(self, result: ConversionResult) -> DetectedPattern | None:
        """Detect cursor operations pattern (OPEN/FETCH/CLOSE)"""
        evidence = []

        # Look for cursor-related steps
        cursor_declare_steps = [step for step in result.steps if step.type == "cursor_declare"]
        cursor_open_steps = [step for step in result.steps if step.type == "cursor_open"]
        cursor_fetch_steps = [step for step in result.steps if step.type == "cursor_fetch"]
        cursor_close_steps = [step for step in result.steps if step.type == "cursor_close"]

        if cursor_declare_steps:
            evidence.append(f"Found {len(cursor_declare_steps)} cursor declaration(s)")
        if cursor_open_steps:
            evidence.append(f"Found {len(cursor_open_steps)} cursor OPEN operation(s)")
        if cursor_fetch_steps:
            evidence.append(f"Found {len(cursor_fetch_steps)} cursor FETCH operation(s)")
        if cursor_close_steps:
            evidence.append(f"Found {len(cursor_close_steps)} cursor CLOSE operation(s)")

        # Look for cursor keywords in SQL text
        for step in result.steps:
            if hasattr(step, "sql") and step.sql:
                sql_lower = step.sql.lower()
                if "cursor" in sql_lower:
                    evidence.append("Found CURSOR keyword in SQL")
                if "open" in sql_lower and "cursor" in sql_lower:
                    evidence.append("Found OPEN CURSOR pattern")
                if "fetch" in sql_lower and "into" in sql_lower:
                    evidence.append("Found FETCH ... INTO pattern")
                if "close" in sql_lower and "cursor" in sql_lower:
                    evidence.append("Found CLOSE CURSOR pattern")

        if evidence:
            confidence = min(len(evidence) * 0.12, 0.20)  # Up to 20% confidence from evidence
            return DetectedPattern(
                name="cursor_operations",
                confidence=confidence,
                description="Function implements cursor-based data processing",
                evidence=evidence,
            )

        return None

    def _detect_control_flow_pattern(self, result: ConversionResult) -> DetectedPattern | None:
        """Detect complex control flow pattern (FOR/IF-ELSIF/CONTINUE)"""
        evidence = []

        # Look for control flow steps
        for_loop_steps = [step for step in result.steps if step.type == "for_loop"]
        if for_loop_steps:
            evidence.append(f"Found {len(for_loop_steps)} FOR loop(s)")

        if_elseif_steps = [step for step in result.steps if step.type == "if_elseif"]
        if if_elseif_steps:
            evidence.append(f"Found {len(if_elseif_steps)} IF-ELSIF-ELSE construct(s)")

        continue_steps = [step for step in result.steps if step.type == "continue"]
        if continue_steps:
            evidence.append(f"Found {len(continue_steps)} CONTINUE statement(s)")

        # Look for control flow keywords in steps
        for step in result.steps:
            if hasattr(step, "sql") and step.sql:
                sql_lower = step.sql.lower()
                if "for" in sql_lower and "loop" in sql_lower:
                    evidence.append("Found FOR loop syntax")
                if "if" in sql_lower and "elsif" in sql_lower:
                    evidence.append("Found IF-ELSIF control flow")
                if "continue" in sql_lower:
                    evidence.append("Found loop control statements")

        if evidence:
            confidence = min(len(evidence) * 0.15, 0.25)  # Up to 25% confidence from evidence
            return DetectedPattern(
                name="control_flow",
                confidence=confidence,
                description="Function implements complex control flow with loops and conditional logic",
                evidence=evidence,
            )

        return None

    def _detect_window_function_pattern(self, result: ConversionResult) -> DetectedPattern | None:
        """Detect window function pattern (ROW_NUMBER, LAG, etc. with OVER clauses)"""
        evidence = []

        # Look for window_function steps
        window_steps = [step for step in result.steps if step.type == "window_function"]
        if window_steps:
            evidence.append(f"Found {len(window_steps)} window function construct(s)")

        # Look for window function keywords in steps
        for step in result.steps:
            if hasattr(step, "sql") and step.sql:
                sql_lower = step.sql.lower()
                if "over" in sql_lower:
                    evidence.append("Found OVER clauses for window functions")
                if "partition" in sql_lower:
                    evidence.append("Found PARTITION BY clauses")
                if "order by" in sql_lower and "over" in sql_lower:
                    evidence.append("Found ORDER BY in window functions")
                if any(
                    func in sql_lower
                    for func in [
                        "row_number",
                        "rank",
                        "dense_rank",
                        "lag",
                        "lead",
                        "first_value",
                        "last_value",
                    ]
                ):
                    evidence.append("Found window function calls (ROW_NUMBER, RANK, LAG, etc.)")

        if evidence:
            confidence = min(len(evidence) * 0.15, 0.25)  # Up to 25% confidence from evidence
            return DetectedPattern(
                name="window_functions",
                confidence=confidence,
                description="Function implements window functions with OVER clauses and complex frames",
                evidence=evidence,
            )

        return None

    def _detect_aggregate_filter_pattern(self, result: ConversionResult) -> DetectedPattern | None:
        """Detect aggregate functions with FILTER clauses pattern"""
        evidence = []

        # Look for aggregate steps
        aggregate_steps = [step for step in result.steps if step.type == "aggregate"]
        if aggregate_steps:
            evidence.append(f"Found {len(aggregate_steps)} aggregate function(s)")

        # Look for FILTER clauses in steps
        for step in result.steps:
            if hasattr(step, "sql") and step.sql:
                sql_lower = step.sql.lower()
                if "filter" in sql_lower:
                    evidence.append("Found FILTER clauses in aggregate functions")
                if "where" in sql_lower and "filter" in sql_lower:
                    evidence.append("Found conditional FILTER clauses")
                if any(agg in sql_lower for agg in ["count", "sum", "avg", "min", "max"]):
                    evidence.append("Found standard aggregate functions")

        if evidence:
            confidence = min(len(evidence) * 0.15, 0.25)  # Up to 25% confidence from evidence
            return DetectedPattern(
                name="complex_aggregates",
                confidence=confidence,
                description="Function implements complex aggregate functions with FILTER clauses",
                evidence=evidence,
            )

        return None
