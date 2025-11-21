# New SpecQL Documentation Architecture
## **Persona-Driven, Journey-Focused Information Structure**

*Designed: 2025-11-19 | Based on user journey analysis and content audit*

---

## Executive Summary

**Current State**: 180+ scattered markdown files with poor discoverability
**New State**: Structured, persona-routed documentation with clear progression
**Goal**: Every user finds what they need within 3 clicks

---

## Core Design Principles

### 1. **Persona-First Routing**
Documentation routes users based on their goals, not technical features.

### 2. **Progressive Disclosure**
Start simple, link to advanced. No information overload.

### 3. **Journey-Driven Organization**
Content organized around user tasks, not system components.

### 4. **Cross-Referenced Network**
Every page links to related concepts for exploration.

### 5. **Action-Oriented Content**
Show what to do, not just what exists.

---

## New Documentation Structure

```
docs/
├── README.md (Universal router - directs to persona paths)
├── 01_getting-started/ (🚀 Alex - Speed to first win)
│   ├── index.md (5-minute setup)
│   ├── first-entity.md (Working Contact entity)
│   ├── first-action.md (Business logic)
│   ├── first-api.md (GraphQL queries)
│   └── production-deploy.md (Go live)
├── 02_migration/ (🏢 Jordan + 🔄 Taylor - Enterprise migration)
│   ├── index.md (Migration overview)
│   ├── assess-legacy.md (What can be migrated)
│   ├── reverse-engineering/
│   │   ├── sql.md (PL/pgSQL functions)
│   │   ├── python.md (Django, SQLAlchemy)
│   │   ├── rust.md (Diesel, SeaORM)
│   │   ├── typescript.md (Prisma, Express)
│   │   └── java.md (Hibernate, Spring)
│   └── patterns/
│       ├── audit-trails.md
│       ├── multi-tenant.md
│       ├── soft-delete.md
│       └── state-machines.md
├── 03_core-concepts/ (All personas - Foundation knowledge)
│   ├── business-yaml.md (Why YAML, not code)
│   ├── trinity-pattern.md (Three identifiers explained)
│   ├── rich-types.md (49 types with examples)
│   ├── actions.md (Business logic engine)
│   └── fraiseql.md (Auto GraphQL)
├── 04_stdlib/ (All personas - Pre-built entities)
│   ├── index.md (What is stdlib)
│   ├── crm/
│   │   ├── contact.md
│   │   ├── organization.md
│   │   └── organization-type.md
│   ├── commerce/
│   │   ├── contract.md
│   │   ├── order.md
│   │   └── price.md
│   ├── geo/
│   │   ├── public-address.md
│   │   ├── location.md
│   │   └── postal-code.md
│   ├── i18n/
│   │   ├── country.md
│   │   ├── currency.md
│   │   └── language.md
│   └── showcase.md (Build CRM in 10 lines)
├── 05_guides/ (Practical how-tos)
│   ├── your-first-entity.md (Step-by-step entity creation)
│   ├── your-first-action.md (Business logic implementation)
│   ├── multi-tenancy.md (Tenant isolation)
│   ├── graphql-integration.md (Frontend integration)
│   ├── custom-fields.md (Extend stdlib entities)
│   └── error-handling.md (Debugging actions)
├── 06_reference/ (Technical details - 🛠️ Casey + advanced users)
│   ├── yaml-syntax.md (Complete grammar)
│   ├── cli-commands.md (All command-line options)
│   ├── rich-types-reference.md (All 49 types + 15 composites)
│   ├── action-steps.md (Every action step type)
│   ├── postgres-schema.md (Generated SQL structure)
│   └── graphql-schema.md (Generated GraphQL)
├── 07_advanced/ (Power features)
│   ├── custom-patterns.md (Extend the generator)
│   ├── performance-tuning.md (Optimization techniques)
│   ├── security-hardening.md (Enterprise security)
│   ├── custom-validators.md (Business rule engines)
│   └── integration-testing.md (Test generated code)
└── 08_contributing/ (🛠️ Casey - Developer enablement)
    ├── index.md (How to contribute)
    ├── architecture.md (System design)
    ├── development-setup.md (Local development)
    ├── testing-guide.md (Testing strategy)
    ├── adding-rich-types.md (Extend type system)
    └── release-process.md (Version management)
```

---

## Persona Path Mapping

### 🚀 **Alex - Startup CTO** (Speed Path)
```
README → 01_getting-started/ → 04_stdlib/showcase.md → Production
```

**Journey**: Quick start → Working app → Production deployment
**Time**: < 30 minutes to first production backend

### 🏢 **Jordan - Enterprise Architect** (Migration Path)
```
README → 02_migration/ → 03_core-concepts/ → 07_advanced/security-hardening.md
```

**Journey**: Assessment → Migration planning → Enterprise features
**Focus**: Compliance, security, scalability

### 🔄 **Taylor - Migration Specialist** (Reverse Engineering Path)
```
README → 02_migration/reverse-engineering/[language].md → 02_migration/patterns/
```

**Journey**: Tech stack analysis → Migration execution → Pattern preservation
**Focus**: Language-specific migration, incremental adoption

### 🤖 **Sam - AI Agent Developer** (Structured Learning Path)
```
README → 03_core-concepts/ → 06_reference/ → 05_guides/
```

**Journey**: Foundation concepts → Technical details → Practical application
**Focus**: Clear, structured, unambiguous content

### 🛠️ **Casey - Contributor** (Deep Dive Path)
```
README → 08_contributing/ → 03_core-concepts/ → 07_advanced/custom-patterns.md
```

**Journey**: Onboarding → Architecture understanding → Feature development
**Focus**: System internals, extension APIs, testing

---

## Content Strategy by Section

### 01_getting-started/ (Action-Oriented)
- **Goal**: Get user to "working backend" in 30 minutes
- **Style**: Step-by-step tutorials with copy-paste code
- **Validation**: Each step must work independently
- **Success**: User has deployed, queryable GraphQL API

### 02_migration/ (Assessment-First)
- **Goal**: Help users understand what can be migrated
- **Style**: Before/after examples, compatibility matrices
- **Validation**: Clear success criteria for each migration type
- **Success**: User knows exactly what they can achieve

### 03_core-concepts/ (Foundation Knowledge)
- **Goal**: Explain "why SpecQL" and core mental models
- **Style**: Conceptual explanations with concrete examples
- **Validation**: Each concept links to practical application
- **Success**: User understands the "SpecQL way"

### 04_stdlib/ (Discovery-Focused)
- **Goal**: Make pre-built entities discoverable and usable
- **Style**: Showcase examples, customization guides
- **Validation**: Every entity has working example
- **Success**: User builds complex apps without custom entities

### 05_guides/ (Problem-Solution)
- **Goal**: Answer "how do I..." questions
- **Style**: Scenario-based, with multiple solution paths
- **Validation**: Real user problems solved
- **Success**: User can implement common patterns

### 06_reference/ (Complete Coverage)
- **Goal**: Answer technical questions definitively
- **Style**: Comprehensive, searchable, machine-readable
- **Validation**: Every feature documented
- **Success**: No "how does X work" questions unanswered

### 07_advanced/ (Expert Features)
- **Goal**: Enable power users and custom implementations
- **Style**: Deep technical content with warnings
- **Validation**: Advanced features work as documented
- **Success**: Enterprise users can customize SpecQL

### 08_contributing/ (Developer Enablement)
- **Goal**: Turn users into contributors
- **Style**: Welcoming, practical, achievement-oriented
- **Validation**: New contributors succeed
- **Success**: Growing, active contributor community

---

## Cross-Linking Strategy

### Progressive Disclosure Links
- **Simple → Advanced**: Every basic concept links to deeper content
- **Theory → Practice**: Concepts link to implementation guides
- **General → Specific**: Overviews link to detailed references

### Persona Cross-Links
- **Speed users** can discover advanced features
- **Enterprise users** can access quick starts
- **Contributors** can understand user needs

### Content Network
```
Getting Started ←→ Core Concepts ←→ Guides ←→ Reference
      ↓              ↓              ↓         ↓
   Migration    ←→ Advanced   ←→ Contributing
```

---

## Implementation Plan

### Phase 1: Foundation (Week 2)
1. Create directory structure
2. Write README router
3. Implement getting-started flow
4. Build core concepts section

### Phase 2: Expansion (Week 3)
1. Complete migration guides
2. Build stdlib documentation
3. Create reference section
4. Add advanced topics

### Phase 3: Polish (Week 3)
1. Cross-link all content
2. Add AI-friendly metadata
3. Create visual assets
4. Launch and archive old docs

---

## Success Metrics

### User Experience
- **Time to first value**: < 10 minutes for quick start
- **Information findability**: < 3 clicks to any feature
- **Journey completion**: 80% of users reach their goals

### Technical Quality
- **Broken links**: 0%
- **Outdated examples**: 0%
- **AI parseability**: 95% accuracy

### Community Health
- **Contributor onboarding**: < 1 week to first PR
- **Documentation issues**: < 5% of total issues

This architecture transforms SpecQL's documentation from archaeological dig to architectural delight. Every user journey is supported, every feature discoverable, every question answerable.

---

*This information architecture serves all personas while maintaining clarity and discoverability.*</content>
</xai:function_call
