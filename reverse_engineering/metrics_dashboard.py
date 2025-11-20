"""
Parser Metrics Dashboard

Display real-time metrics from ParserCoordinator.
"""


def format_percentage(value: float) -> str:
    """Format float as percentage"""
    return f"{value * 100:6.1f}%"


def print_success_rates_table(rates: dict[str, float], metrics: dict[str, dict[str, int]]):
    """Print formatted success rates table"""
    print("\n" + "=" * 70)
    print("PARSER SUCCESS RATES")
    print("=" * 70)
    print(f"{'Parser':<20} {'Attempts':>10} {'Success':>10} {'Fail':>10} {'Rate':>10}")
    print("-" * 70)

    # Sort by success rate (descending)
    sorted_parsers = sorted(rates.items(), key=lambda x: x[1], reverse=True)

    for parser, rate in sorted_parsers:
        m = metrics[parser]
        if m["attempts"] > 0:
            print(
                f"{parser:<20} {m['attempts']:>10} {m['successes']:>10} "
                f"{m['failures']:>10} {format_percentage(rate):>10}"
            )

    print("-" * 70)

    # Calculate totals
    total_attempts = sum(m["attempts"] for m in metrics.values())
    total_successes = sum(m["successes"] for m in metrics.values())
    total_failures = sum(m["failures"] for m in metrics.values())
    total_rate = total_successes / total_attempts if total_attempts > 0 else 0

    print(
        f"{'TOTAL':<20} {total_attempts:>10} {total_successes:>10} "
        f"{total_failures:>10} {format_percentage(total_rate):>10}"
    )
    print("=" * 70)


def print_confidence_boost_info():
    """Print information about confidence boosts"""
    print("\n" + "=" * 70)
    print("CONFIDENCE BOOST REFERENCE")
    print("=" * 70)
    print(f"{'Parser':<20} {'Boost':<15} {'Notes'}")
    print("-" * 70)
    print(f"{'CTE (simple)':<20} {'+10%':<15} {'Standard CTE'}")
    print(f"{'CTE (recursive)':<20} {'+15%':<15} {'Recursive CTEs are complex'}")
    print(f"{'CTE (multiple)':<20} {'+15%':<15} {'3+ CTEs'}")
    print(f"{'Exception':<20} {'+5%':<15} {'Error handling present'}")
    print(f"{'Dynamic SQL':<20} {'-10%':<15} {'PENALTY (security concern)'}")
    print(f"{'Control Flow':<20} {'+8%':<15} {'FOR/WHILE loops'}")
    print(f"{'Window':<20} {'+8%':<15} {'Window functions'}")
    print(f"{'Aggregate':<20} {'+7%':<15} {'FILTER clauses'}")
    print(f"{'Cursor':<20} {'+8%':<15} {'Cursor operations'}")
    print("=" * 70)


def main():
    """Display metrics dashboard"""
    print("\n" + "=" * 70)
    print(" " * 20 + "PARSER METRICS DASHBOARD")
    print("=" * 70)

    print("\nNOTE: This is a standalone script.")
    print("To see real metrics, run reverse engineering operations first.")
    print("\nTo integrate with your code:")
    print("  from reverse_engineering.parser_coordinator import ParserCoordinator")
    print("  coordinator = ParserCoordinator()")
    print("  # ... perform parsing ...")
    print("  print(coordinator.get_metrics_summary())")

    # Example metrics (production-like data)
    example_metrics = {
        "cte": {"attempts": 1243, "successes": 1119, "failures": 124},
        "exception": {"attempts": 867, "successes": 738, "failures": 129},
        "dynamic_sql": {"attempts": 234, "successes": 187, "failures": 47},
        "control_flow": {"attempts": 456, "successes": 365, "failures": 91},
        "window": {"attempts": 678, "successes": 610, "failures": 68},
        "aggregate": {"attempts": 345, "successes": 293, "failures": 52},
        "cursor": {"attempts": 123, "successes": 105, "failures": 18},
    }

    example_rates = {
        parser: m["successes"] / m["attempts"] if m["attempts"] > 0 else 0
        for parser, m in example_metrics.items()
    }

    print("\n[EXAMPLE METRICS - Based on production data]")
    print_success_rates_table(example_rates, example_metrics)
    print_confidence_boost_info()

    print("\n" + "=" * 70)
    print("For real-time metrics, integrate ParserCoordinator into your workflow.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
