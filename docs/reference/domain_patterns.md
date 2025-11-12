# Domain Patterns Reference

This document describes the 15 domain patterns in SpecQL - reusable business logic templates that implement common enterprise patterns. Each pattern provides a complete, tested implementation that can be instantiated with minimal configuration.

## Overview

Domain patterns are higher-level abstractions built on top of primitive actions. They provide:

- **Complete Solutions**: Ready-to-use business logic implementations
- **Best Practices**: Industry-standard patterns with proper error handling
- **Multi-Language**: Generate PostgreSQL, Django, and SQLAlchemy code
- **Composable**: Can be combined with other patterns
- **Configurable**: Customize behavior through parameters

## Available Patterns

### 1. State Machine Pattern
**Category**: Workflow Management

Implements state machines with transitions, guards, and audit trails.

**Use Cases**:
- Order processing (draft → confirmed → shipped → delivered)
- Document approval workflows
- Lead qualification (prospect → qualified → customer)

**Configuration**:
```yaml
patterns:
  - state_machine:
      states: [draft, pending_review, approved, rejected]
      initial_state: draft
      transitions:
        draft_to_pending_review:
          from: draft
          to: pending_review
        pending_review_to_approved:
          from: pending_review
          to: approved
          guards:
            - condition: "user_has_permission('approve')"
              error: "Insufficient permissions"
```

**Generated Features**:
- State field with enum constraint
- State transition functions
- State history table
- Transition validation
- Audit trail

### 2. Audit Trail Pattern
**Category**: Compliance & Tracking

Tracks all changes to entity data with full audit history.

**Use Cases**:
- Financial records auditing
- Medical data compliance
- Regulatory reporting
- Change tracking for legal requirements

**Configuration**:
```yaml
patterns:
  - audit_trail:
      track_versions: true
      track_user: true
      track_ip: false
      retention_days: 2555  # 7 years
```

**Generated Features**:
- Audit table for all changes
- Version numbering
- User tracking
- Timestamp tracking
- Change diff storage

### 3. Soft Delete Pattern
**Category**: Data Management

Implements logical deletion instead of physical deletion.

**Use Cases**:
- Preserving data integrity
- Recovery from accidental deletions
- Maintaining referential integrity
- Audit compliance

**Configuration**:
```yaml
patterns:
  - soft_delete:
      cascade: true
      retention_policy: "mark_deleted"
      allow_hard_delete: false
```

**Generated Features**:
- `deleted_at` timestamp field
- `deleted_by` user field
- Modified queries to exclude deleted records
- Soft delete functions
- Optional hard delete capability

### 4. Validation Chain Pattern
**Category**: Data Quality

Chains multiple validation rules with configurable error handling.

**Use Cases**:
- Complex business rule validation
- Multi-step data validation
- Conditional validation logic
- Custom error messages

**Configuration**:
```yaml
patterns:
  - validation_chain:
      rules:
        - name: email_format
          condition: "email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z]{2,}$'"
          message: "Invalid email format"
        - name: unique_email
          condition: "NOT EXISTS (SELECT 1 FROM contacts WHERE email = $email AND id != $id)"
          message: "Email already exists"
      stop_on_first_error: false
```

**Generated Features**:
- Configurable validation rules
- Custom error messages
- Validation chaining
- Error collection options

### 5. Approval Workflow Pattern
**Category**: Business Process

Implements multi-step approval processes with escalation.

**Use Cases**:
- Purchase order approvals
- Contract approvals
- Budget approvals
- Document reviews

**Configuration**:
```yaml
patterns:
  - approval_workflow:
      levels:
        - name: manager
          condition: "amount <= 1000"
          timeout_days: 3
        - name: director
          condition: "amount <= 10000"
          timeout_days: 7
        - name: executive
          condition: "amount > 10000"
          timeout_days: 14
      escalation:
        enabled: true
        after_days: 2
        notify: ["supervisor", "requester"]
```

**Generated Features**:
- Approval level configuration
- Automatic escalation
- Approval tracking
- Notification system
- Timeout handling

### 6. Hierarchy Navigation Pattern
**Category**: Organizational Structure

Manages hierarchical relationships with efficient navigation.

**Use Cases**:
- Organizational charts
- Product categories
- Geographic hierarchies
- Project structures

**Configuration**:
```yaml
patterns:
  - hierarchy_navigation:
      max_depth: 5
      allow_circular_refs: false
      path_materialization: true
      closure_table: true
```

**Generated Features**:
- Parent-child relationships
- Path materialization
- Closure table for fast queries
- Hierarchy validation
- Navigation functions

### 7. Computed Fields Pattern
**Category**: Data Derivation

Automatically maintains computed/derived field values.

**Use Cases**:
- Calculated totals
- Status rollups
- Aggregated metrics
- Derived attributes

**Configuration**:
```yaml
patterns:
  - computed_fields:
      fields:
        - name: total_amount
          expression: "SELECT SUM(amount) FROM order_items WHERE order_id = id"
          update_triggers: ["order_items.amount"]
        - name: status_summary
          expression: "CASE WHEN completed_items = total_items THEN 'complete' ELSE 'pending' END"
          dependencies: ["completed_items", "total_items"]
```

**Generated Features**:
- Automatic field updates
- Trigger-based recalculation
- Dependency tracking
- Performance optimization

### 8. Search Optimization Pattern
**Category**: Performance

Implements full-text search and optimized querying.

**Use Cases**:
- Product catalogs
- Document libraries
- User directories
- Content management

**Configuration**:
```yaml
patterns:
  - search_optimization:
      full_text_fields: ["title", "description", "content"]
      weighted_search: true
      fuzzy_matching: true
      autocomplete: true
      facets: ["category", "status", "priority"]
```

**Generated Features**:
- Full-text search indexes
- Weighted search results
- Fuzzy matching
- Autocomplete functionality
- Faceted search

### 9. Internationalization Pattern
**Category**: Globalization

Supports multiple languages and locales.

**Use Cases**:
- Multi-language applications
- Localized content
- Regional formatting
- Cultural adaptations

**Configuration**:
```yaml
patterns:
  - internationalization:
      supported_languages: ["en", "es", "fr", "de"]
      default_language: "en"
      fallback_strategy: "default_language"
      translatable_fields: ["name", "description", "content"]
```

**Generated Features**:
- Translation tables
- Language fallback logic
- Localized queries
- Translation management

### 10. File Attachment Pattern
**Category**: Document Management

Manages file attachments with metadata and access control.

**Use Cases**:
- Document management
- Image galleries
- File sharing
- Digital asset management

**Configuration**:
```yaml
patterns:
  - file_attachment:
      max_file_size: "10MB"
      allowed_types: ["pdf", "doc", "docx", "jpg", "png"]
      storage_strategy: "s3"
      access_control: true
      versioning: true
```

**Generated Features**:
- File metadata tracking
- Access control
- Version management
- Storage abstraction
- Upload/download functions

### 11. Tagging Pattern
**Category**: Content Organization

Implements flexible tagging and categorization.

**Use Cases**:
- Content categorization
- Skill tagging
- Product tagging
- Knowledge base organization

**Configuration**:
```yaml
patterns:
  - tagging:
      tag_types: ["category", "skill", "priority"]
      allow_multiple: true
      auto_complete: true
      tag_validation: true
      hierarchical_tags: false
```

**Generated Features**:
- Tag tables and relationships
- Tag validation
- Auto-completion
- Tag statistics
- Bulk tagging operations

### 12. Commenting Pattern
**Category**: Collaboration

Enables threaded comments and discussions.

**Use Cases**:
- Issue tracking
- Document collaboration
- Social features
- Review systems

**Configuration**:
```yaml
patterns:
  - commenting:
      threaded: true
      max_depth: 5
      moderation: true
      notifications: true
      rich_text: true
```

**Generated Features**:
- Comment threads
- Moderation system
- Notification system
- Rich text support
- Comment management

### 13. Notification Pattern
**Category**: Communication

Manages notifications and alerts.

**Use Cases**:
- System alerts
- User notifications
- Email campaigns
- Push notifications

**Configuration**:
```yaml
patterns:
  - notification:
      channels: ["email", "sms", "push", "in_app"]
      templates: true
      scheduling: true
      preferences: true
      delivery_tracking: true
```

**Generated Features**:
- Multi-channel notifications
- Template system
- Delivery tracking
- User preferences
- Scheduling system

### 14. Scheduling Pattern
**Category**: Time Management

Handles time-based operations and scheduling.

**Use Cases**:
- Calendar systems
- Appointment booking
- Task scheduling
- Event management

**Configuration**:
```yaml
patterns:
  - scheduling:
      recurring_events: true
      time_zones: true
      availability: true
      conflicts: true
      reminders: true
```

**Generated Features**:
- Event scheduling
- Recurrence patterns
- Time zone handling
- Conflict detection
- Reminder system

### 15. Rate Limiting Pattern
**Category**: System Protection

Implements rate limiting and throttling.

**Use Cases**:
- API protection
- Resource usage control
- Spam prevention
- Fair usage policies

**Configuration**:
```yaml
patterns:
  - rate_limiting:
      limits:
        - scope: "user"
          window: "1 hour"
          max_requests: 1000
        - scope: "ip"
          window: "1 minute"
          max_requests: 60
      sliding_window: true
      burst_allowance: true
```

**Generated Features**:
- Rate limit tracking
- Sliding window algorithm
- Burst handling
- Limit enforcement
- Analytics and reporting

## Pattern Composition

Patterns can be combined for complex functionality:

```yaml
entity: Order
patterns:
  - state_machine:
      states: [draft, confirmed, shipped, delivered, cancelled]
  - audit_trail:
      track_versions: true
  - soft_delete
  - approval_workflow:
      levels:
        - name: manager
          condition: "total > 1000"
  - computed_fields:
      fields:
        - name: total_amount
          expression: "SELECT SUM(amount * quantity) FROM order_items WHERE order_id = id"
  - notification:
      channels: ["email"]
      templates: true
```

## Instantiation

Patterns are instantiated automatically when generating code:

```bash
# Generate entity with patterns
specql generate order.yaml --target postgresql --output order.sql

# The generated code includes all pattern implementations
```

## Customization

Each pattern can be customized through parameters:

```yaml
patterns:
  - state_machine:
      states: [draft, published, archived]
      initial_state: draft
      # Custom transition logic
      custom_transitions:
        - name: publish
          from: draft
          to: published
          validation: "content IS NOT NULL"
```

## Multi-Language Support

All patterns generate code for:

- **PostgreSQL**: Optimized PL/pgSQL functions
- **Django**: Python model methods and managers
- **SQLAlchemy**: Declarative model extensions

## Best Practices

1. **Start Simple**: Use basic patterns first, add complexity as needed
2. **Combine Wisely**: Choose compatible patterns that work well together
3. **Configure Properly**: Set appropriate parameters for your use case
4. **Test Thoroughly**: Each pattern combination should be tested
5. **Monitor Performance**: Some patterns have performance implications

## Related Documentation

- [Primitives Reference](primitives.md) - Low-level building blocks
- [Entity Templates](entity_templates.md) - Pre-configured entity combinations
- [CLI Commands](cli_commands.md) - Command-line interface
- [Migration Guide](../../guides/migration_guide.md) - Converting existing code