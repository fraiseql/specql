# Getting Started with SpecQL

**Welcome to SpecQL!** This section will get you productive in minutes, not hours.

## 🎯 What You'll Learn

By the end of this section, you'll be able to:
- Install SpecQL and verify your setup
- Generate your first PostgreSQL schema from YAML
- Understand the core concepts (Trinity pattern, actions, etc.)
- Build a complete contact management system
- Deploy your generated code to a database

## 🚀 Quick Start (5 Minutes)

**Goal**: Generate your first PostgreSQL schema in under 5 minutes

If you're in a hurry, jump straight to the **[Quick Start Guide](quickstart.md)** - it's designed for immediate productivity.

## 📋 Prerequisites

Before you begin, ensure you have:

- **Python 3.10+** - SpecQL is written in Python
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
**[Installation Guide](installation.md)** - Install SpecQL and verify your environment

### 2. Your First Generation
**[Quick Start](quickstart.md)** - Generate your first schema from YAML

### 3. Core Concepts
**[Core Concepts](core_concepts.md)** - Understand Trinity pattern, schemas, and actions

### 4. Complete Project
**[First Project](first_project.md)** - Build a contact management system

### 5. Next Steps
**[FAQ](faq.md)** - Common questions and troubleshooting

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

- **Stuck on installation?** Check the [Installation Guide](installation.md)
- **YAML syntax issues?** See the [Core Concepts](core_concepts.md)
- **Generation problems?** Review the [FAQ](faq.md)
- **Community support?** Join our Discord or GitHub Discussions

## 📈 What's Next?

Once you're comfortable with the basics:

1. **Tutorials** - Step-by-step guides for real applications
2. **Guides** - Deep dives into specific features
3. **Reference** - Complete YAML syntax and CLI options
4. **Examples** - Real-world implementations to study

---

**Ready to start?** Head to the [Quick Start Guide](quickstart.md)!