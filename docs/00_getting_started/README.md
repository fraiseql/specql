# Getting Started with SpecQL

**Welcome to SpecQL!** This section will get you productive in minutes, not hours.

## 🎬 See It In Action

### Installation
![Installation Demo](../demos/installation.gif)

### Quick Start
![Quick Start Demo](../demos/quickstart_demo.gif)

### Multi-Language Generation
![Multi-Language Demo](../demos/multi_language_demo.gif)

## 🎯 What You'll Learn

By the end of this section, you'll be able to:
- Install SpecQL and verify your setup
- Generate your first PostgreSQL schema from YAML
- Understand the core concepts (Trinity pattern, actions, etc.)
- Build a complete contact management system
- Deploy your generated code to a database

## 🚀 Quick Start (5 Minutes)

**Goal**: Generate your first PostgreSQL schema in under 5 minutes

If you're in a hurry, jump straight to the **[Quick Start Guide](QUICKSTART.md)** - it's designed for immediate productivity.

## 📋 Prerequisites

Before you begin, ensure you have:

- **Python 3.11+** - SpecQL is written in Python
- **PostgreSQL 14+** - Target database for generation
- **Basic YAML knowledge** - Configuration format
- **Command line access** - For running SpecQL commands

### Quick Setup Check

```bash
# Check Python version
python --version  # Should be 3.10 or higher

# Check PostgreSQL (if available locally)
psql --version    # Should be 14 or higher

# Check pip
pip --version
```

## 📚 Learning Path

### 1. Installation & Setup
**[Quick Start Guide](QUICKSTART.md)** - Install SpecQL and generate your first schema

### 2. Real-World Examples
**[CRM System Example](../../06_examples/CRM_SYSTEM_COMPLETE.md)** - Complete customer relationship management system

**[E-commerce Example](../../06_examples/ECOMMERCE_SYSTEM.md)** - Full online store with inventory and orders

### 3. Advanced Topics
**[YAML Reference](../../03_reference/yaml/complete_reference.md)** - Complete YAML syntax guide

**[CLI Reference](../../03_reference/cli/command_reference.md)** - All command-line options

## 💡 Key Concepts You'll Encounter

### Trinity Pattern
SpecQL automatically creates three identifiers for each entity:
- `pk_*` (INTEGER) - For database JOINs and performance
- `id` (UUID) - For APIs and external references
- `identifier` (TEXT) - For humans (optional custom format)

### Actions
Business logic defined in YAML that compiles to PL/pgSQL functions:
```yaml
actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified'
```

### Schemas
Organize entities by domain (crm, sales, inventory, etc.)

## 🎯 Success Criteria

After completing this section, you should be able to:

✅ Install and run SpecQL commands
✅ Write basic entity YAML definitions
✅ Generate PostgreSQL tables and functions
✅ Apply migrations to a database
✅ Understand generated GraphQL schemas
✅ Use generated TypeScript types

## 🆘 Need Help?

- **Stuck on installation?** Check the [Quick Start Guide](QUICKSTART.md)
- **YAML syntax issues?** See the [YAML Reference](../../03_reference/yaml/complete_reference.md)
- **Generation problems?** Check the [CLI Reference](../../03_reference/cli/command_reference.md)
- **Community support?** Open issues on [GitHub](https://github.com/fraiseql/specql/issues)

## 📈 What's Next?

Once you're comfortable with the basics:

1. **Tutorials** - Step-by-step guides for real applications
2. **Guides** - Deep dives into specific features
3. **Reference** - Complete YAML syntax and CLI options
4. **Examples** - Real-world implementations to study

---

**Ready to start?** Head to the [Quick Start Guide](QUICKSTART.md)!