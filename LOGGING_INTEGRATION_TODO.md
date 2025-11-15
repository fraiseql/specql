# Logging Framework - CLI Integration TODO

**Status**: ✅ Core logging framework cherry-picked from PR #12
**Commit**: 9f8bd07 - feat: add logging framework from PR #12
**Date**: 2025-11-15

---

## ✅ What's Already Done

- ✅ `src/utils/logger.py` - Complete logging framework (323 lines)
- ✅ `tests/utils/test_logger.py` - Comprehensive test suite (265 lines, 23 tests)
- ✅ All tests passing
- ✅ LogContext dataclass for structured logging
- ✅ Team-aware loggers (Team A-E)
- ✅ Colored terminal output
- ✅ Log level support (DEBUG, INFO, WARNING, ERROR)

---

## 🔧 What's Still Needed (Optional for Alpha)

### CLI Integration

The PR #12 also added CLI flags to `src/cli/generate.py`, but these weren't cherry-picked
to avoid merge conflicts. If you want to add them for alpha, here's what to do:

#### 1. Add CLI Flags

In `src/cli/generate.py`, add these options to the `@click.command()`:

```python
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging (DEBUG level)")
@click.option("--quiet", "-q", is_flag=True, help="Suppress all output except errors")
def entities(
    entity_files: tuple,
    # ... existing parameters ...
    verbose: bool,
    quiet: bool,
):
```

#### 2. Configure Logging at Start

At the beginning of the `entities()` function:

```python
from src.utils.logger import configure_logging, get_team_logger
import logging

# Configure logging based on verbosity flags
if quiet:
    configure_logging(level=logging.ERROR)
elif verbose:
    configure_logging(level=logging.DEBUG, verbose=True)
else:
    configure_logging(level=logging.INFO)

logger = get_team_logger("Team E", __name__)
logger.info(f"Starting generation for {len(entity_files)} entity file(s)")
```

#### 3. Add Logging Statements

Throughout the generation workflow:

```python
logger.debug(f"Output directory: {output_dir}")
logger.debug(f"Foundation only: {foundation_only}, Include TV: {include_tv}")
logger.info(f"Generated {len(result.migrations)} migration file(s)")
logger.error(f"Generation failed: {error}", exc_info=True)
```

---

## 📋 Integration Points (If You Want Logging)

### Core Components (PR #12 had these, optional to add)

1. **src/core/specql_parser.py** (Team A - Parser)
   ```python
   from src.utils.logger import get_team_logger, LogContext

   self.logger = get_team_logger("Team A", __name__)
   self.logger.debug("Starting SpecQL YAML parsing")
   ```

2. **src/generators/schema_orchestrator.py** (Team B - Schema Generator)
   ```python
   logger = get_team_logger("Team B", __name__, context)
   logger.info("Generating schema components")
   ```

3. **src/generators/actions/action_orchestrator.py** (Team C - Action Compiler)
   ```python
   logger = get_team_logger("Team C", __name__, context)
   logger.debug(f"Compiling action: {action_name}")
   ```

4. **src/generators/fraiseql/mutation_annotator.py** (Team D - FraiseQL)
   ```python
   logger = get_team_logger("Team D", __name__, context)
   logger.info("Generating FraiseQL metadata")
   ```

---

## 🎯 Recommendation for Alpha Release

### Option A: Skip CLI Integration (RECOMMENDED)
- Core logging framework is available for developers
- No user-facing CLI changes
- Lower risk for alpha
- Can add CLI flags in v0.4.1-alpha or v0.5.0-beta

### Option B: Add CLI Flags Only
- Just add `--verbose` and `--quiet` flags to CLI
- Don't add logging to core components yet
- Simple, low-risk enhancement
- ~20 lines of code in `src/cli/generate.py`

### Option C: Full Integration
- Add logging throughout codebase
- Most helpful for debugging alpha issues
- Higher risk (more code changes)
- ~100 lines of code across multiple files

---

## 📝 Usage Examples (Once Integrated)

### Without CLI Integration (Current State)
Developers can use logging in their code:

```python
from src.utils.logger import get_logger, LogContext

context = LogContext(entity_name="Contact", operation="parse")
logger = get_logger(__name__, context)
logger.info("Processing entity")
```

### With CLI Integration (If Added)
Users can control logging from command line:

```bash
# Normal output (INFO level)
specql generate entities/*.yaml

# Verbose debugging (DEBUG level)
specql generate entities/*.yaml --verbose

# Quiet mode (ERROR only)
specql generate entities/*.yaml --quiet
```

---

## ✅ Decision for v0.4.0-alpha

**Current Status**: Logging framework available but not integrated

**For alpha release**:
- [ ] Keep as-is (framework available, not used) - LOW RISK
- [ ] Add CLI flags only - MEDIUM VALUE, LOW RISK
- [ ] Full integration - HIGH VALUE, MEDIUM RISK

**Recommendation**: Keep as-is for alpha, add CLI integration post-alpha based on user feedback.

---

**Reference**: Original PR #12 with full integration:
https://github.com/fraiseql/specql/pull/12

**Cherry-picked Files**:
- src/utils/logger.py
- tests/utils/test_logger.py

**Skipped Files** (to avoid conflicts):
- src/cli/generate.py (CLI flags)
- src/core/specql_parser.py (Team A logging)
- src/generators/schema_orchestrator.py (Team B logging)
- src/generators/actions/action_orchestrator.py (Team C logging)
- src/generators/fraiseql/mutation_annotator.py (Team D logging)

---

**Date**: 2025-11-15
**Status**: Framework available, integration optional
