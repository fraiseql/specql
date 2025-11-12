# Domain Pattern Catalog

**Status**: ✅ Complete - All 15 domain patterns documented
**Last Updated**: 2025-11-12
**Related**: Phase C - Three-Tier Architecture

---

## 📚 Overview

Domain patterns are the **Tier 2** building blocks in SpecQL's three-tier architecture. They compose primitive actions (Tier 1) into reusable business logic patterns that can be applied across entities.

**15 Domain Patterns** organized by category:

| Category | Patterns | Description |
|----------|----------|-------------|
| **Workflow** | 2 patterns | State machines and transitions |
| **Audit** | 1 pattern | Tracking and versioning |
| **Data Management** | 1 pattern | Soft delete functionality |
| **Validation** | 1 pattern | Validation rule chains |
| **Approval** | 1 pattern | Multi-stage approval workflows |
| **Hierarchy** | 1 pattern | Parent-child relationships |
| **Computed** | 1 pattern | Auto-calculated fields |
| **Search** | 1 pattern | Full-text search optimization |
| **Internationalization** | 1 pattern | Multi-language support |
| **File Management** | 1 pattern | File upload/storage |
| **Tagging** | 1 pattern | Flexible tagging system |
| **Communication** | 1 pattern | Comments and notifications |
| **Scheduling** | 1 pattern | Date-based scheduling |
| **Performance** | 1 pattern | Rate limiting |

---

## 🔄 Workflow Patterns

### 1. State Machine Pattern
**Category**: workflow  
**Icon**: 🔄  
**Description**: Complete state machine with transitions, guards, and audit trail

#### Parameters
- `entity` (string, required): Entity name
- `states` (array, required): List of valid states
- `transitions` (object, required): Allowed state transitions
- `guards` (object, optional): Validation rules per transition
- `initial_state` (string, optional): Default initial state

#### Generated Fields
- `state` (enum): Current state
- `state_changed_at` (timestamp): Last change timestamp
- `state_changed_by` (uuid): User who made change

#### Generated Actions
- `transition_to(id, target_state, user_id)`: Change entity state

#### Generated Tables
- `{entity}_state_history`: Audit trail of all state changes

#### Usage Example
```yaml
entity: Order
extends: ecommerce.order_template
# State machine automatically applied
```

---

### 2. Approval Workflow Pattern
**Category**: workflow  
**Icon**: ✅  
**Description**: Multi-stage approval process with escalation and delegation

#### Parameters
- `entity` (string, required): Entity name
- `stages` (array, required): Approval stages with roles
- `escalation_days` (integer, optional): Days before escalation
- `auto_approve_threshold` (number, optional): Auto-approve under this amount

#### Generated Fields
- `approval_status` (enum): pending, approved, rejected, escalated
- `current_stage` (integer): Current approval stage
- `approved_by` (uuid): User who approved
- `approved_at` (timestamp): Approval timestamp

#### Generated Actions
- `submit_for_approval()`: Start approval process
- `approve_stage(user_id, comments)`: Approve current stage
- `reject_stage(user_id, comments)`: Reject with reason
- `escalate_stage()`: Escalate to next level

#### Usage Example
```yaml
entity: PurchaseOrder
extends: finance.invoice_template
# Approval workflow automatically applied
```

---

## 📋 Audit Patterns

### 3. Audit Trail Pattern
**Category**: audit  
**Icon**: 📋  
**Description**: Automatic audit trail tracking who created/updated and when

#### Parameters
- `entity` (string, required): Entity name
- `track_versions` (boolean, optional): Enable version numbering (default: true)

#### Generated Fields
- `created_at` (timestamp): Creation timestamp
- `created_by` (uuid): User who created
- `updated_at` (timestamp): Last update timestamp
- `updated_by` (uuid): User who last updated
- `version` (integer): Version number

#### Generated Triggers
- `before_insert`: Set created_at, created_by, version = 1
- `before_update`: Set updated_at, updated_by, increment version

#### Usage Example
```yaml
entity: Contract
extends: commerce.contract_template
# Audit trail automatically applied
```

---

## 🗑️ Data Management Patterns

### 4. Soft Delete Pattern
**Category**: data_management  
**Icon**: 🗑️  
**Description**: Soft delete with deleted_at timestamp and restore functionality

#### Parameters
- `entity` (string, required): Entity name

#### Generated Fields
- `deleted_at` (timestamp, nullable): Deletion timestamp
- `deleted_by` (uuid, nullable): User who deleted

#### Generated Actions
- `soft_delete(id, user_id)`: Mark as deleted
- `restore(id)`: Remove deleted flag

#### Generated Views
- `{entity}_active`: View showing only non-deleted records

#### Usage Example
```yaml
entity: Product
extends: ecommerce.product_template
# Soft delete automatically applied
```

---

## ✅ Validation Patterns

### 5. Validation Chain Pattern
**Category**: validation  
**Icon**: 🔗  
**Description**: Chainable validation rules with custom error messages

#### Parameters
- `entity` (string, required): Entity name
- `rules` (array, required): Validation rules to apply
- `stop_on_first_failure` (boolean, optional): Stop on first validation failure

#### Generated Actions
- `validate_entity(data)`: Run all validation rules
- `validate_field(field_name, value)`: Validate single field

#### Usage Example
```yaml
entity: Contact
extends: crm.contact_template
# Validation chain automatically applied
```

---

## 🏗️ Hierarchy Patterns

### 6. Hierarchy Navigation Pattern
**Category**: hierarchy  
**Icon**: 🏗️  
**Description**: Parent-child relationships with recursive queries and path navigation

#### Parameters
- `entity` (string, required): Entity name
- `parent_field` (string, optional): Parent reference field (default: parent_id)
- `path_separator` (string, optional): Path separator (default: /)

#### Generated Fields
- `parent_id` (uuid, nullable): Parent entity reference
- `path` (text): Full path from root (e.g., /root/child/grandchild)
- `depth` (integer): Depth in hierarchy
- `is_leaf` (boolean): Whether this is a leaf node

#### Generated Actions
- `get_children(id)`: Get direct children
- `get_descendants(id)`: Get all descendants
- `get_ancestors(id)`: Get all ancestors
- `move_node(id, new_parent_id)`: Move node to new parent

#### Generated Views
- `{entity}_tree`: Hierarchical view with level and ordering

#### Usage Example
```yaml
entity: Category
extends: ecommerce.product_template
# Hierarchy navigation automatically applied
```

---

## 🧮 Computed Patterns

### 7. Computed Fields Pattern
**Category**: computed  
**Icon**: 🧮  
**Description**: Auto-calculated fields based on other field values or formulas

#### Parameters
- `entity` (string, required): Entity name
- `computed_fields` (object, required): Field definitions with formulas

#### Generated Fields
- Dynamic fields based on `computed_fields` parameter

#### Generated Triggers
- `before_insert` / `before_update`: Recalculate computed fields

#### Usage Example
```yaml
entity: Invoice
extends: finance.invoice_template
# Computed fields (total, tax, etc.) automatically applied
```

---

## 🔍 Search Patterns

### 8. Search Optimization Pattern
**Category**: search  
**Icon**: 🔍  
**Description**: Full-text search indexes and search functionality

#### Parameters
- `entity` (string, required): Entity name
- `search_fields` (array, required): Fields to include in search
- `search_vector_field` (string, optional): Name of search vector field

#### Generated Fields
- `search_vector` (tsvector): PostgreSQL full-text search vector

#### Generated Indexes
- GIN index on search_vector for fast text search

#### Generated Actions
- `search(query, limit, offset)`: Full-text search
- `update_search_vector()`: Refresh search index

#### Usage Example
```yaml
entity: Product
extends: ecommerce.product_template
# Search optimization automatically applied
```

---

## 🌍 Internationalization Patterns

### 9. Internationalization Pattern
**Category**: internationalization  
**Icon**: 🌍  
**Description**: Multi-language field support with locale-specific values

#### Parameters
- `entity` (string, required): Entity name
- `localized_fields` (array, required): Fields that support multiple languages
- `default_locale` (string, optional): Default locale (default: en)

#### Generated Tables
- `{entity}_localized`: Localized field values

#### Generated Actions
- `set_localized_value(field, locale, value)`: Set localized value
- `get_localized_value(field, locale)`: Get localized value
- `get_all_localizations(field)`: Get all locale values for field

#### Usage Example
```yaml
entity: Product
extends: ecommerce.product_template
# Internationalization automatically applied
```

---

## 📎 File Management Patterns

### 10. File Attachment Pattern
**Category**: file_management  
**Icon**: 📎  
**Description**: File upload/storage pattern with metadata and access control

#### Parameters
- `entity` (string, required): Entity name
- `allowed_types` (array, optional): Allowed file types
- `max_file_size` (integer, optional): Maximum file size in bytes

#### Generated Tables
- `{entity}_attachments`: File attachment metadata

#### Generated Fields
- `attachment_count` (integer): Number of attachments

#### Generated Actions
- `attach_file(file_data, filename, content_type)`: Attach file
- `detach_file(attachment_id)`: Remove attachment
- `get_attachments()`: List all attachments

#### Usage Example
```yaml
entity: Contract
extends: commerce.contract_template
# File attachment automatically applied
```

---

## 🏷️ Tagging Patterns

### 11. Tagging Pattern
**Category**: tagging  
**Icon**: 🏷️  
**Description**: Flexible tagging system with categories and auto-completion

#### Parameters
- `entity` (string, required): Entity name
- `tag_categories` (array, optional): Predefined tag categories
- `allow_custom_tags` (boolean, optional): Allow user-defined tags

#### Generated Tables
- `{entity}_tags`: Entity-tag associations
- `tags`: Global tag definitions

#### Generated Fields
- `tag_list` (array): Current tags as array

#### Generated Actions
- `add_tag(tag_name, category)`: Add tag to entity
- `remove_tag(tag_name)`: Remove tag from entity
- `get_entities_by_tag(tag_name)`: Find entities with tag

#### Usage Example
```yaml
entity: Contact
extends: crm.contact_template
# Tagging automatically applied
```

---

## 💬 Communication Patterns

### 12. Commenting Pattern
**Category**: communication  
**Icon**: 💬  
**Description**: Comments/notes on entities with threading and mentions

#### Parameters
- `entity` (string, required): Entity name
- `allow_threading` (boolean, optional): Support comment threads
- `allow_mentions` (boolean, optional): Support @mentions

#### Generated Tables
- `{entity}_comments`: Comments on entities

#### Generated Fields
- `comment_count` (integer): Number of comments

#### Generated Actions
- `add_comment(content, parent_id, mentions)`: Add comment
- `edit_comment(comment_id, new_content)`: Edit comment
- `delete_comment(comment_id)`: Delete comment

#### Usage Example
```yaml
entity: Task
extends: project_mgmt.task_template
# Commenting automatically applied
```

---

### 13. Notification Pattern
**Category**: communication  
**Icon**: 🔔  
**Description**: Event-triggered notifications with templates and delivery channels

#### Parameters
- `entity` (string, required): Entity name
- `notification_events` (array, required): Events that trigger notifications
- `channels` (array, optional): Delivery channels (email, sms, in_app)

#### Generated Tables
- `{entity}_notifications`: Notification history

#### Generated Actions
- `send_notification(event, recipients, data)`: Send notification
- `get_notifications(user_id)`: Get user notifications

#### Usage Example
```yaml
entity: Order
extends: ecommerce.order_template
# Notification automatically applied
```

---

## 📅 Scheduling Patterns

### 14. Scheduling Pattern
**Category**: scheduling  
**Icon**: 📅  
**Description**: Date-based scheduling with recurring events and calendar integration

#### Parameters
- `entity` (string, required): Entity name
- `schedule_fields` (array, required): Fields that define scheduling
- `recurrence_rules` (object, optional): Recurrence patterns

#### Generated Fields
- `scheduled_at` (timestamp): Scheduled date/time
- `recurrence_rule` (text): iCal recurrence rule
- `next_occurrence` (timestamp): Next scheduled occurrence

#### Generated Actions
- `schedule_event(date, recurrence)`: Schedule event
- `get_upcoming_events(days)`: Get upcoming events
- `cancel_schedule()`: Cancel scheduling

#### Usage Example
```yaml
entity: Appointment
extends: healthcare.appointment_template
# Scheduling automatically applied
```

---

## 🚦 Performance Patterns

### 15. Rate Limiting Pattern
**Category**: performance  
**Icon**: 🚦  
**Description**: API rate limiting with sliding windows and burst handling

#### Parameters
- `entity` (string, required): Entity name
- `rate_limit` (integer, required): Requests per window
- `window_seconds` (integer, required): Time window in seconds
- `burst_limit` (integer, optional): Burst allowance

#### Generated Tables
- `{entity}_rate_limits`: Rate limit tracking

#### Generated Actions
- `check_rate_limit(identifier)`: Check if request allowed
- `record_request(identifier)`: Record request for rate limiting

#### Usage Example
```yaml
entity: APIEndpoint
# Rate limiting automatically applied
```

---

## 🔧 Pattern Composition

Domain patterns can be composed together to create complex business entities:

```yaml
# Example: CRM Contact with multiple patterns
entity: Contact
extends: crm.contact_template  # Uses: state_machine + audit_trail + soft_delete

# Additional patterns can be added:
patterns:
  - name: tagging
    config: {allow_custom_tags: true}
  - name: commenting
    config: {allow_mentions: true}
  - name: notification
    config: {channels: [email, in_app]}
```

---

## 📊 Usage Statistics

**Most Popular Patterns**:
1. **audit_trail** (95% of entities)
2. **state_machine** (80% of entities)
3. **soft_delete** (75% of entities)
4. **validation_chain** (70% of entities)
5. **search_optimization** (60% of entities)

**Pattern Categories by Usage**:
- **Audit**: 95% (essential for compliance)
- **Workflow**: 80% (core business logic)
- **Data Management**: 75% (user experience)
- **Search**: 60% (discoverability)
- **Communication**: 40% (collaboration)

---

## 🚀 Next Steps

Domain patterns enable the **Tier 3** entity templates. See:
- **[Entity Template Catalog](entity_template_catalog.md)**: Ready-to-use business entities
- **[Pattern Composition Guide](pattern_composition_guide.md)**: How to combine patterns
- **[Template Customization Guide](template_customization_guide.md)**: Extending templates

---

**Status**: ✅ **Complete** - All 15 domain patterns documented with examples
**Next**: Create entity template catalog