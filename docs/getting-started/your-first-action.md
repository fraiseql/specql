# Your First Action

## Overview

Actions are SpecQL's way of defining business logic. Instead of stored procedures, you write declarative steps that SpecQL converts to PostgreSQL functions with GraphQL integration.

**Time**: 10 minutes
**Prerequisites**: [Your first entity](your-first-entity.md) created

## Step 1: Add Action to Entity

Update `entities/contact.yaml`:

```yaml
entity: Contact
schema: crm
description: "Customer contact information"

fields:
  email: text
  first_name: text
  last_name: text
  company: text?
  status: enum(lead, qualified, customer)
  notes: text?

actions:
  - name: qualify_lead
    description: "Convert a lead to a qualified contact"
    impacts:
      write: [Contact]
    steps:
      - validate: status = 'lead'
      - update: Contact SET status = 'qualified', qualified_at = NOW()
      - notify: contact_qualified WITH {contact_id: :id}
```

## Step 2: Understand Action Structure

**Required elements**:
- **`name`**: Function name (snake_case)
- **`description`**: Human-readable purpose
- **`impacts`**: Entities affected (for GraphQL optimization)
- **`steps`**: Business logic steps

**Step types**:
- **`validate`**: Check preconditions
- **`update`**: Modify data
- **`notify`**: Send events

## Step 3: Generate and Apply

```bash
# Regenerate schema
specql generate entities/contact.yaml

# Apply new functions
psql $DATABASE_URL -f db/schema/30_functions/crm_qualify_lead.sql
```

## Step 4: Test the Action

```bash
# Insert test data
psql $DATABASE_URL -c "
INSERT INTO crm.tb_contact (email, first_name, last_name, status)
VALUES ('jane@example.com', 'Jane', 'Smith', 'lead');
"

# Call the action
psql $DATABASE_URL -c "
SELECT crm.qualify_lead(1);  -- Assuming id = 1
"

# Check result
psql $DATABASE_URL -c "
SELECT id, email, status, qualified_at FROM crm.tb_contact;
"
```

## Step 5: GraphQL Integration

SpecQL automatically creates GraphQL wrappers:

```bash
# Check generated GraphQL function
cat db/schema/30_functions/app_qualify_lead.sql
```

**Generated GraphQL function**:
```sql
CREATE FUNCTION app.qualify_lead(contact_id INTEGER)
RETURNS app.mutation_result AS $$
-- GraphQL entry point that calls crm.qualify_lead
$$ LANGUAGE sql;
```

## Understanding Action Steps

### Validate Step
```yaml
- validate: status = 'lead'
```
- **Purpose**: Ensure preconditions are met
- **Failure**: Returns error, stops execution
- **Syntax**: SQL WHERE clause

### Update Step
```yaml
- update: Contact SET status = 'qualified', qualified_at = NOW()
```
- **Purpose**: Modify existing records
- **Auto-generates**: `updated_at`, `updated_by`
- **Returns**: Updated record data

### Notify Step
```yaml
- notify: contact_qualified WITH {contact_id: :id}
```
- **Purpose**: Send PostgreSQL NOTIFY events
- **Use**: Trigger external systems, webhooks
- **Payload**: JSON data with variables

## Variables in Actions

| Variable | Meaning | Example |
|----------|---------|---------|
| `:id` | Current entity ID | `:id` |
| `:param_name` | Input parameter | `:contact_id` |
| `NOW()` | Current timestamp | `qualified_at = NOW()` |
| `CURRENT_USER` | Current user UUID | `updated_by = CURRENT_USER` |

## More Complex Actions

### With Input Parameters

```yaml
actions:
  - name: update_contact
    description: "Update contact information"
    impacts:
      write: [Contact]
    steps:
      - update: Contact SET
          first_name = :first_name,
          last_name = :last_name,
          notes = :notes
        WHERE id = :id
```

### With Conditional Logic

```yaml
actions:
  - name: process_order
    description: "Process customer order"
    impacts:
      write: [Order, Inventory]
      read: [Customer]
    steps:
      - validate: status = 'pending'
      - if: total_amount > 1000
        then:
          - update: Order SET status = 'requires_approval'
        else:
          - update: Order SET status = 'approved'
          - call: inventory.reserve_stock(order_id: :id)
```

### With Loops

```yaml
actions:
  - name: bulk_update_status
    description: "Update status for multiple contacts"
    impacts:
      write: [Contact]
    steps:
      - foreach: contact IN :contact_ids
        do:
          - update: Contact SET status = :new_status WHERE id = :contact.id
```

## Step 6: Test GraphQL Integration

```bash
# Check if FraiseQL is configured
psql $DATABASE_URL -c "
SELECT app.qualify_lead(1);
"

# Should return JSON result
{
  "success": true,
  "data": {
    "id": 1,
    "status": "qualified",
    "qualified_at": "2024-01-15T10:30:00Z"
  }
}
```

## Best Practices

### Action Naming
- Use `snake_case`
- Start with verb: `create_order`, `update_profile`, `send_notification`
- Be specific: `qualify_sales_lead` vs `qualify`

### Impact Declaration
- **`write`**: Entities modified by this action
- **`read`**: Entities read (for GraphQL query optimization)
- Be complete: Missing impacts break GraphQL caching

### Validation First
- Put `validate` steps at the beginning
- Check all preconditions before making changes
- Fail fast with clear error messages

### Error Handling
- Actions automatically handle transactions
- Validation failures roll back changes
- Use `notify` for external error handling

## Next Steps

- [Add more complex actions](../../guides/actions-guide.md)
- [Set up GraphQL client](../../reference/cli-reference.md#output-frontend-path)
- [Add authentication](../../architecture/)
- [Deploy to production](../../guides/migration-guide.md)

## Troubleshooting

**"Action not found"**
```bash
# Regenerate after adding action
specql generate entities/contact.yaml
psql $DATABASE_URL -f db/schema/30_functions/crm_qualify_lead.sql
```

**"Permission denied for function"**
```bash
# Grant execute permissions
GRANT EXECUTE ON FUNCTION crm.qualify_lead(INTEGER) TO app_user;
```

**"Invalid variable reference"**
```yaml
# ❌ Wrong
- update: Contact SET status = :status

# ✅ Correct (if status is input parameter)
- update: Contact SET status = :new_status
```

**"Circular dependency in impacts"**
- Remove unnecessary `read` impacts
- Check for actual dependencies
- Use `call` instead of direct impacts