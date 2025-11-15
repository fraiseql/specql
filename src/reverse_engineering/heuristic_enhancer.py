"""
Heuristic Enhancer: Improve SQL → SpecQL conversion with pattern detection and heuristics

Improves confidence from 85% → 90% through:
- Variable purpose inference (total/count/flag/temp)
- Pattern detection (state machines, audit trails, etc.)
- Control flow simplification
- Variable naming improvements
"""

from typing import List, Optional, Set
from dataclasses import dataclass
from src.reverse_engineering.ast_to_specql_mapper import ConversionResult


@dataclass
class VariablePurpose:
    """Inferred purpose of a variable"""
    name: str
    purpose: str  # 'total', 'count', 'flag', 'temp', 'accumulator', 'result', 'unknown'
    confidence: float
    evidence: List[str]


@dataclass
class DetectedPattern:
    """Detected domain pattern"""
    name: str
    confidence: float
    description: str
    evidence: List[str]


class HeuristicEnhancer:
    """
    Enhance conversion results with heuristics

    Improves algorithmic conversion through pattern detection and inference
    """

    def __init__(self):
        self.variable_purposes = {}
        self.detected_patterns = []

    def enhance(self, result: ConversionResult) -> ConversionResult:
        """
        Enhance conversion result with heuristics

        Args:
            result: ConversionResult from algorithmic parser

        Returns:
            Enhanced ConversionResult with improved confidence
        """
        # Reset state
        self.variable_purposes = {}
        self.detected_patterns = []

        # Apply enhancements in order
        result = self._infer_variable_purposes(result)
        result = self._detect_patterns(result)
        result = self._simplify_control_flow(result)
        result = self._improve_naming(result)

        # Update confidence based on enhancements
        initial_confidence = result.confidence
        confidence_boost = self._calculate_confidence_boost(result)
        result.confidence = min(initial_confidence + confidence_boost, 0.90)
        # Don't decrease confidence below initial value
        result.confidence = max(result.confidence, initial_confidence)

        # Add metadata
        if not hasattr(result, 'metadata'):
            result.metadata = {}
        result.metadata['detected_patterns'] = [p.name for p in self.detected_patterns]
        result.metadata['variable_purposes'] = {
            name: purpose.purpose for name, purpose in self.variable_purposes.items()
        }

        return result

    def _infer_variable_purposes(self, result: ConversionResult) -> ConversionResult:
        """Infer the purpose of variables based on usage patterns"""
        variables = self._extract_variables(result)

        for var_name in variables:
            purpose = self._infer_variable_purpose(var_name, result)
            if purpose:
                self.variable_purposes[var_name] = purpose

        return result

    def _extract_variables(self, result: ConversionResult) -> Set[str]:
        """Extract all variable names from the conversion result"""
        variables = set()

        for step in result.steps:
            if step.type == "declare" and hasattr(step, 'variable_name'):
                variables.add(step.variable_name)

            # Check for variable usage in expressions
            if hasattr(step, 'expression') and step.expression:
                variables.update(self._extract_vars_from_expression(step.expression))

            if hasattr(step, 'condition') and step.condition:
                variables.update(self._extract_vars_from_expression(step.condition))

        return variables

    def _extract_vars_from_expression(self, expression: str) -> Set[str]:
        """Extract variable names from SQL expression"""
        variables = set()

        # Simple heuristic: look for v_ prefixed variables
        import re
        var_matches = re.findall(r'\bv_\w+', expression)
        variables.update(var_matches)

        # Also look for parameter references
        param_matches = re.findall(r'\bp_\w+', expression)
        variables.update(param_matches)

        return variables

    def _infer_variable_purpose(self, var_name: str, result: ConversionResult) -> Optional[VariablePurpose]:
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
        if any(keyword in name_lower for keyword in ['total', 'sum', 'amount', 'balance']):
            purpose = "total"
            confidence = 0.8
            evidence.append(f"Name contains '{[k for k in ['total', 'sum', 'amount', 'balance'] if k in name_lower][0]}'")

        # Count patterns
        elif any(keyword in name_lower for keyword in ['count', 'cnt', 'num', 'qty', 'quantity']):
            purpose = "count"
            confidence = 0.8
            evidence.append(f"Name contains '{[k for k in ['count', 'cnt', 'num', 'qty', 'quantity'] if k in name_lower][0]}'")

        # Flag/boolean patterns
        elif any(keyword in name_lower for keyword in ['flag', 'is_', 'has_', 'can_', 'should_', 'valid']):
            purpose = "flag"
            confidence = 0.7
            evidence.append(f"Name suggests boolean flag: '{var_name}'")

        # Result patterns
        elif any(keyword in name_lower for keyword in ['result', 'output', 'ret']):
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
                name=var_name,
                purpose=purpose,
                confidence=min(confidence, 1.0),
                evidence=evidence
            )

        return None

    def _analyze_variable_usage(self, var_name: str, result: ConversionResult) -> List[str]:
        """Analyze how a variable is used throughout the function"""
        evidence = []

        for step in result.steps:
            if step.type == "declare" and getattr(step, 'variable_name', None) == var_name:
                # Check initialization
                if hasattr(step, 'default_value'):
                    if step.default_value == "0":
                        evidence.append("initialized to 0")
                    elif str(step.default_value).upper() in ["TRUE", "FALSE"]:
                        evidence.append("initialized to boolean")

            elif step.type == "assign" and hasattr(step, 'variable_name') and step.variable_name == var_name:
                # Check assignment expressions
                expr = getattr(step, 'expression', '').upper()
                if 'SUM(' in expr:
                    evidence.append("used in SUM()")
                if 'COUNT(' in expr:
                    evidence.append("used in COUNT()")
                if 'AVG(' in expr:
                    evidence.append("used in AVG()")

            elif step.type == "query" and hasattr(step, 'into_variable') and step.into_variable == var_name:
                # Check SELECT INTO
                query = getattr(step, 'expression', '').upper()
                if 'SUM(' in query:
                    evidence.append("assigned from SUM() query")
                if 'COUNT(' in query:
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

        self.detected_patterns = patterns
        return result

    def _detect_state_machine_pattern(self, result: ConversionResult) -> Optional[DetectedPattern]:
        """Detect state machine pattern (status transitions)"""
        evidence = []

        # Look for status/state variables
        status_vars = []
        for var_name in self.variable_purposes:
            if self.variable_purposes[var_name].purpose == "flag":
                var_lower = var_name.lower()
                if any(state in var_lower for state in ['status', 'state', 'phase', 'stage']):
                    status_vars.append(var_name)
                    evidence.append(f"Found status variable: {var_name}")

        # Look for status transitions in queries
        status_transitions = 0
        for step in result.steps:
            if step.type == "query":
                # Check both expression and sql attributes
                query_text = getattr(step, 'expression', '') or getattr(step, 'sql', '') or ''
                if query_text and isinstance(query_text, str):
                    query_upper = query_text.upper()
                    if 'UPDATE' in query_upper and 'STATUS' in query_upper:
                        status_transitions += 1
                        evidence.append("Found status update query")

        if len(status_vars) >= 1 and status_transitions >= 1:
            confidence = min(0.8 + (len(status_vars) * 0.1) + (status_transitions * 0.1), 0.95)
            return DetectedPattern(
                name="state_machine",
                confidence=confidence,
                description="Function implements state/status transitions",
                evidence=evidence
            )

        return None

    def _detect_audit_trail_pattern(self, result: ConversionResult) -> Optional[DetectedPattern]:
        """Detect audit trail pattern (logging changes)"""
        evidence = []

        # Look for audit-related operations
        audit_operations = 0
        for step in result.steps:
            if step.type == "query":
                query_text = getattr(step, 'expression', '') or getattr(step, 'sql', '') or ''
                if query_text and isinstance(query_text, str):
                    query_upper = query_text.upper()
                    audit_keywords = ['INSERT INTO', 'AUDIT', 'LOG', 'HISTORY', 'TRAIL']
                    if any(keyword in query_upper for keyword in audit_keywords):
                        audit_operations += 1
                        evidence.append(f"Found audit operation: {query_text[:50]}...")

        # Look for timestamp/user tracking
        timestamp_vars = [v for v in self.variable_purposes
                         if 'time' in self.variable_purposes[v].purpose or 'user' in v.lower()]
        if timestamp_vars:
            evidence.append(f"Found timestamp/user variables: {timestamp_vars}")

        if audit_operations >= 1:
            confidence = min(0.7 + (audit_operations * 0.1), 0.9)
            return DetectedPattern(
                name="audit_trail",
                confidence=confidence,
                description="Function implements audit trail logging",
                evidence=evidence
            )

        return None

    def _detect_soft_delete_pattern(self, result: ConversionResult) -> Optional[DetectedPattern]:
        """Detect soft delete pattern (setting deleted flags)"""
        evidence = []

        # Look for deleted/deleted_at updates
        soft_delete_ops = 0
        for step in result.steps:
            if step.type == "query":
                query_text = getattr(step, 'expression', '') or getattr(step, 'sql', '') or ''
                if query_text and isinstance(query_text, str):
                    query_upper = query_text.upper()
                    if 'UPDATE' in query_upper and ('DELETED' in query_upper or 'DELETED_AT' in query_upper):
                        soft_delete_ops += 1
                        evidence.append("Found soft delete operation")

        if soft_delete_ops >= 1:
            return DetectedPattern(
                name="soft_delete",
                confidence=0.85,
                description="Function implements soft delete pattern",
                evidence=evidence
            )

        return None

    def _detect_validation_chain_pattern(self, result: ConversionResult) -> Optional[DetectedPattern]:
        """Detect validation chain pattern (multiple checks)"""
        evidence = []

        # Count validation operations
        validation_checks = 0
        if_statements = 0

        for step in result.steps:
            if step.type == "if":
                if_statements += 1
                condition = getattr(step, 'condition', '') or ''
                if condition and isinstance(condition, str):
                    condition_upper = condition.upper()
                    # Look for validation keywords
                    if any(keyword in condition_upper for keyword in ['NULL', 'EMPTY', 'VALID', 'EXISTS']):
                        validation_checks += 1
                        evidence.append(f"Found validation check: {condition[:30]}...")

        if validation_checks >= 2 and if_statements >= 2:
            confidence = min(0.75 + (validation_checks * 0.05), 0.9)
            return DetectedPattern(
                name="validation_chain",
                confidence=confidence,
                description="Function implements validation chain pattern",
                evidence=evidence
            )

        return None

    def _simplify_control_flow(self, result: ConversionResult) -> ConversionResult:
        """Simplify unnecessary control flow structures"""
        # For now, just detect potential simplifications
        # Future: actually modify the AST to simplify

        simplified_steps = []
        for step in result.steps:
            # Detect simple IF-THEN-RETURN patterns that could be simplified
            if step.type == "if" and len(step.then_steps) == 1 and step.then_steps[0].type == "return":
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
            if step.type == "declare" and hasattr(step, 'variable_name'):
                improved_name = self._improve_variable_name(step.variable_name)
                if improved_name != step.variable_name:
                    step.variable_name = improved_name

        return result

    def _improve_variable_name(self, var_name: str) -> str:
        """Improve a single variable name"""
        # Remove common prefixes
        if var_name.startswith('v_'):
            return var_name[2:]  # Remove 'v_' prefix
        elif var_name.startswith('p_'):
            return var_name[2:]  # Remove 'p_' prefix for parameters

        return var_name

    def _calculate_confidence_boost(self, result: ConversionResult) -> float:
        """Calculate confidence boost from heuristics"""
        boost = 0.0

        # Boost from variable purpose inference
        if self.variable_purposes:
            avg_var_confidence = sum(p.confidence for p in self.variable_purposes.values()) / len(self.variable_purposes)
            boost += avg_var_confidence * 0.02  # Small boost per variable

        # Boost from pattern detection
        for pattern in self.detected_patterns:
            boost += pattern.confidence * 0.03  # Boost per detected pattern

        # Cap the total boost - allow reaching 90% from algorithmic 85%
        return min(boost, 0.05)  # Max 5% boost to reach 90% confidence