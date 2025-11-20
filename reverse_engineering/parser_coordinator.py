"""
ParserCoordinator - Coordinate specialized SQL parsers

Separates parser coordination logic from AST mapping logic.
Provides centralized metrics and monitoring.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from reverse_engineering.aggregate_filter_parser import AggregateFilterParser
from reverse_engineering.control_flow_parser import ControlFlowParser
from reverse_engineering.cte_parser import CTEParser
from reverse_engineering.cursor_operations_parser import CursorOperationsParser
from reverse_engineering.dynamic_sql_parser import DynamicSQLParser
from reverse_engineering.exception_handler_parser import ExceptionHandlerParser
from reverse_engineering.window_function_parser import WindowFunctionParser

logger = logging.getLogger(__name__)


@dataclass
class ParserResult:
    """Result from a specialized parser"""

    steps: list[Any]  # ActionSteps from parser
    confidence_boost: float  # How much to boost confidence (0.0 - 1.0)
    parser_used: str  # Which parser produced this ('cte', 'exception', etc.)
    metadata: dict[str, Any] = field(default_factory=dict)
    success: bool = True


class ParserCoordinator:
    """
    Coordinate specialized SQL parsers.

    Responsibilities:
    - Decide which parsers to use based on SQL content
    - Execute parsers and collect results
    - Track metrics (attempts, successes, failures)
    - Provide observability into parser performance

    Usage:
        coordinator = ParserCoordinator()

        # Check if parser should be used
        if coordinator.should_use_cte_parser(sql):
            result = coordinator.parse_with_cte(sql)

        # Or get all applicable parsers
        results = coordinator.parse_with_best_parsers(sql)

        # Check metrics
        rates = coordinator.get_success_rates()
    """

    def __init__(self):
        # Initialize all specialized parsers
        self.cte_parser = CTEParser()
        self.exception_parser = ExceptionHandlerParser()
        self.dynamic_sql_parser = DynamicSQLParser()
        self.control_flow_parser = ControlFlowParser()
        self.window_parser = WindowFunctionParser()
        self.aggregate_parser = AggregateFilterParser()
        self.cursor_parser = CursorOperationsParser()

        # Metrics tracking
        self.metrics = {
            "cte": {"attempts": 0, "successes": 0, "failures": 0},
            "exception": {"attempts": 0, "successes": 0, "failures": 0},
            "dynamic_sql": {"attempts": 0, "successes": 0, "failures": 0},
            "control_flow": {"attempts": 0, "successes": 0, "failures": 0},
            "window": {"attempts": 0, "successes": 0, "failures": 0},
            "aggregate": {"attempts": 0, "successes": 0, "failures": 0},
            "cursor": {"attempts": 0, "successes": 0, "failures": 0},
        }

    # ==================== Parser Selection Methods ====================

    def should_use_cte_parser(self, sql: str) -> bool:
        """Check if SQL contains CTE (WITH clause)"""
        return bool(re.search(r"\bWITH\b", sql, re.IGNORECASE))

    def should_use_exception_parser(self, sql: str) -> bool:
        """Check if SQL contains exception handling"""
        return bool(re.search(r"\bEXCEPTION\b", sql, re.IGNORECASE))

    def should_use_dynamic_sql_parser(self, sql: str) -> bool:
        """Check if SQL contains dynamic SQL (EXECUTE)"""
        return bool(re.search(r"\bEXECUTE\b", sql, re.IGNORECASE))

    def should_use_control_flow_parser(self, sql: str) -> bool:
        """Check if SQL contains control flow (FOR loops, etc.)"""
        patterns = [r"\bFOR\b", r"\bLOOP\b", r"\bWHILE\b"]
        return any(re.search(p, sql, re.IGNORECASE) for p in patterns)

    def should_use_window_parser(self, sql: str) -> bool:
        """Check if SQL contains window functions"""
        patterns = [r"\bOVER\s*\(", r"\bPARTITION\s+BY\b", r"\bROW_NUMBER\b"]
        return any(re.search(p, sql, re.IGNORECASE) for p in patterns)

    def should_use_aggregate_parser(self, sql: str) -> bool:
        """Check if SQL contains aggregate functions with FILTER"""
        return bool(re.search(r"\bFILTER\s*\(\s*WHERE\b", sql, re.IGNORECASE))

    def should_use_cursor_parser(self, sql: str) -> bool:
        """Check if SQL contains cursor operations"""
        patterns = [r"\bCURSOR\b", r"\bFETCH\b", r"\bOPEN\b", r"\bCLOSE\b"]
        return any(re.search(p, sql, re.IGNORECASE) for p in patterns)

    # ==================== Parser Execution Methods ====================

    def parse_with_cte(self, sql: str) -> ParserResult | None:
        """Parse SQL with CTE parser"""
        self.metrics["cte"]["attempts"] += 1

        try:
            steps = self.cte_parser.parse(sql)

            if steps:
                self.metrics["cte"]["successes"] += 1

                # Determine metadata and confidence boost
                is_recursive = "RECURSIVE" in sql.upper()
                cte_count = len(re.findall(r"(\w+)\s+AS\s*\(", sql))

                confidence_boost = 0.10
                if is_recursive:
                    confidence_boost = 0.15  # Recursive CTEs are complex
                if cte_count > 2:
                    confidence_boost += 0.05  # Multiple CTEs bonus

                return ParserResult(
                    steps=steps if isinstance(steps, list) else [steps],
                    confidence_boost=confidence_boost,
                    parser_used="cte",
                    metadata={
                        "is_recursive": is_recursive,
                        "cte_count": cte_count,
                    },
                    success=True,
                )
            else:
                self.metrics["cte"]["failures"] += 1
                return None

        except Exception as e:
            self.metrics["cte"]["failures"] += 1
            logger.warning(f"CTE parser failed: {e}")
            return None

    def parse_with_exception(self, sql: str) -> ParserResult | None:
        """Parse SQL with exception handler parser"""
        self.metrics["exception"]["attempts"] += 1

        try:
            steps = self.exception_parser.parse(sql)

            if steps:
                self.metrics["exception"]["successes"] += 1

                # Count exception handlers
                handler_count = len(re.findall(r"\bWHEN\b", sql, re.IGNORECASE))

                return ParserResult(
                    steps=steps if isinstance(steps, list) else [steps],
                    confidence_boost=0.05,  # Error handling improves confidence
                    parser_used="exception",
                    metadata={"handler_count": handler_count},
                    success=True,
                )
            else:
                self.metrics["exception"]["failures"] += 1
                return None

        except Exception as e:
            self.metrics["exception"]["failures"] += 1
            logger.warning(f"Exception parser failed: {e}")
            return None

    def parse_with_dynamic_sql(self, sql: str) -> ParserResult | None:
        """Parse SQL with dynamic SQL parser"""
        self.metrics["dynamic_sql"]["attempts"] += 1

        try:
            steps = self.dynamic_sql_parser.parse(sql)

            if steps:
                self.metrics["dynamic_sql"]["successes"] += 1

                # Dynamic SQL reduces confidence (security/complexity concern)
                return ParserResult(
                    steps=steps if isinstance(steps, list) else [steps],
                    confidence_boost=-0.10,  # NEGATIVE boost (reduces confidence)
                    parser_used="dynamic_sql",
                    metadata={"has_format": "format(" in sql.lower()},
                    success=True,
                )
            else:
                self.metrics["dynamic_sql"]["failures"] += 1
                return None

        except Exception as e:
            self.metrics["dynamic_sql"]["failures"] += 1
            logger.warning(f"Dynamic SQL parser failed: {e}")
            return None

    def parse_with_control_flow(self, sql: str) -> ParserResult | None:
        """Parse SQL with control flow parser"""
        self.metrics["control_flow"]["attempts"] += 1

        try:
            steps = self.control_flow_parser.parse(sql)

            if steps:
                self.metrics["control_flow"]["successes"] += 1

                return ParserResult(
                    steps=steps if isinstance(steps, list) else [steps],
                    confidence_boost=0.08,
                    parser_used="control_flow",
                    metadata={},
                    success=True,
                )
            else:
                self.metrics["control_flow"]["failures"] += 1
                return None

        except Exception as e:
            self.metrics["control_flow"]["failures"] += 1
            logger.warning(f"Control flow parser failed: {e}")
            return None

    def parse_with_window(self, sql: str) -> ParserResult | None:
        """Parse SQL with window function parser"""
        self.metrics["window"]["attempts"] += 1

        try:
            steps = self.window_parser.parse(sql)

            if steps:
                self.metrics["window"]["successes"] += 1

                return ParserResult(
                    steps=steps if isinstance(steps, list) else [steps],
                    confidence_boost=0.08,
                    parser_used="window",
                    metadata={},
                    success=True,
                )
            else:
                self.metrics["window"]["failures"] += 1
                return None

        except Exception as e:
            self.metrics["window"]["failures"] += 1
            logger.warning(f"Window function parser failed: {e}")
            return None

    def parse_with_aggregate(self, sql: str) -> ParserResult | None:
        """Parse SQL with aggregate filter parser"""
        self.metrics["aggregate"]["attempts"] += 1

        try:
            steps = self.aggregate_parser.parse(sql)

            if steps:
                self.metrics["aggregate"]["successes"] += 1

                return ParserResult(
                    steps=steps if isinstance(steps, list) else [steps],
                    confidence_boost=0.07,
                    parser_used="aggregate",
                    metadata={},
                    success=True,
                )
            else:
                self.metrics["aggregate"]["failures"] += 1
                return None

        except Exception as e:
            self.metrics["aggregate"]["failures"] += 1
            logger.warning(f"Aggregate parser failed: {e}")
            return None

    def parse_with_cursor(self, sql: str) -> ParserResult | None:
        """Parse SQL with cursor operations parser"""
        self.metrics["cursor"]["attempts"] += 1

        try:
            steps = self.cursor_parser.parse(sql)

            if steps:
                self.metrics["cursor"]["successes"] += 1

                return ParserResult(
                    steps=steps if isinstance(steps, list) else [steps],
                    confidence_boost=0.08,
                    parser_used="cursor",
                    metadata={},
                    success=True,
                )
            else:
                self.metrics["cursor"]["failures"] += 1
                return None

        except Exception as e:
            self.metrics["cursor"]["failures"] += 1
            logger.warning(f"Cursor parser failed: {e}")
            return None

    # ==================== Coordination Method ====================

    def parse_with_best_parsers(self, sql: str) -> list[ParserResult]:
        """
        Parse SQL with all applicable parsers.

        Returns list of ParserResults from successful parsers.
        """
        results = []

        # Try each parser that matches the SQL
        if self.should_use_cte_parser(sql):
            result = self.parse_with_cte(sql)
            if result:
                results.append(result)

        if self.should_use_exception_parser(sql):
            result = self.parse_with_exception(sql)
            if result:
                results.append(result)

        if self.should_use_dynamic_sql_parser(sql):
            result = self.parse_with_dynamic_sql(sql)
            if result:
                results.append(result)

        if self.should_use_control_flow_parser(sql):
            result = self.parse_with_control_flow(sql)
            if result:
                results.append(result)

        if self.should_use_window_parser(sql):
            result = self.parse_with_window(sql)
            if result:
                results.append(result)

        if self.should_use_aggregate_parser(sql):
            result = self.parse_with_aggregate(sql)
            if result:
                results.append(result)

        if self.should_use_cursor_parser(sql):
            result = self.parse_with_cursor(sql)
            if result:
                results.append(result)

        return results

    # ==================== Metrics Methods ====================

    def get_metrics(self) -> dict[str, dict[str, int]]:
        """Get raw metrics for all parsers"""
        return self.metrics.copy()

    def get_success_rates(self) -> dict[str, float]:
        """Calculate success rate for each parser"""
        rates = {}

        for parser_name, metrics in self.metrics.items():
            attempts = metrics["attempts"]
            successes = metrics["successes"]

            if attempts > 0:
                rates[parser_name] = successes / attempts
            else:
                rates[parser_name] = 0.0

        return rates

    def reset_metrics(self) -> None:
        """Reset all metrics to zero"""
        for parser_metrics in self.metrics.values():
            parser_metrics["attempts"] = 0
            parser_metrics["successes"] = 0
            parser_metrics["failures"] = 0

    def get_metrics_summary(self) -> str:
        """Get human-readable metrics summary"""
        rates = self.get_success_rates()

        lines = ["Parser Success Rates:"]
        for parser, rate in sorted(rates.items()):
            attempts = self.metrics[parser]["attempts"]
            if attempts > 0:
                lines.append(f"  {parser:15s}: {rate:6.1%} ({attempts} attempts)")

        return "\n".join(lines)
