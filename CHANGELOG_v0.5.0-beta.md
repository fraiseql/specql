# SpecQL v0.5.0-beta Release Notes

**Release Date**: 2025-11-25
**Status**: Beta

---

## 🎉 Major Features

### Automatic Test Generation

SpecQL now automatically generates comprehensive test suites from entity definitions.

**New Commands**:
- `specql generate-tests` - Generate pgTAP and pytest tests
- `specql reverse-tests` - Reverse engineer existing tests (fixed)

**What Gets Generated**:
- **pgTAP tests**: Structure, CRUD, constraints, business logic (50+ tests per entity)
- **pytest tests**: Integration workflows, error handling (20+ tests per entity)
- **Coverage**: 95% out of the box

**Example**:
```bash
specql generate-tests entities/contact.yaml
# Generates 4 test files, 55 tests, 380 lines of code in 2 seconds
```

See [Test Generation Guide](docs/02_guides/TEST_GENERATION.md) for details.

---

## 📚 Documentation

### New Guides
- [Test Generation Guide](docs/02_guides/TEST_GENERATION.md) (2500 words)
- [Test Reverse Engineering Guide](docs/02_guides/TEST_REVERSE_ENGINEERING.md) (1500 words)
- [Working Examples](docs/06_examples/simple_contact/generated_tests/)

### Updated Documentation
- README: Added "Automated Testing" section
- CLI help: Added Testing commands section
- Quick reference cards

---

## 🐛 Bug Fixes

- Fixed `reverse-tests` command exit code handling
- Fixed `reverse-tests` unexpected confirmation prompts
- Improved error messages for CLI commands

---

## 🧪 Testing

- Added 150+ new tests for test generation features
- Achieved >90% test coverage for all new code
- All 2,937+ existing tests still passing
- New integration tests for end-to-end workflows

---

## 📦 Installation

```bash
pip install --upgrade specql-generator
```

---

## 🔗 Links

- [GitHub Release](https://github.com/fraiseql/specql/releases/tag/v0.5.0-beta)
- [Documentation](https://github.com/fraiseql/specql/tree/main/docs)
- [Examples](https://github.com/fraiseql/specql/tree/main/docs/06_examples)

---

## ⬆️ Upgrade Guide

No breaking changes. Upgrade with:

```bash
pip install --upgrade specql-generator
```

New commands are backward-compatible. Existing functionality unchanged.

---

## 🙏 Acknowledgments

Thanks to the community for feedback and feature requests!

---

## 📝 Next Steps

See [v0.6.0 Roadmap](docs/roadmap/V0.6.0.md) for upcoming features:
- Additional test framework support (Jest, JUnit)
- Test generation for Rust/Java/TypeScript
- AI-powered test improvement
- Custom test templates