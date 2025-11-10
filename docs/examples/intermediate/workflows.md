# Business Workflows Example

This example demonstrates how to implement complex business workflows using SpecQL's workflow orchestration patterns for multi-step processes with conditional logic and approvals.

## Overview

We'll create a purchase requisition system that requires:
1. Requisition submission
2. Manager approval
3. Budget verification
4. Final approval
5. Purchase order creation

This shows how SpecQL handles complex, multi-step business processes.

## Entity Definitions

### Purchase Requisition Entity (`requisition.yaml`)

```yaml
entity: PurchaseRequisition
schema: procurement
description: "Purchase requisition with approval workflow"

fields:
  requester_id: uuid
  department: text
  description: text
  total_amount: decimal(10,2)
  status: enum(draft, submitted, manager_approved, budget_approved, approved, rejected, ordered)
  submitted_at: timestamp
  approved_at: timestamp
  ordered_at: timestamp

actions:
  # Submit requisition for approval
  - name: submit_requisition
    pattern: composite/workflow_orchestrator
    requires: caller.is_requester
    workflow:
      - step: validate_draft
        condition: "status = 'draft'"
        error: "can_only_submit_drafts"

      - step: validate_amount
        condition: "total_amount > 0"
        error: "invalid_amount"

      - step: update_status
        action: update
        entity: PurchaseRequisition
        fields: [status: 'submitted', submitted_at: 'now()']

      - step: notify_manager
        action: notify
        recipient: "department_manager"
        message: "New requisition requires approval"

  # Manager approval step
  - name: approve_by_manager
    pattern: composite/conditional_workflow
    requires: caller.is_manager
    conditions:
      - if: "total_amount <= 1000"
        then:
          - update: PurchaseRequisition SET status = 'approved', approved_at = now()
          - notify: requester "Requisition approved"
        else:
          - update: PurchaseRequisition SET status = 'manager_approved'
          - notify: budget_approver "Requisition requires budget approval"

  # Budget approval step
  - name: approve_budget
    pattern: composite/conditional_workflow
    requires: caller.can_approve_budget
    conditions:
      - if: "department_budget_available(total_amount, department)"
        then:
          - update: PurchaseRequisition SET status = 'budget_approved'
          - notify: final_approver "Requisition ready for final approval"
        else:
          - update: PurchaseRequisition SET status = 'rejected'
          - notify: requester "Insufficient budget"

  # Final approval and PO creation
  - name: final_approval
    pattern: composite/workflow_orchestrator
    requires: caller.can_final_approve
    workflow:
      - step: approve_requisition
        action: update
        entity: PurchaseRequisition
        fields: [status: 'approved', approved_at: 'now()']

      - step: create_purchase_order
        action: insert
        entity: PurchaseOrder
        fields:
          requisition_id: "id"
          vendor_id: "selected_vendor"
          total_amount: "total_amount"
          status: "'pending'"

      - step: notify_requester
        action: notify
        recipient: "requester"
        message: "Purchase order created"

  # Rejection workflow
  - name: reject_requisition
    pattern: composite/workflow_orchestrator
    requires: caller.can_reject_requisition
    workflow:
      - step: update_status
        action: update
        entity: PurchaseRequisition
        fields: [status: 'rejected']

      - step: notify_requester
        action: notify
        recipient: "requester"
        message: "Requisition rejected: {reason}"
```

### Purchase Order Entity (`purchase_order.yaml`)

```yaml
entity: PurchaseOrder
schema: procurement
description: "Purchase order created from approved requisition"

fields:
  requisition_id: uuid
  vendor_id: uuid
  total_amount: decimal(10,2)
  status: enum(pending, sent, received)
  created_at: timestamp
```

## Generated SQL

SpecQL generates complex workflow orchestration functions:

```sql
-- Submit requisition workflow
CREATE OR REPLACE FUNCTION procurement.submit_requisition(
    p_requisition_id uuid
) RETURNS void AS $$
DECLARE
    v_status text;
    v_amount decimal(10,2);
BEGIN
    -- Get current requisition state
    SELECT status, total_amount INTO v_status, v_amount
    FROM procurement.purchase_requisition WHERE id = p_requisition_id;

    -- Step 1: Validate draft status
    IF v_status != 'draft' THEN
        RAISE EXCEPTION 'Can only submit draft requisitions';
    END IF;

    -- Step 2: Validate amount
    IF v_amount <= 0 THEN
        RAISE EXCEPTION 'Invalid requisition amount';
    END IF;

    -- Step 3: Update status
    UPDATE procurement.purchase_requisition SET
        status = 'submitted',
        submitted_at = now()
    WHERE id = p_requisition_id;

    -- Step 4: Notify manager (would integrate with notification system)
    -- This is a placeholder for actual notification logic
    PERFORM notify_manager(p_requisition_id, 'New requisition requires approval');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Manager approval with conditional logic
CREATE OR REPLACE FUNCTION procurement.approve_by_manager(
    p_requisition_id uuid
) RETURNS void AS $$
DECLARE
    v_amount decimal(10,2);
    v_requester_id uuid;
BEGIN
    -- Get requisition details
    SELECT total_amount, requester_id INTO v_amount, v_requester_id
    FROM procurement.purchase_requisition WHERE id = p_requisition_id;

    -- Conditional workflow based on amount
    IF v_amount <= 1000 THEN
        -- Small amount: auto-approve
        UPDATE procurement.purchase_requisition SET
            status = 'approved',
            approved_at = now()
        WHERE id = p_requisition_id;

        PERFORM notify_user(v_requester_id, 'Requisition approved');
    ELSE
        -- Large amount: requires budget approval
        UPDATE procurement.purchase_requisition SET
            status = 'manager_approved'
        WHERE id = p_requisition_id;

        PERFORM notify_budget_approver(p_requisition_id, 'Requisition requires budget approval');
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Final approval with purchase order creation
CREATE OR REPLACE FUNCTION procurement.final_approval(
    p_requisition_id uuid,
    p_vendor_id uuid
) RETURNS uuid AS $$
DECLARE
    v_po_id uuid;
    v_amount decimal(10,2);
    v_requester_id uuid;
BEGIN
    -- Get requisition details
    SELECT total_amount, requester_id INTO v_amount, v_requester_id
    FROM procurement.purchase_requisition WHERE id = p_requisition_id;

    -- Step 1: Approve requisition
    UPDATE procurement.purchase_requisition SET
        status = 'approved',
        approved_at = now()
    WHERE id = p_requisition_id;

    -- Step 2: Create purchase order
    INSERT INTO procurement.purchase_order (
        requisition_id, vendor_id, total_amount, status, created_at
    ) VALUES (
        p_requisition_id, p_vendor_id, v_amount, 'pending', now()
    ) RETURNING id INTO v_po_id;

    -- Step 3: Notify requester
    PERFORM notify_user(v_requester_id, 'Purchase order created');

    RETURN v_po_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## Usage Examples

### Complete Requisition Workflow

```sql
-- 1. Create draft requisition
INSERT INTO procurement.purchase_requisition (
    requester_id, department, description, total_amount, status
) VALUES (
    'user-uuid-here',
    'Engineering',
    'New development servers',
    2500.00,
    'draft'
) RETURNING id;
-- Returns: requisition-uuid

-- 2. Submit for approval
SELECT procurement.submit_requisition('requisition-uuid');

-- 3. Manager approval (conditional based on amount)
SELECT procurement.approve_by_manager('requisition-uuid');
-- Since amount > 1000, moves to 'manager_approved'

-- 4. Budget approval
SELECT procurement.approve_budget('requisition-uuid');

-- 5. Final approval and PO creation
SELECT procurement.final_approval('requisition-uuid', 'vendor-uuid');
-- Returns: purchase-order-uuid
```

### Querying Workflow Status

```sql
-- Get requisition with full workflow status
SELECT
    pr.id,
    pr.description,
    pr.total_amount,
    pr.status,
    pr.submitted_at,
    pr.approved_at,
    po.id as purchase_order_id,
    po.status as po_status
FROM procurement.purchase_requisition pr
LEFT JOIN procurement.purchase_order po ON pr.id = po.requisition_id
WHERE pr.id = 'requisition-uuid';
```

### Workflow Analytics

```sql
-- Average approval time by department
SELECT
    department,
    AVG(EXTRACT(EPOCH FROM (approved_at - submitted_at))/3600) as avg_approval_hours,
    COUNT(*) as total_requisitions
FROM procurement.purchase_requisition
WHERE status = 'approved'
GROUP BY department;

-- Approval rate by amount range
SELECT
    CASE
        WHEN total_amount <= 100 THEN 'Small (≤$100)'
        WHEN total_amount <= 1000 THEN 'Medium ($101-$1000)'
        ELSE 'Large (>$1000)'
    END as amount_range,
    COUNT(*) as total,
    SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
    ROUND(
        SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END)::decimal /
        COUNT(*) * 100, 1
    ) as approval_rate
FROM procurement.purchase_requisition
GROUP BY amount_range;
```

## Error Handling

### Invalid State Transitions

```sql
-- Try to approve already approved requisition
SELECT procurement.approve_by_manager('approved-requisition-uuid');
-- ERROR: Invalid workflow state transition
```

### Missing Permissions

```sql
-- Try to approve without manager role
SELECT procurement.approve_by_manager('requisition-uuid');
-- ERROR: Insufficient permissions
```

## Testing Complex Workflows

SpecQL generates comprehensive workflow tests:

```sql
-- Run workflow tests
SELECT * FROM runtests('procurement.workflow_test');

-- Example test output:
-- ok 1 - submit_requisition validates draft status
-- ok 2 - submit_requisition updates status and timestamps
-- ok 3 - approve_by_manager handles small amounts
-- ok 4 - approve_by_manager escalates large amounts
-- ok 5 - approve_budget checks department budget
-- ok 6 - final_approval creates purchase order
-- ok 7 - reject_requisition updates status
-- ok 8 - workflow maintains audit trail
```

## Advanced Workflow Patterns

### Parallel Approvals

```yaml
actions:
  - name: parallel_approval
    pattern: composite/workflow_orchestrator
    workflow:
      - step: request_approvals
        parallel:
          - notify: manager "Approval needed"
          - notify: budget_approver "Budget check needed"
          - notify: legal "Legal review needed"

      - step: wait_for_all_approvals
        condition: "manager_approved AND budget_approved AND legal_approved"

      - step: finalize_approval
        action: update
        entity: Requisition
        fields: [status: 'approved']
```

### Retry Logic

```yaml
actions:
  - name: submit_with_retry
    pattern: composite/retry_orchestrator
    max_attempts: 3
    backoff_seconds: 60
    workflow:
      - step: attempt_submission
        action: call_external_api
        on_failure: retry

      - step: handle_failure
        condition: "attempts >= max_attempts"
        action: update
        entity: Requisition
        fields: [status: 'submission_failed']
```

## Key Benefits

✅ **Process Automation**: Complex workflows executed reliably
✅ **Business Logic**: Conditional logic and approvals built-in
✅ **Audit Trail**: Complete history of workflow execution
✅ **Error Handling**: Robust failure recovery and notifications
✅ **Scalability**: Handles high-volume workflow processing
✅ **Maintainability**: Workflow logic defined declaratively

## Common Use Cases

- **Procurement**: Purchase requisitions, approvals, vendor selection
- **HR**: Employee onboarding, leave approvals, expense reports
- **Content**: Article publishing, review processes, approvals
- **Financial**: Loan applications, credit approvals, transaction processing
- **IT**: Change management, incident response, deployment approvals

## Next Steps

- Add [saga patterns](../advanced/saga-pattern.md) for distributed workflow coordination
- Implement [event-driven patterns](../advanced/event-driven.md) for workflow triggers
- Use [batch operations](batch-operations.md) for bulk workflow processing

---

**See Also:**
- [Multi-Entity Operations](multi-entity.md)
- [Batch Operations](batch-operations.md)
- [Workflow Patterns](../../guides/mutation-patterns/workflows.md)