"""
Pattern usage analytics and dashboard

Analyzes pattern adoption, usage statistics, and provides insights
for pattern library optimization.
"""

import yaml
from pathlib import Path
from collections import defaultdict, Counter
from dataclasses import dataclass
from typing import Dict, List, Any, Set
import json


@dataclass
class PatternUsage:
    """Usage statistics for a single pattern"""

    pattern_name: str
    usage_count: int
    entities: List[str]
    avg_complexity: float
    common_config_keys: List[str]


@dataclass
class PatternAnalytics:
    """Complete analytics report for pattern library"""

    total_entities: int
    entities_with_patterns: int
    total_pattern_usage: int
    pattern_breakdown: Dict[str, PatternUsage]
    adoption_rate: float
    most_popular_patterns: List[str]
    entities_without_patterns: List[str]
    recommendations: List[str]


class PatternAnalyticsEngine:
    """Analyzes pattern usage across SpecQL entities"""

    def __init__(self, entities_dir: Path, stdlib_dir: Path):
        self.entities_dir = entities_dir
        self.stdlib_dir = stdlib_dir
        self.available_patterns = self._load_available_patterns()

    def _load_available_patterns(self) -> Set[str]:
        """Load all available patterns from stdlib"""
        patterns = set()

        if not self.stdlib_dir.exists():
            return patterns

        # Look for pattern files in stdlib/actions
        actions_dir = self.stdlib_dir / "actions"
        if actions_dir.exists():
            for pattern_file in actions_dir.rglob("*.yaml"):
                try:
                    with open(pattern_file, "r") as f:
                        data = yaml.safe_load(f)
                        if isinstance(data, dict) and "name" in data:
                            patterns.add(data["name"])
                except Exception:
                    continue

        return patterns

    def analyze_entity(self, entity_path: Path) -> Dict[str, Any]:
        """Analyze a single entity file for pattern usage"""
        try:
            with open(entity_path, "r") as f:
                entity_data = yaml.safe_load(f)

            entity_name = entity_data.get("entity", "unknown")
            actions = entity_data.get("actions", [])

            pattern_usage = []
            for action in actions:
                if isinstance(action, dict) and "pattern" in action:
                    pattern_name = action["pattern"]
                    config = action.get("config", {})

                    pattern_usage.append(
                        {
                            "pattern": pattern_name,
                            "action": action.get("name", "unnamed"),
                            "config_keys": list(config.keys()) if isinstance(config, dict) else [],
                            "config_complexity": len(config) if isinstance(config, dict) else 0,
                        }
                    )

            return {
                "entity_name": entity_name,
                "has_patterns": len(pattern_usage) > 0,
                "pattern_count": len(pattern_usage),
                "patterns": pattern_usage,
            }

        except Exception as e:
            return {
                "entity_name": entity_path.stem,
                "has_patterns": False,
                "pattern_count": 0,
                "patterns": [],
                "error": str(e),
            }

    def analyze_all_entities(self) -> PatternAnalytics:
        """Analyze all entities in the entities directory"""
        entity_files = list(self.entities_dir.glob("**/*.yaml"))
        total_entities = len(entity_files)

        pattern_usage = defaultdict(list)
        entities_with_patterns = []
        entities_without_patterns = []

        all_pattern_details = []

        for entity_file in entity_files:
            analysis = self.analyze_entity(entity_file)

            if analysis["has_patterns"]:
                entities_with_patterns.append(analysis["entity_name"])
                all_pattern_details.extend(analysis["patterns"])

                for pattern_detail in analysis["patterns"]:
                    pattern_usage[pattern_detail["pattern"]].append(
                        {
                            "entity": analysis["entity_name"],
                            "action": pattern_detail["action"],
                            "config_keys": pattern_detail["config_keys"],
                            "complexity": pattern_detail["config_complexity"],
                        }
                    )
            else:
                entities_without_patterns.append(analysis["entity_name"])

        # Build pattern usage statistics
        pattern_breakdown = {}
        for pattern_name, usages in pattern_usage.items():
            entities = list(set(u["entity"] for u in usages))
            complexities = [u["complexity"] for u in usages]

            # Find most common config keys
            all_config_keys = []
            for u in usages:
                all_config_keys.extend(u["config_keys"])
            common_keys = [k for k, _ in Counter(all_config_keys).most_common(3)]

            pattern_breakdown[pattern_name] = PatternUsage(
                pattern_name=pattern_name,
                usage_count=len(usages),
                entities=entities,
                avg_complexity=sum(complexities) / len(complexities) if complexities else 0,
                common_config_keys=common_keys,
            )

        # Calculate adoption rate
        adoption_rate = len(entities_with_patterns) / total_entities if total_entities > 0 else 0

        # Find most popular patterns
        most_popular = sorted(
            pattern_breakdown.keys(), key=lambda p: pattern_breakdown[p].usage_count, reverse=True
        )[:5]

        # Generate recommendations
        recommendations = self._generate_recommendations(
            pattern_breakdown, entities_without_patterns, adoption_rate
        )

        return PatternAnalytics(
            total_entities=total_entities,
            entities_with_patterns=len(entities_with_patterns),
            total_pattern_usage=sum(len(usages) for usages in pattern_usage.values()),
            pattern_breakdown=pattern_breakdown,
            adoption_rate=adoption_rate,
            most_popular_patterns=most_popular,
            entities_without_patterns=entities_without_patterns,
            recommendations=recommendations,
        )

    def _generate_recommendations(
        self,
        pattern_breakdown: Dict[str, PatternUsage],
        entities_without_patterns: List[str],
        adoption_rate: float,
    ) -> List[str]:
        """Generate recommendations based on analytics"""
        recommendations = []

        # Adoption rate recommendations
        if adoption_rate < 0.5:
            recommendations.append(
                f"📈 Low adoption rate ({adoption_rate:.1%}). Consider pattern training or documentation improvements."
            )
        elif adoption_rate > 0.8:
            recommendations.append(
                f"✅ High adoption rate ({adoption_rate:.1%}). Pattern library is well-utilized!"
            )

        # Popular patterns
        if pattern_breakdown:
            top_pattern = max(pattern_breakdown.values(), key=lambda p: p.usage_count)
            recommendations.append(
                f"🏆 Most popular pattern: '{top_pattern.pattern_name}' used in {top_pattern.usage_count} actions"
            )

        # Entities without patterns
        if entities_without_patterns:
            recommendations.append(
                f"🎯 {len(entities_without_patterns)} entities without patterns. Consider migration analysis."
            )

        # Pattern complexity insights
        complex_patterns = [p for p in pattern_breakdown.values() if p.avg_complexity > 5]
        if complex_patterns:
            recommendations.append(
                f"🔧 {len(complex_patterns)} patterns have high configuration complexity. Consider simplification."
            )

        return recommendations

    def generate_dashboard_report(self) -> str:
        """Generate a comprehensive dashboard report"""
        analytics = self.analyze_all_entities()

        report = []
        report.append("# 📊 Pattern Analytics Dashboard")
        report.append("")

        # Summary section
        report.append("## 📈 Summary")
        report.append(f"- **Total Entities**: {analytics.total_entities}")
        report.append(f"- **Entities with Patterns**: {analytics.entities_with_patterns}")
        report.append(f"- **Pattern Adoption Rate**: {analytics.adoption_rate:.1%}")
        report.append(f"- **Total Pattern Usage**: {analytics.total_pattern_usage}")
        report.append("")

        # Pattern breakdown
        if analytics.pattern_breakdown:
            report.append("## 🔍 Pattern Usage Breakdown")
            report.append("| Pattern | Usage Count | Entities | Avg Complexity | Common Config |")
            report.append("|---------|-------------|----------|----------------|---------------|")

            for pattern_name, usage in analytics.pattern_breakdown.items():
                entities_str = ", ".join(usage.entities[:3])  # Show first 3
                if len(usage.entities) > 3:
                    entities_str += f" (+{len(usage.entities) - 3} more)"

                config_str = ", ".join(usage.common_config_keys[:2])  # Show top 2
                if len(usage.common_config_keys) > 2:
                    config_str += "..."

                report.append(
                    f"| {pattern_name} | {usage.usage_count} | {entities_str} | "
                    f"{usage.avg_complexity:.1f} | {config_str} |"
                )
            report.append("")

        # Most popular patterns
        if analytics.most_popular_patterns:
            report.append("## 🏆 Most Popular Patterns")
            for i, pattern in enumerate(analytics.most_popular_patterns[:3], 1):
                usage = analytics.pattern_breakdown[pattern]
                report.append(f"{i}. **{pattern}** - {usage.usage_count} usages")
            report.append("")

        # Entities without patterns
        if analytics.entities_without_patterns:
            report.append("## 🎯 Entities Without Patterns")
            for entity in analytics.entities_without_patterns[:5]:  # Show first 5
                report.append(f"- {entity}")
            if len(analytics.entities_without_patterns) > 5:
                report.append(f"- ... and {len(analytics.entities_without_patterns) - 5} more")
            report.append("")

        # Recommendations
        if analytics.recommendations:
            report.append("## 💡 Recommendations")
            for rec in analytics.recommendations:
                report.append(f"- {rec}")
            report.append("")

        # JSON export for further analysis
        report.append("## 📤 Export Data")
        report.append("```json")
        export_data = {
            "summary": {
                "total_entities": analytics.total_entities,
                "entities_with_patterns": analytics.entities_with_patterns,
                "adoption_rate": analytics.adoption_rate,
                "total_pattern_usage": analytics.total_pattern_usage,
            },
            "patterns": {
                name: {
                    "usage_count": usage.usage_count,
                    "entity_count": len(usage.entities),
                    "avg_complexity": usage.avg_complexity,
                }
                for name, usage in analytics.pattern_breakdown.items()
            },
        }
        report.append(json.dumps(export_data, indent=2))
        report.append("```")

        return "\n".join(report)


def run_pattern_analytics(entities_dir: Path, stdlib_dir: Path) -> str:
    """
    Run comprehensive pattern analytics

    Args:
        entities_dir: Directory containing entity YAML files
        stdlib_dir: Directory containing pattern library

    Returns:
        Formatted analytics report
    """
    engine = PatternAnalyticsEngine(entities_dir, stdlib_dir)
    return engine.generate_dashboard_report()


if __name__ == "__main__":
    # Example usage
    entities_dir = Path("entities")
    stdlib_dir = Path("stdlib")

    if entities_dir.exists() and stdlib_dir.exists():
        report = run_pattern_analytics(entities_dir, stdlib_dir)
        print(report)
    else:
        print("❌ Entities or stdlib directories not found")
        print(f"Entities dir: {entities_dir.absolute()}")
        print(f"Stdlib dir: {stdlib_dir.absolute()}")
