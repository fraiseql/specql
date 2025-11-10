# Tutorial 2: Building a CRM (30 minutes)

Build a complete Customer Relationship Management system using SpecQL's entity relationships, state machines, and business logic patterns.

## 🎯 What You'll Learn

- Design related entities
- Implement state machines for lead management
- Add business logic validation
- Generate comprehensive tests

## 📋 Prerequisites

- Completed [Tutorial 1: Hello SpecQL](../01-hello-specql.md)
- Basic understanding of CRM concepts

## 🏗️ Step 1: Design Your CRM Entities

Create a `crm/` directory and design your core entities:

### Contact Entity (`crm/contact.yaml`)

```yaml
entity: Contact
schema: crm
description: "CRM contact information"

fields:
  email: text
  first_name: text
  last_name: text
  company: ref(Company)
  phone: text
  status: enum(lead, qualified, customer, inactive)
  lead_score: integer
  last_contacted: timestamp
  created_at: timestamp

actions:
  - name: create_contact
    pattern: crud/create
    requires: caller.can_create_contacts

  - name: update_contact
    pattern: crud/update
    requires: caller.can_edit_contacts
    fields: [first_name, last_name, phone, lead_score]

  - name: qualify_lead
    pattern: state_machine/transition
    requires: caller.can_qualify_leads
    from_state: lead
    to_state: qualified
    steps:
      - validate: lead_score >= 50
        error: "insufficient_lead_score"
      - update: Contact SET status = 'qualified', last_contacted = now()

  - name: convert_to_customer
    pattern: state_machine/transition
    requires: caller.can_convert_customers
    from_state: qualified
    to_state: customer
    steps:
      - update: Contact SET status = 'customer', last_contacted = now()
```

### Company Entity (`crm/company.yaml`)

```yaml
entity: Company
schema: crm
description: "CRM company information"

fields:
  name: text
  domain: text
  industry: text
  size: enum(startup, small, medium, enterprise)
  revenue: decimal(12,2)
  created_at: timestamp

actions:
  - name: create_company
    pattern: crud/create
    requires: caller.can_create_companies

  - name: update_company
    pattern: crud/update
    requires: caller.can_edit_companies
    fields: [name, domain, industry, size, revenue]
```

### Deal Entity (`crm/deal.yaml`)

```yaml
entity: Deal
schema: crm
description: "CRM sales deal"

fields:
  contact_id: ref(Contact)
  company_id: ref(Company)
  title: text
  value: decimal(10,2)
  stage: enum(prospecting, qualification, proposal, negotiation, closed_won, closed_lost)
  expected_close_date: date
  probability: integer  # 0-100
  created_at: timestamp
  closed_at: timestamp

actions:
  - name: create_deal
    pattern: crud/create
    requires: caller.can_create_deals

  - name: advance_deal
    pattern: state_machine/guarded_transition
    requires: caller.can_advance_deals
    from_states: [prospecting, qualification, proposal, negotiation]
    to_state: closed_won
    guard: probability >= 80
    steps:
      - update: Deal SET stage = 'closed_won', closed_at = now()

  - name: lose_deal
    pattern: state_machine/transition
    requires: caller.can_close_deals
    from_states: [prospecting, qualification, proposal, negotiation]
    to_state: closed_lost
    steps:
      - update: Deal SET stage = 'closed_lost', closed_at = now()
```

## 🗄️ Step 2: Generate and Apply Schema

Generate the complete CRM schema:

```bash
# Generate schema for all entities
specql generate schema

# Apply to database
specql db migrate
```

Check your generated tables:

```sql
-- Connect to database
psql $DATABASE_URL

-- List CRM tables
\dt crm.*

-- Should show: contact, company, deal tables
```

## 🏃 Step 3: Create CRM Data

Create some sample CRM data:

```sql
-- Create a company
SELECT crm.create_company(
    'Acme Corp',
    'acme.com',
    'Technology',
    'medium',
    5000000.00
);

-- Create a contact
SELECT crm.create_contact(
    'john.doe@acme.com',
    'John',
    'Doe',
    (SELECT id FROM crm.company WHERE name = 'Acme Corp'),
    '+1-555-0123',
    75  -- lead score
);

-- Create a deal
SELECT crm.create_deal(
    (SELECT id FROM crm.contact WHERE email = 'john.doe@acme.com'),
    (SELECT id FROM crm.company WHERE name = 'Acme Corp'),
    'Enterprise Software License',
    250000.00,
    'prospecting',
    '2024-03-15',
    30
);
```

## 🔄 Step 4: Use State Machines

Demonstrate the lead qualification workflow:

```sql
-- Check initial contact status
SELECT first_name, last_name, status, lead_score
FROM crm.contact WHERE email = 'john.doe@acme.com';

-- Try to qualify (should fail - lead score too low)
SELECT crm.qualify_lead(
    (SELECT id FROM crm.contact WHERE email = 'john.doe@acme.com')
);
-- ERROR: insufficient_lead_score

-- Update lead score and try again
UPDATE crm.contact SET lead_score = 85 WHERE email = 'john.doe@acme.com';

SELECT crm.qualify_lead(
    (SELECT id FROM crm.contact WHERE email = 'john.doe@acme.com')
);
-- SUCCESS

-- Check updated status
SELECT first_name, last_name, status, lead_score
FROM crm.contact WHERE email = 'john.doe@acme.com';
-- Should show: status = 'qualified'
```

## 📊 Step 5: Query CRM Analytics

Create some analytics queries:

```sql
-- CRM Dashboard: Contact status breakdown
SELECT
    status,
    COUNT(*) as contact_count,
    ROUND(AVG(lead_score), 1) as avg_lead_score
FROM crm.contact
GROUP BY status
ORDER BY contact_count DESC;

-- Deal pipeline by stage
SELECT
    stage,
    COUNT(*) as deal_count,
    SUM(value) as total_value,
    ROUND(AVG(probability), 1) as avg_probability,
    ROUND(SUM(value * probability / 100), 0) as weighted_value
FROM crm.deal
GROUP BY stage
ORDER BY total_value DESC;

-- Company performance
SELECT
    c.name as company_name,
    COUNT(co.id) as contact_count,
    COUNT(d.id) as deal_count,
    COALESCE(SUM(d.value), 0) as total_deal_value
FROM crm.company c
LEFT JOIN crm.contact co ON c.id = co.company_id
LEFT JOIN crm.deal d ON c.id = d.company_id
GROUP BY c.id, c.name
ORDER BY total_deal_value DESC;
```

## 🧪 Step 6: Generate and Run Tests

Generate comprehensive tests for your CRM:

```bash
# Generate tests
specql generate tests

# Run all tests
specql test

# Run specific CRM tests
specql test --pattern "*crm*"
```

Check test results:

```sql
-- Run pgTAP tests manually
SELECT * FROM runtests('crm.contact_test');
SELECT * FROM runtests('crm.deal_state_machine_test');
```

## 🔧 Step 7: Add Business Logic

Enhance your CRM with more advanced patterns. Add a `crm/activity.yaml` for tracking interactions:

```yaml
entity: Activity
schema: crm
description: "CRM activity tracking"

fields:
  contact_id: ref(Contact)
  type: enum(call, email, meeting, note)
  subject: text
  description: text
  created_by: uuid
  created_at: timestamp

actions:
  - name: log_activity
    pattern: crud/create
    requires: caller.can_log_activities
    steps:
      - insert: Activity
      - update: Contact SET last_contacted = now()
        WHERE id = contact_id
```

Regenerate and test:

```bash
specql generate schema
specql db migrate
specql generate tests
specql test
```

## 📈 Step 8: Advanced CRM Queries

Create advanced analytics:

```sql
-- Contact engagement analysis
SELECT
    c.first_name || ' ' || c.last_name as contact_name,
    c.status,
    c.lead_score,
    COUNT(a.id) as activity_count,
    MAX(a.created_at) as last_activity,
    EXTRACT(days FROM now() - MAX(a.created_at)) as days_since_last_activity
FROM crm.contact c
LEFT JOIN crm.activity a ON c.id = a.contact_id
GROUP BY c.id, c.first_name, c.last_name, c.status, c.lead_score
ORDER BY days_since_last_activity;

-- Deal conversion funnel
WITH deal_stages AS (
    SELECT
        stage,
        COUNT(*) as count_in_stage,
        ROUND(AVG(probability), 1) as avg_probability
    FROM crm.deal
    GROUP BY stage
),
stage_order AS (
    SELECT
        stage,
        ROW_NUMBER() OVER (ORDER BY
            CASE stage
                WHEN 'prospecting' THEN 1
                WHEN 'qualification' THEN 2
                WHEN 'proposal' THEN 3
                WHEN 'negotiation' THEN 4
                WHEN 'closed_won' THEN 5
                WHEN 'closed_lost' THEN 6
            END
        ) as stage_order
    FROM (SELECT DISTINCT stage FROM crm.deal) s
)
SELECT
    so.stage_order,
    ds.stage,
    ds.count_in_stage,
    ds.avg_probability,
    ROUND(
        100.0 * ds.count_in_stage /
        FIRST_VALUE(ds.count_in_stage) OVER (ORDER BY so.stage_order),
        1
    ) as conversion_rate
FROM deal_stages ds
JOIN stage_order so ON ds.stage = so.stage
ORDER BY so.stage_order;
```

## 🎉 Success!

You've built a complete CRM system with:

✅ **Entity Relationships**: Contacts, companies, deals
✅ **State Machines**: Lead qualification workflow
✅ **Business Logic**: Validation and guard conditions
✅ **Analytics**: Comprehensive reporting queries
✅ **Testing**: Full test coverage
✅ **Advanced Patterns**: Activity tracking and analytics

## 🧪 Test Your Knowledge

Try these advanced exercises:

1. **Add deal stages**: Extend the deal state machine with more stages
2. **Create reports**: Build monthly sales reports
3. **Add notifications**: Implement email notifications for status changes
4. **Bulk operations**: Add bulk contact import functionality
5. **API integration**: Connect to email marketing service

## 📚 Next Steps

- [Tutorial 3: State Machines](../03-state-machines.md) - Deep dive into state machines
- [Tutorial 4: Testing](../04-testing.md) - Advanced testing patterns
- [Tutorial 5: Production](../05-production.md) - Production deployment

## 💡 Pro Tips

- Use `specql generate --watch` during development
- Create separate schema files for different domains
- Use `specql validate` to catch errors early
- Leverage generated tests for regression protection
- Consider using views for complex analytics queries

---

**Time completed**: 30 minutes
**Entities created**: Contact, Company, Deal, Activity
**Tests generated**: 50+ test cases
**Next tutorial**: [State Machines →](../03-state-machines.md)