# ParserCoordinator Design

## Current Architecture (Tightly Coupled)

```
ASTToSpecQLMapper
├── __init__: Creates 7 parser instances
├── _parse_begin_block: Calls parsers directly
├── Direct imports of all parsers
└── Parser logic mixed with mapping logic
```

**Problems**:
- ASTToSpecQLMapper has too many responsibilities
- Hard to test parser coordination independently
- Parser selection logic scattered across methods
- No centralized metrics or monitoring

## Target Architecture (Clean Separation)

```
ASTToSpecQLMapper
├── Uses ParserCoordinator (composition)
└── Focuses only on AST → SpecQL mapping

ParserCoordinator
├── Manages 7 specialized parsers
├── Decides which parsers to use (should_use_* methods)
├── Tracks parser metrics (attempts, successes, failures)
├── Provides parser results with metadata
└── Single responsibility: Coordinate specialized parsers
```

## Interface Design

```python
@dataclass
class ParserResult:
    """Result from a specialized parser"""
    steps: List[ActionStep]
    confidence_boost: float  # How much to boost confidence
    parser_used: str  # Which parser produced this
    metadata: Dict[str, Any]  # Parser-specific metadata
    success: bool

class ParserCoordinator:
    """Coordinates specialized SQL parsers"""

    def __init__(self):
        # Initialize all parsers
        self.cte_parser = CTEParser()
        self.exception_parser = ExceptionHandlerParser()
        # ... etc

        # Metrics tracking
        self.metrics = {
            'cte': {'attempts': 0, 'successes': 0, 'failures': 0},
            'exception': {'attempts': 0, 'successes': 0, 'failures': 0},
            # ... etc
        }

    # Parser selection methods
    def should_use_cte_parser(self, sql: str) -> bool
    def should_use_exception_parser(self, sql: str) -> bool
    # ... etc

    # Parser execution methods
    def parse_with_cte(self, sql: str) -> Optional[ParserResult]
    def parse_with_exception(self, sql: str) -> Optional[ParserResult]
    # ... etc

    # Coordination method
    def parse_with_best_parsers(self, sql: str) -> List[ParserResult]

    # Metrics methods
    def get_metrics(self) -> Dict[str, Any]
    def get_success_rates(self) -> Dict[str, float]
    def reset_metrics(self) -> None
```

## Benefits

1. **Single Responsibility**: ASTToSpecQLMapper focuses on mapping, ParserCoordinator on coordination
2. **Testability**: Can test parser coordination independently
3. **Observability**: Centralized metrics collection
4. **Maintainability**: Easy to add new parsers
5. **Flexibility**: Can swap coordination strategies
