-- Seed basic patterns for testing

SET search_path TO pattern_library;

-- Pattern 1: Audit Trail
INSERT INTO domain_patterns (name, category, description, parameters, implementation, source_type)
VALUES (
    'audit_trail',
    'audit',
    'Track created_at, updated_at, deleted_at timestamps for record auditing',
    '{"entity": {"type": "string", "required": true, "description": "Target entity name"}}'::jsonb,
    '{
        "fields": [
            {"name": "created_at", "type": "timestamp", "default": "now()", "description": "Record creation time"},
            {"name": "updated_at", "type": "timestamp", "default": "now()", "description": "Last update time"},
            {"name": "deleted_at", "type": "timestamp", "description": "Soft delete timestamp"}
        ]
    }'::jsonb,
    'manual'
);

-- Pattern 2: Soft Delete
INSERT INTO domain_patterns (name, category, description, parameters, implementation, source_type)
VALUES (
    'soft_delete',
    'audit',
    'Mark records as deleted without physical removal',
    '{"entity": {"type": "string", "required": true}}'::jsonb,
    '{
        "fields": [
            {"name": "deleted_at", "type": "timestamp", "description": "Soft delete timestamp"},
            {"name": "deleted_by", "type": "ref(User)", "description": "User who deleted"}
        ],
        "actions": [
            {
                "name": "soft_delete",
                "steps": [
                    {"validate": "deleted_at IS NULL"},
                    {"update": "{{entity}} SET deleted_at = now(), deleted_by = current_user_id"}
                ]
            },
            {
                "name": "restore",
                "steps": [
                    {"validate": "deleted_at IS NOT NULL"},
                    {"update": "{{entity}} SET deleted_at = NULL, deleted_by = NULL"}
                ]
            }
        ]
    }'::jsonb,
    'manual'
);

-- Pattern 3: State Machine
INSERT INTO domain_patterns (name, category, description, parameters, implementation, source_type)
VALUES (
    'state_machine',
    'state_machine',
    'Finite state machine with configurable states and transitions',
    '{
        "entity": {"type": "string", "required": true},
        "states": {"type": "array", "default": ["draft", "active", "archived"], "description": "Valid states"},
        "initial_state": {"type": "string", "default": "draft"}
    }'::jsonb,
    '{
        "fields": [
            {"name": "status", "type": "enum({{states}})", "default": "{{initial_state}}"},
            {"name": "status_changed_at", "type": "timestamp"},
            {"name": "previous_status", "type": "enum({{states}})"}
        ],
        "actions": [
            {
                "name": "transition_state",
                "steps": [
                    {"validate": "new_status IN {{states}}"},
                    {"update": "{{entity}} SET previous_status = status, status = new_status, status_changed_at = now()"}
                ]
            }
        ]
    }'::jsonb,
    'manual'
);

-- Pattern 4: Approval Workflow
INSERT INTO domain_patterns (name, category, description, parameters, implementation, source_type)
VALUES (
    'approval_workflow',
    'workflow',
    'Two-stage approval workflow: pending -> approved/rejected',
    '{
        "entity": {"type": "string", "required": true},
        "approver_role": {"type": "string", "default": "manager"}
    }'::jsonb,
    '{
        "fields": [
            {"name": "approval_status", "type": "enum(pending, approved, rejected)", "default": "pending"},
            {"name": "approved_by", "type": "ref(User)"},
            {"name": "approved_at", "type": "timestamp"},
            {"name": "rejection_reason", "type": "text"}
        ],
        "actions": [
            {
                "name": "approve",
                "steps": [
                    {"validate": "approval_status = ''pending''"},
                    {"validate": "current_user_has_role(''{{approver_role}}'')"},
                    {"update": "{{entity}} SET approval_status = ''approved'', approved_by = current_user_id, approved_at = now()"},
                    {"notify": "submitter", "template": "approval_granted"}
                ]
            },
            {
                "name": "reject",
                "steps": [
                    {"validate": "approval_status = ''pending''"},
                    {"validate": "current_user_has_role(''{{approver_role}}'')"},
                    {"update": "{{entity}} SET approval_status = ''rejected'', rejection_reason = :reason"},
                    {"notify": "submitter", "template": "approval_rejected"}
                ]
            }
        ]
    }'::jsonb,
    'manual'
);

-- Pattern 5: Validation Chain
INSERT INTO domain_patterns (name, category, description, parameters, implementation, source_type)
VALUES (
    'validation_chain',
    'validation',
    'Sequential validation steps with error accumulation',
    '{"entity": {"type": "string", "required": true}}'::jsonb,
    '{
        "actions": [
            {
                "name": "validate_entity",
                "steps": [
                    {"validate": "field1 IS NOT NULL", "error": "Field1 is required"},
                    {"validate": "field2 > 0", "error": "Field2 must be positive"},
                    {"validate": "field3 IN (''valid1'', ''valid2'')", "error": "Invalid field3 value"}
                ]
            }
        ]
    }'::jsonb,
    'manual'
);

-- Display seeded patterns
SELECT name, category, description FROM domain_patterns;