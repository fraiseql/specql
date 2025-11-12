"""
Query optimization for pattern-generated SQL

Analyzes and optimizes generated SQL for better performance
"""

from typing import Dict, List, Any
from dataclasses import dataclass
import re


@dataclass
class OptimizationSuggestion:
    """A suggested optimization for SQL"""

    type: str  # 'index', 'query_rewrite', 'structure_change', etc.
    description: str
    sql_impact: str
    estimated_improvement: str
    implementation_complexity: str
    priority: str  # 'high', 'medium', 'low'


@dataclass
class QueryAnalysis:
    """Analysis of a SQL query"""

    query_type: str  # 'SELECT', 'INSERT', 'UPDATE', 'DELETE'
    tables_accessed: List[str]
    columns_accessed: Dict[str, List[str]]
    where_conditions: List[str]
    joins: List[str]
    estimated_complexity: str
    potential_issues: List[str]
    optimization_suggestions: List[OptimizationSuggestion]


class QueryOptimizer:
    """Optimizes pattern-generated SQL queries"""

    def __init__(self):
        self.index_patterns = {
            "uuid_pk": r"WHERE id = \$[\w_]+",
            "tenant_filter": r"tenant_id = \$[\w_]+",
            "status_filter": r"status = \'[\w_]+\'",
            "date_range": r"created_at BETWEEN \$[\w_]+ AND \$[\w_]+",
            "foreign_key": r"(\w+_id) = \$[\w_]+",
            "composite_status_date": r"status = \'[\w_]+\' AND created_at",
            "text_search": r"(\w+) ILIKE \$[\w_]+",
        }

    def analyze_query(self, sql: str) -> QueryAnalysis:
        """Analyze a SQL query for optimization opportunities"""
        # Parse query type
        query_type = self._extract_query_type(sql)

        # Extract tables
        tables = self._extract_tables(sql)

        # Extract columns
        columns = self._extract_columns(sql)

        # Extract WHERE conditions
        where_conditions = self._extract_where_conditions(sql)

        # Extract JOINs
        joins = self._extract_joins(sql)

        # Calculate complexity
        complexity = self._calculate_complexity(sql, where_conditions, joins)

        # Identify potential issues
        issues = self._identify_potential_issues(sql, where_conditions, joins)

        # Generate optimization suggestions
        suggestions = self._generate_optimization_suggestions(
            sql, query_type, tables, columns, where_conditions, joins
        )

        return QueryAnalysis(
            query_type=query_type,
            tables_accessed=tables,
            columns_accessed=columns,
            where_conditions=where_conditions,
            joins=joins,
            estimated_complexity=complexity,
            potential_issues=issues,
            optimization_suggestions=suggestions,
        )

    def _extract_query_type(self, sql: str) -> str:
        """Extract the query type from SQL"""
        sql_upper = sql.upper()
        if sql_upper.startswith("SELECT"):
            return "SELECT"
        elif sql_upper.startswith("INSERT"):
            return "INSERT"
        elif sql_upper.startswith("UPDATE"):
            return "UPDATE"
        elif sql_upper.startswith("DELETE"):
            return "DELETE"
        else:
            return "UNKNOWN"

    def _extract_tables(self, sql: str) -> List[str]:
        """Extract table names from SQL"""
        # Simple regex to find table references
        table_pattern = r"(?:FROM|UPDATE|INTO)\s+([\w.]+)"
        matches = re.findall(table_pattern, sql, re.IGNORECASE)
        return [match.split(".")[-1] for match in matches]

    def _extract_columns(self, sql: str) -> Dict[str, List[str]]:
        """Extract columns accessed per table"""
        columns = {}

        # Simple extraction - in real implementation would need more sophisticated parsing
        select_pattern = r"SELECT\s+(.*?)\s+FROM"
        select_match = re.search(select_pattern, sql, re.IGNORECASE | re.DOTALL)

        if select_match:
            select_clause = select_match.group(1)
            # Very basic column extraction
            col_matches = re.findall(r"(\w+)\.", select_clause)
            if col_matches:
                columns["main"] = list(set(col_matches))

        return columns

    def _extract_where_conditions(self, sql: str) -> List[str]:
        """Extract WHERE conditions"""
        where_pattern = r"WHERE\s+(.*?)(?:\s+(GROUP|ORDER|LIMIT)|$)"
        where_match = re.search(where_pattern, sql, re.IGNORECASE | re.DOTALL)

        if where_match:
            where_clause = where_match.group(1)
            # Split by AND/OR
            conditions = re.split(r"\s+(AND|OR)\s+", where_clause)
            return [cond.strip() for cond in conditions if cond.upper() not in ["AND", "OR"]]
        return []

    def _extract_joins(self, sql: str) -> List[str]:
        """Extract JOIN clauses"""
        join_pattern = r"(?:INNER\s+|LEFT\s+|RIGHT\s+|FULL\s+)?JOIN\s+([\w.]+)"
        matches = re.findall(join_pattern, sql, re.IGNORECASE)
        return matches

    def _calculate_complexity(self, sql: str, where_conditions: List[str], joins: List[str]) -> str:
        """Calculate query complexity"""
        complexity_score = 0

        # Base complexity
        complexity_score += len(where_conditions) * 2
        complexity_score += len(joins) * 3

        # Subqueries
        if "SELECT" in sql.upper() and "(" in sql:
            complexity_score += 5

        # Complex expressions
        if any(op in sql.upper() for op in ["LIKE", "ILIKE", "REGEX", "SIMILAR TO"]):
            complexity_score += 2

        # Determine complexity level
        if complexity_score <= 5:
            return "low"
        elif complexity_score <= 15:
            return "medium"
        else:
            return "high"

    def _identify_potential_issues(
        self, sql: str, where_conditions: List[str], joins: List[str]
    ) -> List[str]:
        """Identify potential performance issues"""
        issues = []

        # Check for SELECT *
        if "SELECT *" in sql.upper():
            issues.append("SELECT * used - consider specifying columns")

        # Check for missing WHERE clauses on large tables
        if not where_conditions and "SELECT" in sql.upper():
            issues.append("SELECT without WHERE clause may scan entire table")

        # Check for Cartesian products
        if len(joins) > 3:
            issues.append("Multiple JOINs detected - verify proper join conditions")

        # Check for non-indexable conditions
        for condition in where_conditions:
            if any(func in condition.upper() for func in ["UPPER(", "LOWER(", "SUBSTR("]):
                issues.append(f"Function on indexed column: {condition}")

        return issues

    def _generate_optimization_suggestions(
        self,
        sql: str,
        query_type: str,
        tables: List[str],
        columns: Dict[str, List[str]],
        where_conditions: List[str],
        joins: List[str],
    ) -> List[OptimizationSuggestion]:
        """Generate optimization suggestions"""
        suggestions = []

        # Index suggestions based on WHERE patterns
        for condition in where_conditions:
            for index_type, pattern in self.index_patterns.items():
                if re.search(pattern, condition, re.IGNORECASE):
                    suggestions.append(
                        OptimizationSuggestion(
                            type="index",
                            description=f"Consider adding {index_type} index for condition: {condition}",
                            sql_impact="Reduced index scans and improved query performance",
                            estimated_improvement="10-100x faster for filtered queries",
                            implementation_complexity="low",
                            priority="high"
                            if "uuid_pk" in index_type or "tenant_filter" in index_type
                            else "medium",
                        )
                    )
                    break

        # Query structure suggestions
        if query_type == "SELECT" and len(joins) > 2:
            suggestions.append(
                OptimizationSuggestion(
                    type="query_rewrite",
                    description="Complex query with multiple JOINs - consider breaking into smaller queries or using CTEs",
                    sql_impact="Improved readability and potential performance",
                    estimated_improvement="20-50% performance improvement",
                    implementation_complexity="medium",
                    priority="medium",
                )
            )

        # Materialized view suggestions for complex aggregations
        if "GROUP BY" in sql.upper() or "COUNT(" in sql.upper():
            suggestions.append(
                OptimizationSuggestion(
                    type="structure_change",
                    description="Consider materialized view for frequently accessed aggregations",
                    sql_impact="Pre-computed results for faster queries",
                    estimated_improvement="100-1000x faster for complex aggregations",
                    implementation_complexity="high",
                    priority="low",
                )
            )

        # Partitioning suggestions for large tables
        if any(table in ["audit_log", "event_log", "transaction_log"] for table in tables):
            suggestions.append(
                OptimizationSuggestion(
                    type="structure_change",
                    description="Consider table partitioning for time-series data",
                    sql_impact="Faster queries on partitioned data",
                    estimated_improvement="5-10x faster for date-filtered queries",
                    implementation_complexity="high",
                    priority="medium",
                )
            )

        return suggestions

    def optimize_pattern_sql(
        self, pattern_name: str, sql_template: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Optimize SQL generated from a pattern

        Args:
            pattern_name: Name of the pattern
            sql_template: Jinja2 SQL template
            config: Pattern configuration

        Returns:
            Optimization recommendations and improved SQL
        """
        # This would analyze the template and config to suggest optimizations
        # For now, return basic structure
        return {
            "pattern": pattern_name,
            "optimizations_applied": [],
            "performance_tips": [
                "Ensure tenant_id is always included in WHERE clauses",
                "Use appropriate indexes for frequently filtered columns",
                "Consider query result caching for read-heavy patterns",
            ],
            "estimated_performance_impact": "baseline",
        }


class PatternPerformanceOptimizer:
    """Optimizes entire pattern libraries for performance"""

    def __init__(self):
        self.query_optimizer = QueryOptimizer()
        self.performance_profiles = {}

    def analyze_pattern_library(self, stdlib_path: str) -> Dict[str, Any]:
        """Analyze entire pattern library for performance characteristics"""
        # This would scan all patterns and analyze their SQL generation
        return {
            "total_patterns": 0,
            "patterns_analyzed": 0,
            "performance_profile": "baseline",
            "recommendations": [],
        }

    def generate_performance_report(self, entity_sql: Dict[str, str]) -> str:
        """Generate comprehensive performance report for entity SQL"""
        report_lines = ["# 🚀 SQL Performance Analysis Report", ""]

        total_optimizations = 0

        for action_name, sql in entity_sql.items():
            report_lines.append(f"## {action_name}")
            analysis = self.query_optimizer.analyze_query(sql)

            report_lines.append(f"- **Query Type**: {analysis.query_type}")
            report_lines.append(f"- **Complexity**: {analysis.estimated_complexity}")
            report_lines.append(f"- **Tables**: {', '.join(analysis.tables_accessed)}")

            if analysis.potential_issues:
                report_lines.append("- **Issues Found**:")
                for issue in analysis.potential_issues:
                    report_lines.append(f"  - ⚠️ {issue}")

            if analysis.optimization_suggestions:
                report_lines.append("- **Optimization Suggestions**:")
                total_optimizations += len(analysis.optimization_suggestions)
                for suggestion in analysis.optimization_suggestions:
                    priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}[
                        suggestion.priority
                    ]
                    report_lines.append(
                        f"  - {priority_emoji} **{suggestion.type}**: {suggestion.description}"
                    )
                    report_lines.append(f"    - Impact: {suggestion.sql_impact}")
                    report_lines.append(f"    - Improvement: {suggestion.estimated_improvement}")
                    report_lines.append(f"    - Complexity: {suggestion.implementation_complexity}")

            report_lines.append("")

        report_lines.append("## 📊 Summary")
        report_lines.append(f"- **Total Actions Analyzed**: {len(entity_sql)}")
        report_lines.append(f"- **Optimization Opportunities**: {total_optimizations}")

        if total_optimizations > 0:
            report_lines.append("- **Next Steps**:")
            report_lines.append("  1. Review high-priority optimizations first")
            report_lines.append("  2. Implement suggested indexes")
            report_lines.append("  3. Test performance improvements")
            report_lines.append("  4. Monitor query performance in production")

        return "\n".join(report_lines)
