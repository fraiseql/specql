# Entity Templates Reference

This document describes the 15+ entity templates in SpecQL - pre-configured business entities that combine domain patterns into complete, production-ready implementations.

## Overview

Entity templates provide complete business entity implementations with:

- **Pre-configured Fields**: Industry-standard field sets
- **Domain Patterns**: Appropriate business logic patterns
- **Actions**: Common operations and workflows
- **Relationships**: Standard entity relationships
- **Validation**: Built-in business rules
- **Multi-Language**: PostgreSQL, Django, and SQLAlchemy generation

## Template Categories

### CRM (Customer Relationship Management)

#### Contact Template
**Purpose**: Customer and prospect contact information

**Features**:
- Basic contact details (name, email, phone)
- Address information
- Lead scoring and qualification
- Communication preferences
- State machine for lead lifecycle

**Configuration**:
```yaml
# Instantiate with customizations
template: crm.contact
customizations:
  additional_fields:
    linkedin_url: text
    twitter_handle: text
  enable_lead_scoring: true
  custom_states: [prospect, qualified, customer, lost]
```

**Generated Entities**:
- Contact table with all fields
- Lead scoring functions
- State transition actions
- Communication tracking

#### Lead Template
**Purpose**: Sales lead management

**Features**:
- Lead source tracking
- Qualification criteria
- Conversion tracking
- Assignment and routing
- Follow-up scheduling

**Configuration**:
```yaml
template: crm.lead
customizations:
  qualification_criteria:
    - budget: numeric
    - timeline: date
    - decision_makers: integer
  auto_assignment: true
  lead_scoring: true
```

#### Opportunity Template
**Purpose**: Sales opportunity tracking

**Features**:
- Deal value and probability
- Sales stage management
- Competitor tracking
- Forecast calculations
- Win/loss analysis

**Configuration**:
```yaml
template: crm.opportunity
customizations:
  stages: [discovery, proposal, negotiation, closed_won, closed_lost]
  forecast_accuracy: true
  competitor_tracking: true
```

#### Account Template
**Purpose**: Customer account management

**Features**:
- Account hierarchy
- Contact relationships
- Account health scoring
- Revenue tracking
- Contract management

### E-Commerce

#### Product Template
**Purpose**: Product catalog management

**Features**:
- Product variants and options
- Pricing and inventory
- Categories and attributes
- Image management
- Search optimization

**Configuration**:
```yaml
template: ecommerce.product
customizations:
  enable_variants: true
  enable_inventory_tracking: true
  additional_patterns: [soft_delete, search_optimization]
```

#### Order Template
**Purpose**: Order processing and fulfillment

**Features**:
- Order lifecycle management
- Payment processing integration
- Shipping and tracking
- Order modifications
- Returns and refunds

**Configuration**:
```yaml
template: ecommerce.order
customizations:
  payment_integration: true
  shipping_providers: [fedex, ups, dhl]
  order_modifications: true
```

#### Cart Template
**Purpose**: Shopping cart functionality

**Features**:
- Cart persistence
- Item management
- Price calculations
- Coupon and discount handling
- Cart conversion tracking

#### Customer Template
**Purpose**: E-commerce customer profiles

**Features**:
- Purchase history
- Preferences and segmentation
- Loyalty program integration
- Address book management
- Wishlist functionality

### Healthcare

#### Patient Template
**Purpose**: Patient information management

**Features**:
- Medical record number
- Demographics and insurance
- Medical history tracking
- Appointment scheduling
- Consent and privacy management

**Configuration**:
```yaml
template: healthcare.patient
customizations:
  hipaa_compliance: true
  medical_history_tracking: true
  insurance_integration: true
```

#### Appointment Template
**Purpose**: Medical appointment scheduling

**Features**:
- Provider scheduling
- Patient booking
- Waitlist management
- Cancellation and rescheduling
- Reminder notifications

#### Prescription Template
**Purpose**: Medication management

**Features**:
- Prescription tracking
- Dosage instructions
- Refill management
- Drug interaction checking
- Pharmacy integration

#### Provider Template
**Purpose**: Healthcare provider profiles

**Features**:
- Provider credentials and specialties
- Schedule management
- Patient assignments
- Performance tracking
- Continuing education

### Project Management

#### Project Template
**Purpose**: Project definition and tracking

**Features**:
- Project hierarchy
- Timeline and milestone management
- Resource allocation
- Budget tracking
- Risk management

**Configuration**:
```yaml
template: project_mgmt.project
customizations:
  enable_budget_tracking: true
  risk_management: true
  resource_allocation: true
```

#### Task Template
**Purpose**: Task and work item management

**Features**:
- Task dependencies
- Time tracking
- Assignment and delegation
- Progress reporting
- Quality assurance

#### Milestone Template
**Purpose**: Project milestone tracking

**Features**:
- Milestone dependencies
- Progress measurement
- Stakeholder notifications
- Risk assessment
- Completion validation

### Human Resources

#### Employee Template
**Purpose**: Employee information management

**Features**:
- Personal and contact information
- Job details and compensation
- Performance management
- Training and development
- Benefits administration

**Configuration**:
```yaml
template: hr.employee
customizations:
  performance_reviews: true
  training_tracking: true
  benefits_integration: true
```

#### Position Template
**Purpose**: Job position definitions

**Features**:
- Position descriptions
- Requirements and qualifications
- Compensation structures
- Reporting relationships
- Succession planning

#### Department Template
**Purpose**: Organizational structure

**Features**:
- Department hierarchy
- Budget management
- Headcount planning
- Performance metrics
- Resource allocation

#### Timesheet Template
**Purpose**: Time tracking and attendance

**Features**:
- Time entry and approval
- Project time allocation
- Overtime calculation
- Leave management
- Payroll integration

### Finance

#### Invoice Template
**Purpose**: Invoice creation and management

**Features**:
- Invoice generation
- Line item management
- Tax calculations
- Payment tracking
- Aging and collections

**Configuration**:
```yaml
template: finance.invoice
customizations:
  multi_currency: true
  tax_integration: true
  payment_terms: [net_30, net_60, due_on_receipt]
```

#### Payment Template
**Purpose**: Payment processing and tracking

**Features**:
- Payment method handling
- Transaction processing
- Reconciliation
- Refund management
- Fraud detection

#### Transaction Template
**Purpose**: Financial transaction recording

**Features**:
- Double-entry accounting
- Transaction categorization
- Audit trail
- Reconciliation
- Financial reporting

## Template Instantiation

Templates are instantiated using the CLI:

```bash
# Instantiate a basic template
specql instantiate crm.contact --output contact.yaml

# Instantiate with customizations
specql instantiate ecommerce.product \
  --customizations '{"enable_variants": true, "enable_inventory_tracking": true}' \
  --output product.yaml

# List available templates
specql templates list

# Show template details
specql templates show crm.contact
```

## Customization Options

All templates support customization through parameters:

```yaml
template: crm.contact
customizations:
  # Add custom fields
  additional_fields:
    custom_field_1: text
    custom_field_2: integer

  # Modify existing patterns
  state_machine:
    states: [draft, active, inactive, archived]
    initial_state: draft

  # Enable/disable features
  enable_audit_trail: true
  enable_soft_delete: false

  # Configure relationships
  relationships:
    - entity: Account
      type: many_to_one
      field: account_id
```

## Generated Code Structure

Each template generates:

### PostgreSQL
- Table schema with constraints
- Functions for business logic
- Triggers for automation
- Indexes for performance
- Views for reporting

### Django
- Model classes with relationships
- Manager classes for queries
- Form classes for validation
- Admin configuration
- Migration files

### SQLAlchemy
- Declarative model classes
- Relationship definitions
- Query helpers
- Event listeners
- Migration scripts

## Template Composition

Templates can be extended and combined:

```yaml
# Start with a base template
template: crm.contact

# Add additional patterns
additional_patterns:
  - commenting:
      threaded: true
      moderation: true
  - file_attachment:
      max_file_size: "5MB"
      allowed_types: ["pdf", "doc", "jpg"]

# Add custom actions
custom_actions:
  - name: send_welcome_email
    type: notification
    template: "welcome_email"
    triggers: ["after_create"]
```

## Industry-Specific Templates

### SaaS Multi-Tenant
- Organization management
- User provisioning
- Subscription handling
- Feature flags
- Usage tracking

### Manufacturing
- Bill of materials
- Work order management
- Quality control
- Inventory optimization
- Production scheduling

### Education
- Student information systems
- Course management
- Grade tracking
- Attendance monitoring
- Certification management

## Best Practices

1. **Start with Templates**: Use templates as starting points rather than building from scratch
2. **Customize Incrementally**: Add customizations gradually, testing at each step
3. **Follow Naming Conventions**: Use consistent field names and relationships
4. **Test Generated Code**: Always test the generated multi-language output
5. **Version Control**: Keep template customizations under version control

## Migration from Custom Code

Templates can be used to modernize existing systems:

```bash
# Reverse engineer existing SQL
specql reverse existing_functions.sql --output analysis.yaml

# Identify applicable templates
specql analyze analysis.yaml --suggest-templates

# Generate migration plan
specql migrate plan --from analysis.yaml --to crm.contact
```

## Performance Considerations

Templates include performance optimizations:

- **Indexes**: Automatic index creation for common queries
- **Partitioning**: Support for large table partitioning
- **Caching**: Query result caching strategies
- **Archiving**: Data archiving for historical records
- **Monitoring**: Performance monitoring and alerting

## Related Documentation

- [Domain Patterns](domain_patterns.md) - Individual business logic patterns
- [Primitives](primitives.md) - Low-level building blocks
- [CLI Commands](cli_commands.md) - Command-line interface
- [Migration Guide](../../guides/migration_guide.md) - Converting existing systems