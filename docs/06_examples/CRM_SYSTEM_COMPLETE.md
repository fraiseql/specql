# Complete CRM System Example

**What You'll Build**: A production-ready CRM with contacts, companies, deals, and activities.

**Time**: 30 minutes
**Complexity**: Intermediate

## System Overview

Our CRM will have:
- **Companies**: Organizations we do business with
- **Contacts**: People at those companies
- **Deals**: Sales opportunities
- **Activities**: Calls, emails, meetings

## Architecture

```
Company (1) ──< (N) Contact
   │                  │
   │                  │
   └──< (N) Deal <────┘
          │
          └──< (N) Activity
```

## Step 1: Create Company Entity

Create `entities/crm/company.yaml`:

```yaml
entity: Company
schema: crm
description: An organization we do business with

fields:
  # Identity
  name: text  # This becomes 'identifier' (Trinity pattern)
  legal_name: text
  website: url

  # Contact info
  phone: text
  email: email

  # Address
  address_line1: text
  address_line2: text
  city: text
  state: text
  postal_code: text
  country: text

  # Business info
  industry: text
  employee_count: integer
  annual_revenue: decimal

  # Status
  status: enum(prospect, customer, partner, inactive)

  # Metadata (created_at, updated_at auto-added)

indexes:
  - fields: [name]
    unique: true
  - fields: [status]
  - fields: [industry]

actions:
  - name: convert_to_customer
    description: Convert prospect to customer
    requires: caller.can_manage_companies
    steps:
      - validate: status = 'prospect'
        error: "already_customer"
      - update: Company SET status = 'customer'
      - notify: sales_team
      - log: "Company converted to customer"
```

## Step 2: Create Contact Entity

Create `entities/crm/contact.yaml`:

```yaml
entity: Contact
schema: crm
description: A person at a company we do business with

fields:
  # Identity
  first_name: text
  last_name: text
  email: email
  phone: text

  # Job info
  job_title: text
  department: text

  # Relationships
  company: ref(Company)

  # Status
  status: enum(lead, qualified, customer, inactive)

  # Preferences
  preferred_contact_method: enum(email, phone, in_person)

indexes:
  - fields: [email]
    unique: true
  - fields: [company_id, status]
  - fields: [last_name, first_name]

actions:
  - name: qualify_lead
    description: Convert lead to qualified prospect
    requires: caller.can_qualify_leads
    steps:
      - validate: status = 'lead'
        error: "contact_already_qualified"
      - update: Contact SET status = 'qualified'
      - notify: sales_rep
      - log: "Contact qualified as prospect"

  - name: convert_to_customer
    description: Convert qualified contact to customer
    requires: caller.can_convert_customers
    steps:
      - validate: status = 'qualified'
        error: "contact_not_qualified"
      - update: Contact SET status = 'customer'
      - update: Company SET status = 'customer' WHERE id = company_id
      - notify: account_manager
      - log: "Contact converted to customer"
```

## Step 3: Create Deal Entity

Create `entities/crm/deal.yaml`:

```yaml
entity: Deal
schema: crm
description: A sales opportunity

fields:
  # Deal info
  name: text
  description: text
  amount: decimal
  currency: text
  expected_close_date: date

  # Relationships
  company: ref(Company)
  primary_contact: ref(Contact)

  # Sales process
  stage: enum(prospecting, qualification, proposal, negotiation, closed_won, closed_lost)
  probability: integer  # 0-100

  # Assignment
  assigned_to: text  # User ID or name

indexes:
  - fields: [company_id, stage]
  - fields: [assigned_to, expected_close_date]
  - fields: [stage, probability]

actions:
  - name: advance_stage
    description: Move deal to next stage
    requires: caller.can_advance_deals
    steps:
      - validate: stage IN ('prospecting', 'qualification', 'proposal', 'negotiation')
        error: "deal_already_closed"
      - update: Deal SET stage = CASE
          WHEN stage = 'prospecting' THEN 'qualification'
          WHEN stage = 'qualification' THEN 'proposal'
          WHEN stage = 'proposal' THEN 'negotiation'
          WHEN stage = 'negotiation' THEN 'closed_won'
        END
      - update: Deal SET probability = CASE
          WHEN stage = 'qualification' THEN 30
          WHEN stage = 'proposal' THEN 60
          WHEN stage = 'negotiation' THEN 90
          WHEN stage = 'closed_won' THEN 100
        END WHERE stage IN ('qualification', 'proposal', 'negotiation', 'closed_won')
      - notify: sales_team
      - log: "Deal advanced to {stage}"

  - name: close_won
    description: Mark deal as won
    requires: caller.can_close_deals
    steps:
      - validate: stage != 'closed_won'
        error: "deal_already_won"
      - update: Deal SET stage = 'closed_won', probability = 100
      - notify: finance_team
      - log: "Deal closed won"

  - name: close_lost
    description: Mark deal as lost
    requires: caller.can_close_deals
    steps:
      - validate: stage != 'closed_lost'
        error: "deal_already_lost"
      - update: Deal SET stage = 'closed_lost', probability = 0
      - notify: sales_manager
      - log: "Deal closed lost"
```

## Step 4: Create Activity Entity

Create `entities/crm/activity.yaml`:

```yaml
entity: Activity
schema: crm
description: A sales activity (call, email, meeting)

fields:
  # Activity info
  type: enum(call, email, meeting, demo, webinar, other)
  subject: text
  description: text
  duration_minutes: integer

  # When it happened
  scheduled_at: timestamp
  completed_at: timestamp

  # Relationships
  deal: ref(Deal)
  contact: ref(Contact)
  company: ref(Company)

  # Outcome
  outcome: enum(scheduled, completed, cancelled, no_show)
  notes: text

indexes:
  - fields: [deal_id, scheduled_at]
  - fields: [contact_id, type]
  - fields: [scheduled_at, outcome]

actions:
  - name: complete_activity
    description: Mark activity as completed
    requires: caller.can_log_activities
    steps:
      - validate: outcome = 'scheduled'
        error: "activity_not_scheduled"
      - update: Activity SET outcome = 'completed', completed_at = NOW()
      - notify: assigned_user
      - log: "Activity completed"

  - name: reschedule_activity
    description: Reschedule a planned activity
    requires: caller.can_manage_activities
    steps:
      - validate: outcome = 'scheduled'
        error: "activity_not_scheduled"
      - update: Activity SET scheduled_at = ?
      - notify: participants
      - log: "Activity rescheduled"
```

## Step 5: Generate the Complete System

```bash
# Create output directory
mkdir -p output/crm

# Generate all entities
specql generate entities/crm/*.yaml --output output/crm

# You should see generation for all 4 entities
```

## Step 6: Inspect Generated Code

### PostgreSQL Schema
```bash
# Check the generated tables
cat output/crm/postgresql/crm/01_tables.sql

# You'll see:
# - crm.tb_company (companies)
# - crm.tb_contact (contacts)
# - crm.tb_deal (deals)
# - crm.tb_activity (activities)
# - Foreign key relationships
# - Indexes and constraints
```

### Business Logic Functions
```bash
# Check the generated functions
cat output/crm/postgresql/crm/02_functions.sql

# You'll see functions like:
# - crm.fn_company_convert_to_customer()
# - crm.fn_contact_qualify_lead()
# - crm.fn_deal_advance_stage()
# - crm.fn_activity_complete_activity()
```

### Java/Spring Boot
```bash
# Check Java entities
ls output/crm/java/com/example/crm/

# You'll see:
# - Company.java, CompanyRepository.java, CompanyService.java
# - Contact.java, ContactRepository.java, ContactService.java
# - Deal.java, DealRepository.java, DealService.java
# - Activity.java, ActivityRepository.java, ActivityService.java
```

## Step 7: Test the CRM System

If you have PostgreSQL running:

```bash
# Create test database
createdb crm_test

# Apply schema
psql crm_test < output/crm/postgresql/crm/01_tables.sql
psql crm_test < output/crm/postgresql/crm/02_functions.sql

# Insert test data
psql crm_test << 'EOF'
-- Create a company
INSERT INTO crm.tb_company (name, industry, status)
VALUES ('Acme Corp', 'Technology', 'prospect');

-- Create a contact
INSERT INTO crm.tb_contact (first_name, last_name, email, company_id, status)
VALUES ('John', 'Doe', 'john@acme.com', 1, 'lead');

-- Create a deal
INSERT INTO crm.tb_deal (name, amount, company_id, primary_contact_id, stage, probability)
VALUES ('Enterprise Software License', 50000.00, 1, 1, 'prospecting', 10);

-- Log an activity
INSERT INTO crm.tb_activity (type, subject, deal_id, contact_id, outcome)
VALUES ('call', 'Initial outreach', 1, 1, 'completed');
EOF

# Query the data
psql crm_test -c "SELECT * FROM crm.tv_company;"
psql crm_test -c "SELECT * FROM crm.tv_contact;"
psql crm_test -c "SELECT * FROM crm.tv_deal;"
psql crm_test -c "SELECT * FROM crm.tv_activity;"

# Test business logic
psql crm_test -c "SELECT crm.fn_contact_qualify_lead(1, 'sales@example.com');"
psql crm_test -c "SELECT crm.fn_deal_advance_stage(1, 'sales@example.com');"
```

## Step 8: FraiseQL Integration

Add this to your FraiseQL configuration:

```yaml
# fraiseql-config.yaml
schemas:
  - name: crm
    entities:
      - entities/crm/company.yaml
      - entities/crm/contact.yaml
      - entities/crm/deal.yaml
      - entities/crm/activity.yaml

# This gives you instant GraphQL API:
# - query { companies { name contacts { firstName lastName } } }
# - mutation { qualifyLead(contactId: 1) { success } }
```

## Common CRM Patterns Used

### 1. Status Workflow
- **Leads** → **Qualified** → **Customers**
- **Prospects** → **Customers** → **Partners**
- **Prospecting** → **Qualification** → **Proposal** → **Negotiation** → **Closed**

### 2. Audit Logging
All actions automatically log changes with timestamps and user context.

### 3. Soft Deletes
Entities remain in database but are marked inactive rather than deleted.

### 4. Trinity Pattern
Every table has:
- `pk_*`: Auto-incrementing primary key
- `id`: UUID for external references
- `identifier`: Human-readable unique identifier

### 5. Business Logic Validation
Actions validate state before making changes:
```yaml
actions:
  - name: qualify_lead
    steps:
      - validate: status = 'lead'  # Must be lead first
      - update: Contact SET status = 'qualified'
```

## Full Source Code

All YAML files for this example:
- [View Source](../../examples/crm/)
- [View on GitHub](https://github.com/fraiseql/specql/tree/main/examples/crm)

## Next Steps

- Add user authentication and permissions
- Integrate with email/calendar systems
- Add reporting and analytics
- Implement mobile app frontend
- Set up CI/CD pipeline

This CRM system demonstrates how SpecQL enables rapid development of complex, production-ready business applications with proper data relationships, business logic, and multi-language code generation.