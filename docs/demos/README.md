# SpecQL Demo Assets

This directory contains asciinema recordings and GIF animations demonstrating SpecQL features.

## Available Demos

### Installation Demo
- **File**: `installation.gif` (88KB)
- **Duration**: ~9 frames
- **Shows**: SpecQL installation process
- **Used in**: Main README, Getting Started guide

### Quick Start Demo
- **File**: `quickstart_demo.gif` (196KB)
- **Duration**: ~8 frames
- **Shows**: Quick start workflow from YAML to code generation
- **Used in**: Main README, Getting Started guide, Quickstart tutorial

### Multi-Language Demo
- **File**: `multi_language_demo.gif` (52KB)
- **Duration**: ~12 frames
- **Shows**: Generating code for multiple languages (PostgreSQL, Java, Rust, TypeScript)
- **Used in**: Main README, Getting Started guide

### Reverse Engineering Demo
- **File**: `reverse_engineering.gif` (42KB)
- **Duration**: ~6 frames
- **Shows**: Converting existing code back to SpecQL YAML
- **Used in**: Main README

## Source Files

Original asciinema recordings (`.cast` files) are also included for re-generation:
- `installation.cast`
- `quickstart_demo.cast`
- `multi_language_demo.cast`
- `reverse_engineering.cast`

## Regenerating GIFs

To regenerate GIFs from cast files:

```bash
# Install agg if needed
curl -L -o agg https://github.com/asciinema/agg/releases/download/v1.7.0/agg-x86_64-unknown-linux-gnu
chmod +x agg

# Convert cast to GIF
./agg <input.cast> <output.gif>

# Example:
./agg installation.cast installation.gif
```

## Recording New Demos

To record a new demo:

```bash
# Record with asciinema
asciinema rec demo_name.cast --title "Demo Title" --idle-time-limit 2 -c ./demo_script.sh

# Convert to GIF
./agg demo_name.cast demo_name.gif
```

## Demo Scripts

Demo scripts (`.sh` files) contain the commands executed during recording:

### Test Generation & Analysis Demos
- `test_generation_script.sh` - Test generation from entity YAML
- `test_execution_script.sh` - Running generated tests
- `coverage_analysis_script.sh` - Coverage analysis and gap detection
- `installation_demo.sh` - Installation walkthrough

### Running Interactive Demos

The test-related demo scripts can be run interactively:

```bash
# Test Generation Demo (~30 seconds)
./docs/demos/test_generation_script.sh

# Test Execution Demo (~45 seconds)
./docs/demos/test_execution_script.sh

# Coverage Analysis Demo (~30 seconds)
./docs/demos/coverage_analysis_script.sh
```

These demos showcase the complete workflow from entity definition to test execution and coverage analysis.

## Usage in Documentation

GIFs are referenced in documentation using relative paths:

```markdown
![Installation Demo](../demos/installation.gif)
```

**Current locations**:
- Main `README.md` - All 4 demos
- `docs/00_getting_started/README.md` - Installation, Quick Start, Multi-Language
- `docs/00_getting_started/QUICKSTART.md` - Quick Start demo

---

**Note**: Keep GIF sizes reasonable (<200KB each) for fast page loads. Use `--idle-time-limit 2` to reduce file size by cutting long pauses.
