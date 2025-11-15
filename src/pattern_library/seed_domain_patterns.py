"""Seed domain patterns for Tier 2"""

from .api import PatternLibrary


def seed_state_machine_pattern(library: PatternLibrary):
    """Seed state machine domain pattern"""

    library.add_domain_pattern(
        name="state_machine",
        category="workflow",
        description="State machine with transitions, guards, and audit trail",
        parameters={
            "entity": {"type": "string", "required": True},
            "states": {"type": "array", "required": True, "description": "List of valid states"},
            "transitions": {"type": "object", "required": True, "description": "Allowed state transitions"},
            "guards": {"type": "object", "required": False, "description": "Validation rules per transition"},
            "initial_state": {"type": "string", "required": False, "description": "Default initial state"}
        },
        implementation={
            "fields": [
                {
                    "name": "state",
                    "type": "enum",
                    "values": ["{{ states | join('\", \"') }}"],
                    "default": "{{ initial_state or states[0] }}",
                    "required": True
                },
                {
                    "name": "state_changed_at",
                    "type": "timestamp",
                    "default": "NOW()"
                },
                {
                    "name": "state_changed_by",
                    "type": "uuid"
                }
            ],
            "actions": [
                {
                    "name": "transition_to",
                    "parameters": [
                        {"name": "id", "type": "uuid"},
                        {"name": "target_state", "type": "text"},
                        {"name": "user_id", "type": "uuid"}
                    ],
                    "steps": [
                        {
                            "type": "query",
                            "sql": "SELECT state FROM tb_{{ entity }} WHERE id = $id",
                            "into": "current_state"
                        },
                        {
                            "type": "validate",
                            "condition": "target_state IN {{ states }}",
                            "error": "Invalid target state"
                        },
                        {
                            "type": "validate",
                            "condition": "transition_allowed(current_state, target_state)",
                            "error": "Transition not allowed"
                        },
                        {
                            "type": "update",
                            "entity": "{{ entity }}",
                            "where": "id = $id",
                            "fields": {
                                "state": "$target_state",
                                "state_changed_at": "NOW()",
                                "state_changed_by": "$user_id"
                            }
                        },
                        {
                            "type": "insert",
                            "entity": "{{ entity }}_state_history",
                            "fields": {
                                "entity_id": "$id",
                                "from_state": "$current_state",
                                "to_state": "$target_state",
                                "changed_by": "$user_id",
                                "changed_at": "NOW()"
                            }
                        }
                    ]
                }
            ],
            "tables": [
                {
                    "name": "{{ entity }}_state_history",
                    "fields": [
                        {"name": "pk_{{ entity }}_state_history", "type": "integer", "primary_key": True},
                        {"name": "entity_id", "type": "uuid"},
                        {"name": "from_state", "type": "text"},
                        {"name": "to_state", "type": "text"},
                        {"name": "changed_by", "type": "uuid"},
                        {"name": "changed_at", "type": "timestamp", "default": "NOW()"}
                    ]
                }
            ]
        },
        tags="workflow,state,transition,audit",
        icon="🔄"
    )

    print("✅ Seeded state_machine pattern")


def seed_audit_trail_pattern(library: PatternLibrary):
    """Seed audit trail domain pattern"""

    library.add_domain_pattern(
        name="audit_trail",
        category="audit",
        description="Automatic audit trail tracking who created/updated and when",
        parameters={
            "entity": {"type": "string", "required": True},
            "track_versions": {"type": "boolean", "required": False, "default": True}
        },
        implementation={
            "fields": [
                {"name": "created_at", "type": "timestamp", "default": "NOW()", "required": True},
                {"name": "created_by", "type": "uuid", "required": True},
                {"name": "updated_at", "type": "timestamp", "default": "NOW()", "required": True},
                {"name": "updated_by", "type": "uuid"},
                {"name": "version", "type": "integer", "default": 1}
            ],
            "triggers": [
                {
                    "event": "before_insert",
                    "action": "set_created_fields",
                    "logic": {
                        "steps": [
                            {"type": "assign", "variable": "created_at", "value": "NOW()"},
                            {"type": "assign", "variable": "created_by", "value": "$current_user_id"},
                            {"type": "assign", "variable": "version", "value": 1}
                        ]
                    }
                },
                {
                    "event": "before_update",
                    "action": "set_updated_fields",
                    "logic": {
                        "steps": [
                            {"type": "assign", "variable": "updated_at", "value": "NOW()"},
                            {"type": "assign", "variable": "updated_by", "value": "$current_user_id"},
                            {"type": "assign", "variable": "version", "value": "version + 1"}
                        ]
                    }
                }
            ]
        },
        tags="audit,tracking,version,history",
        icon="📋"
    )

    print("✅ Seeded audit_trail pattern")


def seed_soft_delete_pattern(library: PatternLibrary):
    """Seed soft delete domain pattern"""

    library.add_domain_pattern(
        name="soft_delete",
        category="data_management",
        description="Soft delete pattern with deleted_at timestamp",
        parameters={
            "entity": {"type": "string", "required": True}
        },
        implementation={
            "fields": [
                {"name": "deleted_at", "type": "timestamp", "nullable": True},
                {"name": "deleted_by", "type": "uuid", "nullable": True}
            ],
            "actions": [
                {
                    "name": "soft_delete",
                    "parameters": [
                        {"name": "id", "type": "uuid"},
                        {"name": "user_id", "type": "uuid"}
                    ],
                    "steps": [
                        {
                            "type": "validate",
                            "condition": "deleted_at IS NULL",
                            "error": "{{ entity }} already deleted"
                        },
                        {
                            "type": "update",
                            "entity": "{{ entity }}",
                            "where": "id = $id",
                            "fields": {
                                "deleted_at": "NOW()",
                                "deleted_by": "$user_id"
                            }
                        }
                    ]
                },
                {
                    "name": "restore",
                    "parameters": [
                        {"name": "id", "type": "uuid"}
                    ],
                    "steps": [
                        {
                            "type": "validate",
                            "condition": "deleted_at IS NOT NULL",
                            "error": "{{ entity }} not deleted"
                        },
                        {
                            "type": "update",
                            "entity": "{{ entity }}",
                            "where": "id = $id",
                            "fields": {
                                "deleted_at": "NULL",
                                "deleted_by": "NULL"
                            }
                        }
                    ]
                }
            ],
            "views": [
                {
                    "name": "{{ entity }}_active",
                    "query": "SELECT * FROM tb_{{ entity }} WHERE deleted_at IS NULL"
                }
            ]
        },
        tags="delete,soft,restore,data_management",
        icon="🗑️"
    )

    print("✅ Seeded soft_delete pattern")


def seed_validation_chain_pattern(library: PatternLibrary):
    """Seed validation chain domain pattern"""

    library.add_domain_pattern(
        name="validation_chain",
        category="validation",
        description="Chainable validation rules with conditional execution",
        parameters={
            "entity": {"type": "string", "required": True},
            "rules": {"type": "array", "required": True, "description": "List of validation rules"},
            "fail_fast": {"type": "boolean", "required": False, "default": False, "description": "Stop on first failure"}
        },
        implementation={
            "actions": [
                {
                    "name": "validate_chain",
                    "parameters": [
                        {"name": "data", "type": "object"}
                    ],
                    "steps": [
                        {
                            "type": "assign",
                            "variable": "validation_errors",
                            "value": []
                        },
                        {
                            "type": "foreach",
                            "collection": "{{ rules }}",
                            "item": "rule",
                            "steps": [
                                {
                                    "type": "if",
                                    "condition": "$rule.condition IS NULL OR evaluate_condition($rule.condition, $data)",
                                    "then": [
                                        {
                                            "type": "call",
                                            "function": "validate_rule",
                                            "args": {"rule": "$rule", "data": "$data"},
                                            "into": "rule_result"
                                        },
                                        {
                                            "type": "if",
                                            "condition": "$rule_result.valid == false",
                                            "then": [
                                                {
                                                    "type": "append",
                                                    "to": "validation_errors",
                                                    "value": "$rule_result.error"
                                                },
                                                {
                                                    "type": "if",
                                                    "condition": "{{ fail_fast }}",
                                                    "then": [
                                                        {"type": "break"}
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "type": "if",
                            "condition": "len($validation_errors) > 0",
                            "then": [
                                {
                                    "type": "raise",
                                    "error": "Validation failed"
                                }
                            ]
                        }
                    ]
                }
            ],
            "functions": [
                {
                    "name": "validate_rule",
                    "parameters": ["rule", "data"],
                    "logic": {
                        "steps": [
                            {
                                "type": "switch",
                                "expression": "$rule.type",
                                "cases": {
                                    "required": [
                                        {
                                            "type": "if",
                                            "condition": "$data.get($rule.field) IS NULL OR $data.get($rule.field) == ''",
                                            "then": [
                                                {"type": "return", "value": {"valid": False, "error": "$rule.field is required"}}
                                            ],
                                            "else": [
                                                {"type": "return", "value": {"valid": True}}
                                            ]
                                        }
                                    ],
                                    "email": [
                                        {
                                            "type": "if",
                                            "condition": "NOT is_valid_email($data.get($rule.field))",
                                            "then": [
                                                {"type": "return", "value": {"valid": False, "error": "$rule.field must be a valid email"}}
                                            ],
                                            "else": [
                                                {"type": "return", "value": {"valid": True}}
                                            ]
                                        }
                                    ],
                                    "length": [
                                        {
                                            "type": "assign",
                                            "variable": "value",
                                            "value": "$data.get($rule.field, '')"
                                        },
                                        {
                                            "type": "if",
                                            "condition": "$rule.min AND len($value) < $rule.min",
                                            "then": [
                                                {"type": "return", "value": {"valid": False, "error": "$rule.field must be at least $rule.min characters"}}
                                            ]
                                        },
                                        {
                                            "type": "if",
                                            "condition": "$rule.max AND len($value) > $rule.max",
                                            "then": [
                                                {"type": "return", "value": {"valid": False, "error": "$rule.field must be at most $rule.max characters"}}
                                            ]
                                        },
                                        {"type": "return", "value": {"valid": True}}
                                    ],
                                    "range": [
                                        {
                                            "type": "assign",
                                            "variable": "value",
                                            "value": "$data.get($rule.field)"
                                        },
                                        {
                                            "type": "if",
                                            "condition": "$rule.min AND $value < $rule.min",
                                            "then": [
                                                {"type": "return", "value": {"valid": False, "error": "$rule.field must be at least $rule.min"}}
                                            ]
                                        },
                                        {
                                            "type": "if",
                                            "condition": "$rule.max AND $value > $rule.max",
                                            "then": [
                                                {"type": "return", "value": {"valid": False, "error": "$rule.field must be at most $rule.max"}}
                                            ]
                                        },
                                        {"type": "return", "value": {"valid": True}}
                                    ],
                                    "custom": [
                                        {
                                            "type": "call",
                                            "function": "$rule.validator",
                                            "args": {"value": "$data.get($rule.field)", "data": "$data"},
                                            "into": "custom_result"
                                        },
                                        {"type": "return", "value": "$custom_result"}
                                    ]
                                },
                                "default": [
                                    {"type": "return", "value": {"valid": False, "error": "Unknown validation type"}}
                                ]
                            }
                        ]
                    }
                }
            ]
        },
        tags="validation,chain,rules,conditional",
        icon="🔗"
    )

    print("✅ Seeded validation_chain pattern")


def seed_approval_workflow_pattern(library: PatternLibrary):
    """Seed approval workflow domain pattern"""

    library.add_domain_pattern(
        name="approval_workflow",
        category="workflow",
        description="Multi-stage approval process with reviewers and escalation",
        parameters={
            "entity": {"type": "string", "required": True},
            "stages": {"type": "array", "required": True, "description": "Approval stages with reviewers"},
            "auto_approve_threshold": {"type": "number", "required": False, "description": "Auto-approve if amount below threshold"},
            "escalation_days": {"type": "number", "required": False, "default": 7, "description": "Days before escalation"}
        },
        implementation={
            "fields": [
                {"name": "approval_status", "type": "enum", "values": ["pending", "approved", "rejected", "escalated"], "default": "pending"},
                {"name": "current_stage", "type": "integer", "default": 0},
                {"name": "approved_by", "type": "array", "default": []},
                {"name": "rejected_by", "type": "array", "default": []},
                {"name": "approval_started_at", "type": "timestamp"},
                {"name": "approval_completed_at", "type": "timestamp"}
            ],
            "actions": [
                {
                    "name": "start_approval",
                    "parameters": [
                        {"name": "id", "type": "uuid"},
                        {"name": "initiator_id", "type": "uuid"}
                    ],
                    "steps": [
                        {
                            "type": "validate",
                            "condition": "approval_status == 'pending'",
                            "error": "Approval already started"
                        },
                        {
                            "type": "if",
                            "condition": "{{ auto_approve_threshold }} AND get_amount({{ entity }}, id) < {{ auto_approve_threshold }}",
                            "then": [
                                {
                                    "type": "update",
                                    "entity": "{{ entity }}",
                                    "where": "id = $id",
                                    "fields": {
                                        "approval_status": "approved",
                                        "approved_by": "[$initiator_id]",
                                        "approval_started_at": "NOW()",
                                        "approval_completed_at": "NOW()"
                                    }
                                },
                                {
                                    "type": "insert",
                                    "entity": "{{ entity }}_approval_history",
                                    "fields": {
                                        "entity_id": "$id",
                                        "action": "auto_approved",
                                        "stage": 0,
                                        "user_id": "$initiator_id",
                                        "timestamp": "NOW()",
                                        "notes": "Auto-approved due to low amount"
                                    }
                                }
                            ],
                            "else": [
                                {
                                    "type": "update",
                                    "entity": "{{ entity }}",
                                    "where": "id = $id",
                                    "fields": {
                                        "approval_status": "pending",
                                        "current_stage": 1,
                                        "approval_started_at": "NOW()"
                                    }
                                },
                                {
                                    "type": "call",
                                    "function": "notify_reviewers",
                                    "args": {"entity_id": "$id", "stage": 1}
                                }
                            ]
                        }
                    ]
                },
                {
                    "name": "approve_stage",
                    "parameters": [
                        {"name": "id", "type": "uuid"},
                        {"name": "reviewer_id", "type": "uuid"},
                        {"name": "notes", "type": "text"}
                    ],
                    "steps": [
                        {
                            "type": "query",
                            "sql": "SELECT current_stage, stages FROM tb_{{ entity }} WHERE id = $id",
                            "into": "current"
                        },
                        {
                            "type": "validate",
                            "condition": "current.current_stage > 0",
                            "error": "Approval not started"
                        },
                        {
                            "type": "validate",
                            "condition": "is_reviewer_for_stage(reviewer_id, current.current_stage, {{ stages }})",
                            "error": "Not authorized to review this stage"
                        },
                        {
                            "type": "update",
                            "entity": "{{ entity }}",
                            "where": "id = $id",
                            "fields": {
                                "approved_by": "approved_by + [$reviewer_id]"
                            }
                        },
                        {
                            "type": "insert",
                            "entity": "{{ entity }}_approval_history",
                            "fields": {
                                "entity_id": "$id",
                                "action": "approved",
                                "stage": "$current.current_stage",
                                "user_id": "$reviewer_id",
                                "timestamp": "NOW()",
                                "notes": "$notes"
                            }
                        },
                        {
                            "type": "if",
                            "condition": "all_reviewers_approved(id, current.current_stage, {{ stages }})",
                            "then": [
                                {
                                    "type": "if",
                                    "condition": "current.current_stage >= len({{ stages }})",
                                    "then": [
                                        {
                                            "type": "update",
                                            "entity": "{{ entity }}",
                                            "where": "id = $id",
                                            "fields": {
                                                "approval_status": "approved",
                                                "approval_completed_at": "NOW()"
                                            }
                                        }
                                    ],
                                    "else": [
                                        {
                                            "type": "update",
                                            "entity": "{{ entity }}",
                                            "where": "id = $id",
                                            "fields": {
                                                "current_stage": "current_stage + 1"
                                            }
                                        },
                                        {
                                            "type": "call",
                                            "function": "notify_reviewers",
                                            "args": {"entity_id": "$id", "stage": "current.current_stage + 1"}
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    "name": "reject_approval",
                    "parameters": [
                        {"name": "id", "type": "uuid"},
                        {"name": "reviewer_id", "type": "uuid"},
                        {"name": "notes", "type": "text"}
                    ],
                    "steps": [
                        {
                            "type": "update",
                            "entity": "{{ entity }}",
                            "where": "id = $id",
                            "fields": {
                                "approval_status": "rejected",
                                "rejected_by": "rejected_by + [$reviewer_id]",
                                "approval_completed_at": "NOW()"
                            }
                        },
                        {
                            "type": "insert",
                            "entity": "{{ entity }}_approval_history",
                            "fields": {
                                "entity_id": "$id",
                                "action": "rejected",
                                "stage": "$current_stage",
                                "user_id": "$reviewer_id",
                                "timestamp": "NOW()",
                                "notes": "$notes"
                            }
                        }
                    ]
                }
            ],
            "tables": [
                {
                    "name": "{{ entity }}_approval_history",
                    "fields": [
                        {"name": "pk_{{ entity }}_approval_history", "type": "integer", "primary_key": True},
                        {"name": "entity_id", "type": "uuid"},
                        {"name": "action", "type": "enum", "values": ["started", "approved", "rejected", "escalated"]},
                        {"name": "stage", "type": "integer"},
                        {"name": "user_id", "type": "uuid"},
                        {"name": "timestamp", "type": "timestamp", "default": "NOW()"},
                        {"name": "notes", "type": "text"}
                    ]
                }
            ],
            "triggers": [
                {
                    "event": "after_update",
                    "condition": "old.approval_status != new.approval_status",
                    "action": "notify_status_change"
                }
            ]
        },
        tags="approval,workflow,review,stages,escalation",
        icon="✅"
    )

    print("✅ Seeded approval_workflow pattern")


def seed_hierarchy_navigation_pattern(library: PatternLibrary):
    """Seed hierarchy navigation domain pattern"""

    library.add_domain_pattern(
        name="hierarchy_navigation",
        category="data_structure",
        description="Parent-child relationships with recursive queries and navigation",
        parameters={
            "entity": {"type": "string", "required": True},
            "parent_field": {"type": "string", "required": False, "default": "parent_id", "description": "Field name for parent reference"},
            "max_depth": {"type": "integer", "required": False, "default": 10, "description": "Maximum hierarchy depth"},
            "enable_circular_check": {"type": "boolean", "required": False, "default": True, "description": "Prevent circular references"}
        },
        implementation={
            "fields": [
                {"name": "{{ parent_field }}", "type": "uuid", "nullable": True},
                {"name": "hierarchy_level", "type": "integer", "default": 0},
                {"name": "hierarchy_path", "type": "array", "default": []},
                {"name": "is_leaf", "type": "boolean", "default": True}
            ],
            "actions": [
                {
                    "name": "get_children",
                    "parameters": [
                        {"name": "id", "type": "uuid"},
                        {"name": "depth", "type": "integer", "default": 1}
                    ],
                    "steps": [
                        {
                            "type": "query",
                            "sql": """
                                WITH RECURSIVE hierarchy AS (
                                    SELECT id, {{ parent_field }}, hierarchy_level, 0 as depth
                                    FROM tb_{{ entity }}
                                    WHERE id = $id

                                    UNION ALL

                                    SELECT c.id, c.{{ parent_field }}, c.hierarchy_level, h.depth + 1
                                    FROM tb_{{ entity }} c
                                    JOIN hierarchy h ON c.{{ parent_field }} = h.id
                                    WHERE h.depth < $depth
                                )
                                SELECT * FROM hierarchy WHERE id != $id
                            """,
                            "into": "children"
                        },
                        {"type": "return", "value": "$children"}
                    ]
                },
                {
                    "name": "get_parent_chain",
                    "parameters": [
                        {"name": "id", "type": "uuid"}
                    ],
                    "steps": [
                        {
                            "type": "query",
                            "sql": """
                                WITH RECURSIVE ancestry AS (
                                    SELECT id, {{ parent_field }}, hierarchy_level
                                    FROM tb_{{ entity }}
                                    WHERE id = $id

                                    UNION ALL

                                    SELECT p.id, p.{{ parent_field }}, p.hierarchy_level
                                    FROM tb_{{ entity }} p
                                    JOIN ancestry a ON p.id = a.{{ parent_field }}
                                )
                                SELECT * FROM ancestry WHERE id != $id ORDER BY hierarchy_level
                            """,
                            "into": "parents"
                        },
                        {"type": "return", "value": "$parents"}
                    ]
                },
                {
                    "name": "move_node",
                    "parameters": [
                        {"name": "id", "type": "uuid"},
                        {"name": "new_parent_id", "type": "uuid"}
                    ],
                    "steps": [
                        {
                            "type": "validate",
                            "condition": "$new_parent_id IS NULL OR NOT is_descendant($id, $new_parent_id)",
                            "error": "Cannot move node under its own descendant"
                        },
                        {
                            "type": "query",
                            "sql": "SELECT hierarchy_level FROM tb_{{ entity }} WHERE id = $new_parent_id",
                            "into": "parent_level"
                        },
                        {
                            "type": "update",
                            "entity": "{{ entity }}",
                            "where": "id = $id",
                            "fields": {
                                "{{ parent_field }}": "$new_parent_id",
                                "hierarchy_level": "$parent_level.hierarchy_level + 1"
                            }
                        },
                        {
                            "type": "call",
                            "function": "update_hierarchy_path",
                            "args": {"node_id": "$id"}
                        },
                        {
                            "type": "call",
                            "function": "update_descendant_levels",
                            "args": {"root_id": "$id"}
                        }
                    ]
                },
                {
                    "name": "get_tree",
                    "parameters": [
                        {"name": "root_id", "type": "uuid"}
                    ],
                    "steps": [
                        {
                            "type": "query",
                            "sql": """
                                WITH RECURSIVE tree AS (
                                    SELECT id, {{ parent_field }}, hierarchy_level, hierarchy_path,
                                           CAST(id AS TEXT) as path_string
                                    FROM tb_{{ entity }}
                                    WHERE id = $root_id

                                    UNION ALL

                                    SELECT c.id, c.{{ parent_field }}, c.hierarchy_level, c.hierarchy_path,
                                           t.path_string || '/' || CAST(c.id AS TEXT)
                                    FROM tb_{{ entity }} c
                                    JOIN tree t ON c.{{ parent_field }} = t.id
                                )
                                SELECT *,
                                       LENGTH(path_string) - LENGTH(REPLACE(path_string, '/', '')) as depth
                                FROM tree
                                ORDER BY path_string
                            """,
                            "into": "tree_data"
                        },
                        {"type": "return", "value": "$tree_data"}
                    ]
                }
            ],
            "functions": [
                {
                    "name": "is_descendant",
                    "parameters": ["ancestor_id", "descendant_id"],
                    "logic": {
                        "steps": [
                            {
                                "type": "query",
                                "sql": """
                                    WITH RECURSIVE descendants AS (
                                        SELECT id, {{ parent_field }}
                                        FROM tb_{{ entity }}
                                        WHERE id = $ancestor_id

                                        UNION ALL

                                        SELECT c.id, c.{{ parent_field }}
                                        FROM tb_{{ entity }} c
                                        JOIN descendants d ON c.{{ parent_field }} = d.id
                                    )
                                    SELECT COUNT(*) > 0 as is_descendant
                                    FROM descendants
                                    WHERE id = $descendant_id
                                """,
                                "into": "result"
                            },
                            {"type": "return", "value": "$result.is_descendant"}
                        ]
                    }
                },
                {
                    "name": "update_hierarchy_path",
                    "parameters": ["node_id"],
                    "logic": {
                        "steps": [
                            {
                                "type": "call",
                                "function": "get_parent_chain",
                                "args": {"id": "$node_id"},
                                "into": "parents"
                            },
                            {
                                "type": "assign",
                                "variable": "path",
                                "value": "[p.id for p in $parents] + [$node_id]"
                            },
                            {
                                "type": "update",
                                "entity": "{{ entity }}",
                                "where": "id = $node_id",
                                "fields": {"hierarchy_path": "$path"}
                            }
                        ]
                    }
                },
                {
                    "name": "update_descendant_levels",
                    "parameters": ["root_id"],
                    "logic": {
                        "steps": [
                            {
                                "type": "query",
                                "sql": "SELECT hierarchy_level FROM tb_{{ entity }} WHERE id = $root_id",
                                "into": "root_level"
                            },
                            {
                                "type": "query",
                                "sql": """
                                    WITH RECURSIVE descendants AS (
                                        SELECT id, {{ parent_field }}, 0 as relative_level
                                        FROM tb_{{ entity }}
                                        WHERE id = $root_id

                                        UNION ALL

                                        SELECT c.id, c.{{ parent_field }}, d.relative_level + 1
                                        FROM tb_{{ entity }} c
                                        JOIN descendants d ON c.{{ parent_field }} = d.id
                                    )
                                    SELECT id, $root_level.hierarchy_level + relative_level as new_level
                                    FROM descendants
                                    WHERE id != $root_id
                                """,
                                "into": "updates"
                            },
                            {
                                "type": "foreach",
                                "collection": "$updates",
                                "item": "update",
                                "steps": [
                                    {
                                        "type": "update",
                                        "entity": "{{ entity }}",
                                        "where": "id = $update.id",
                                        "fields": {"hierarchy_level": "$update.new_level"}
                                    }
                                ]
                            }
                        ]
                    }
                }
            ],
            "triggers": [
                {
                    "event": "before_insert",
                    "action": "validate_hierarchy",
                    "logic": {
                        "steps": [
                            {
                                "type": "if",
                                "condition": "{{ enable_circular_check }} AND {{ parent_field }} IS NOT NULL",
                                "then": [
                                    {
                                        "type": "validate",
                                        "condition": "NOT is_descendant(id, {{ parent_field }})",
                                        "error": "Circular reference detected in hierarchy"
                                    }
                                ]
                            },
                            {
                                "type": "if",
                                "condition": "{{ parent_field }} IS NOT NULL",
                                "then": [
                                    {
                                        "type": "query",
                                        "sql": "SELECT hierarchy_level FROM tb_{{ entity }} WHERE id = {{ parent_field }}",
                                        "into": "parent"
                                    },
                                    {
                                        "type": "assign",
                                        "variable": "hierarchy_level",
                                        "value": "$parent.hierarchy_level + 1"
                                    },
                                    {
                                        "type": "validate",
                                        "condition": "$hierarchy_level <= {{ max_depth }}",
                                        "error": "Maximum hierarchy depth exceeded"
                                    }
                                ],
                                "else": [
                                    {
                                        "type": "assign",
                                        "variable": "hierarchy_level",
                                        "value": 0
                                    }
                                ]
                            }
                        ]
                    }
                },
                {
                    "event": "after_insert",
                    "action": "update_hierarchy_path"
                }
            ],
            "indexes": [
                {"fields": ["{{ parent_field }}"], "name": "idx_{{ entity }}_{{ parent_field }}"},
                {"fields": ["hierarchy_level"], "name": "idx_{{ entity }}_hierarchy_level"},
                {"fields": ["hierarchy_path"], "name": "idx_{{ entity }}_hierarchy_path", "type": "gin"}
            ]
        },
        tags="hierarchy,tree,parent-child,recursive,navigation",
        icon="🌳"
    )

    print("✅ Seeded hierarchy_navigation pattern")


def seed_computed_fields_pattern(library: PatternLibrary):
    """Seed computed fields domain pattern"""

    library.add_domain_pattern(
        name="computed_fields",
        category="data_processing",
        description="Auto-calculated fields with dependency tracking",
        parameters={
            "entity": {"type": "string", "required": True},
            "computed_fields": {"type": "object", "required": True, "description": "Field definitions with formulas"}
        },
        implementation={
            "actions": [
                {
                    "name": "recalculate_field",
                    "parameters": [
                        {"name": "id", "type": "uuid"},
                        {"name": "field_name", "type": "text"}
                    ],
                    "steps": [
                        {
                            "type": "validate",
                            "condition": "$field_name IN {{ computed_fields }}",
                            "error": "Field is not computed"
                        },
                        {
                            "type": "query",
                            "sql": "SELECT * FROM tb_{{ entity }} WHERE id = $id",
                            "into": "record"
                        },
                        {
                            "type": "call",
                            "function": "compute_field_value",
                            "args": {"record": "$record", "field_name": "$field_name", "formula": "{{ computed_fields }}[$field_name]"},
                            "into": "computed_value"
                        },
                        {
                            "type": "update",
                            "entity": "{{ entity }}",
                            "where": "id = $id",
                            "fields": {"$field_name": "$computed_value"}
                        }
                    ]
                },
                {
                    "name": "recalculate_all_fields",
                    "parameters": [
                        {"name": "id", "type": "uuid"}
                    ],
                    "steps": [
                        {
                            "type": "query",
                            "sql": "SELECT * FROM tb_{{ entity }} WHERE id = $id",
                            "into": "record"
                        },
                        {
                            "type": "foreach",
                            "collection": "{{ computed_fields }}",
                            "item": "field_def",
                            "steps": [
                                {
                                    "type": "call",
                                    "function": "compute_field_value",
                                    "args": {"record": "$record", "field_name": "$field_def.key", "formula": "$field_def.value"},
                                    "into": "computed_value"
                                },
                                {
                                    "type": "update",
                                    "entity": "{{ entity }}",
                                    "where": "id = $id",
                                    "fields": {"$field_def.key": "$computed_value"}
                                }
                            ]
                        }
                    ]
                },
                {
                    "name": "bulk_recalculate",
                    "parameters": [
                        {"name": "where_clause", "type": "text", "default": "1=1"}
                    ],
                    "steps": [
                        {
                            "type": "query",
                            "sql": "SELECT id FROM tb_{{ entity }} WHERE $where_clause",
                            "into": "records"
                        },
                        {
                            "type": "foreach",
                            "collection": "$records",
                            "item": "record",
                            "steps": [
                                {
                                    "type": "call",
                                    "function": "recalculate_all_fields",
                                    "args": {"id": "$record.id"}
                                }
                            ]
                        }
                    ]
                }
            ],
            "functions": [
                {
                    "name": "compute_field_value",
                    "parameters": ["record", "field_name", "formula"],
                    "logic": {
                        "steps": [
                            {
                                "type": "switch",
                                "expression": "$formula.type",
                                "cases": {
                                    "expression": [
                                        {
                                            "type": "assign",
                                            "variable": "context",
                                            "value": "$record"
                                        },
                                        {
                                            "type": "call",
                                            "function": "evaluate_expression",
                                            "args": {"expression": "$formula.expression", "context": "$context"},
                                            "into": "result"
                                        },
                                        {"type": "return", "value": "$result"}
                                    ],
                                    "aggregate": [
                                        {
                                            "type": "query",
                                            "sql": "$formula.query",
                                            "into": "aggregated"
                                        },
                                        {"type": "return", "value": "$aggregated.value"}
                                    ],
                                    "lookup": [
                                        {
                                            "type": "query",
                                            "sql": "SELECT $formula.select_field FROM $formula.from_table WHERE $formula.where_field = $record.$formula.lookup_field",
                                            "into": "lookup_result"
                                        },
                                        {"type": "return", "value": "$lookup_result.$formula.select_field"}
                                    ],
                                    "concat": [
                                        {
                                            "type": "assign",
                                            "variable": "parts",
                                            "value": "[$record[field] for field in $formula.fields]"
                                        },
                                        {
                                            "type": "assign",
                                            "variable": "result",
                                            "value": "$formula.separator.join($parts)"
                                        },
                                        {"type": "return", "value": "$result"}
                                    ],
                                    "math": [
                                        {
                                            "type": "assign",
                                            "variable": "result",
                                            "value": "eval($formula.operation.replace('{field}', str($record.get($formula.field, 0))))"
                                        },
                                        {"type": "return", "value": "$result"}
                                    ]
                                },
                                "default": [
                                    {"type": "return", "value": None}
                                ]
                            }
                        ]
                    }
                },
                {
                    "name": "evaluate_expression",
                    "parameters": ["expression", "context"],
                    "logic": {
                        "steps": [
                            {
                                "type": "assign",
                                "variable": "safe_context",
                                "value": "{k: v for k, v in $context.items() if isinstance(v, (int, float, str, bool))}"
                            },
                            {
                                "type": "assign",
                                "variable": "result",
                                "value": "eval($expression, {'__builtins__': {}}, $safe_context)"
                            },
                            {"type": "return", "value": "$result"}
                        ]
                    }
                }
            ],
            "triggers": [
                {
                    "event": "after_insert",
                    "action": "compute_all_fields"
                },
                {
                    "event": "after_update",
                    "action": "recompute_dependent_fields",
                    "logic": {
                        "steps": [
                            {
                                "type": "assign",
                                "variable": "changed_fields",
                                "value": "[field for field in {{ computed_fields }}.keys() if old.get(field) != new.get(field)]"
                            },
                            {
                                "type": "foreach",
                                "collection": "{{ computed_fields }}",
                                "item": "field_def",
                                "steps": [
                                    {
                                        "type": "assign",
                                        "variable": "dependencies",
                                        "value": "get_field_dependencies($field_def.value)"
                                    },
                                    {
                                        "type": "if",
                                        "condition": "any(dep in $changed_fields for dep in $dependencies)",
                                        "then": [
                                            {
                                                "type": "call",
                                                "function": "recalculate_field",
                                                "args": {"id": "new.id", "field_name": "$field_def.key"}
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                }
            ]
        },
        tags="computed,calculated,auto,formula,expression",
        icon="🧮"
    )

    print("✅ Seeded computed_fields pattern")


def seed_search_optimization_pattern(library: PatternLibrary):
    """Seed search optimization domain pattern"""

    library.add_domain_pattern(
        name="search_optimization",
        category="search",
        description="Full-text search indexes and search functionality",
        parameters={
            "entity": {"type": "string", "required": True},
            "search_fields": {"type": "array", "required": True, "description": "Fields to include in search"},
            "search_vector_field": {"type": "string", "required": False, "default": "search_vector", "description": "Name of search vector field"},
            "enable_fuzzy_search": {"type": "boolean", "required": False, "default": True, "description": "Enable fuzzy matching"},
            "enable_autocomplete": {"type": "boolean", "required": False, "default": False, "description": "Enable autocomplete suggestions"}
        },
        implementation={
            "fields": [
                {"name": "{{ search_vector_field }}", "type": "tsvector"},
                {"name": "search_updated_at", "type": "timestamp"}
            ],
            "actions": [
                {
                    "name": "search",
                    "parameters": [
                        {"name": "query", "type": "text"},
                        {"name": "limit", "type": "integer", "default": 50},
                        {"name": "offset", "type": "integer", "default": 0},
                        {"name": "fuzzy", "type": "boolean", "default": "{{ enable_fuzzy_search }}"}
                    ],
                    "steps": [
                        {
                            "type": "assign",
                            "variable": "search_query",
                            "value": "$query"
                        },
                        {
                            "type": "if",
                            "condition": "$fuzzy",
                            "then": [
                                {
                                    "type": "assign",
                                    "variable": "search_query",
                                    "value": "to_tsquery('english', $query)"
                                }
                            ],
                            "else": [
                                {
                                    "type": "assign",
                                    "variable": "search_query",
                                    "value": "plainto_tsquery('english', $query)"
                                }
                            ]
                        },
                        {
                            "type": "query",
                            "sql": """
                                SELECT *,
                                       ts_rank({{ search_vector_field }}, $search_query) as rank,
                                       ts_headline('english', {{ search_fields | join(" || ' ' || ") }}, $search_query) as highlights
                                FROM tb_{{ entity }}
                                WHERE {{ search_vector_field }} @@ $search_query
                                ORDER BY rank DESC
                                LIMIT $limit OFFSET $offset
                            """,
                            "into": "results"
                        },
                        {"type": "return", "value": "$results"}
                    ]
                },
                {
                    "name": "autocomplete",
                    "parameters": [
                        {"name": "prefix", "type": "text"},
                        {"name": "limit", "type": "integer", "default": 10}
                    ],
                    "steps": [
                        {
                            "type": "query",
                            "sql": """
                                SELECT DISTINCT unnest(tsvector_to_array({{ search_vector_field }})) as suggestion
                                FROM tb_{{ entity }}
                                WHERE {{ search_vector_field }} @@ to_tsquery('english', $prefix || ':*')
                                ORDER BY suggestion
                                LIMIT $limit
                            """,
                            "into": "suggestions"
                        },
                        {"type": "return", "value": "$suggestions"}
                    ]
                },
                {
                    "name": "update_search_index",
                    "parameters": [
                        {"name": "id", "type": "uuid"}
                    ],
                    "steps": [
                        {
                            "type": "query",
                            "sql": "SELECT * FROM tb_{{ entity }} WHERE id = $id",
                            "into": "record"
                        },
                        {
                            "type": "assign",
                            "variable": "search_text",
                            "value": "{{ search_fields | join(\" || ' ' || \") | replace('record.', '') }}"
                        },
                        {
                            "type": "assign",
                            "variable": "search_vector",
                            "value": "to_tsvector('english', $search_text)"
                        },
                        {
                            "type": "update",
                            "entity": "{{ entity }}",
                            "where": "id = $id",
                            "fields": {
                                "{{ search_vector_field }}": "$search_vector",
                                "search_updated_at": "NOW()"
                            }
                        }
                    ]
                },
                {
                    "name": "rebuild_search_index",
                    "steps": [
                        {
                            "type": "query",
                            "sql": "SELECT id FROM tb_{{ entity }}",
                            "into": "all_records"
                        },
                        {
                            "type": "foreach",
                            "collection": "$all_records",
                            "item": "record",
                            "steps": [
                                {
                                    "type": "call",
                                    "function": "update_search_index",
                                    "args": {"id": "$record.id"}
                                }
                            ]
                        }
                    ]
                }
            ],
            "triggers": [
                {
                    "event": "after_insert",
                    "action": "update_search_index"
                },
                {
                    "event": "after_update",
                    "condition": "any(field in {{ search_fields }} for field in changed_fields)",
                    "action": "update_search_index"
                }
            ],
            "indexes": [
                {
                    "fields": ["{{ search_vector_field }}"],
                    "name": "idx_{{ entity }}_{{ search_vector_field }}",
                    "type": "gin"
                },
                {
                    "fields": ["search_updated_at"],
                    "name": "idx_{{ entity }}_search_updated_at"
                }
            ],
            "functions": [
                {
                    "name": "search_with_weights",
                    "parameters": ["query", "field_weights"],
                    "logic": {
                        "steps": [
                            {
                                "type": "assign",
                                "variable": "weighted_query",
                                "value": "''"
                            },
                            {
                                "type": "foreach",
                                "collection": "$field_weights",
                                "item": "weight_def",
                                "steps": [
                                    {
                                        "type": "assign",
                                        "variable": "weighted_query",
                                        "value": "$weighted_query + ' OR ' + $weight_def.field + ':(' + $query + ')'"
                                    }
                                ]
                            },
                            {
                                "type": "query",
                                "sql": """
                                    SELECT *,
                                           ts_rank_cd({{ search_vector_field }}, to_tsquery('english', $weighted_query)) as weighted_rank
                                    FROM tb_{{ entity }}
                                    WHERE {{ search_vector_field }} @@ to_tsquery('english', $weighted_query)
                                    ORDER BY weighted_rank DESC
                                """,
                                "into": "weighted_results"
                            },
                            {"type": "return", "value": "$weighted_results"}
                        ]
                    }
                }
            ]
        },
        tags="search,full-text,index,fuzzy,autocomplete",
        icon="🔍"
    )

    print("✅ Seeded search_optimization pattern")


def seed_internationalization_pattern(library: PatternLibrary):
    """Seed internationalization domain pattern"""

    library.add_domain_pattern(
        name="internationalization",
        category="localization",
        description="Multi-language field support with translations",
        parameters={
            "entity": {"type": "string", "required": True},
            "translatable_fields": {"type": "array", "required": True, "description": "Fields that need translation"},
            "default_locale": {"type": "string", "required": False, "default": "en", "description": "Default language code"},
            "supported_locales": {"type": "array", "required": False, "default": ["en"], "description": "Supported language codes"}
        },
        implementation={
            "tables": [
                {
                    "name": "{{ entity }}_translations",
                    "fields": [
                        {"name": "pk_{{ entity }}_translations", "type": "integer", "primary_key": True},
                        {"name": "entity_id", "type": "uuid"},
                        {"name": "locale", "type": "varchar", "length": 5},
                        {"name": "field_name", "type": "varchar", "length": 100},
                        {"name": "field_value", "type": "text"},
                        {"name": "created_at", "type": "timestamp", "default": "NOW()"},
                        {"name": "updated_at", "type": "timestamp", "default": "NOW()"},
                        {"name": "translated_by", "type": "uuid"}
                    ],
                    "indexes": [
                        {"fields": ["entity_id", "locale"], "name": "idx_{{ entity }}_translations_entity_locale"},
                        {"fields": ["entity_id", "field_name"], "name": "idx_{{ entity }}_translations_entity_field"},
                        {"fields": ["locale"], "name": "idx_{{ entity }}_translations_locale"}
                    ]
                }
            ],
            "actions": [
                {
                    "name": "set_translation",
                    "parameters": [
                        {"name": "entity_id", "type": "uuid"},
                        {"name": "locale", "type": "varchar"},
                        {"name": "field_name", "type": "varchar"},
                        {"name": "field_value", "type": "text"},
                        {"name": "user_id", "type": "uuid"}
                    ],
                    "steps": [
                        {
                            "type": "validate",
                            "condition": "$locale IN {{ supported_locales }}",
                            "error": "Unsupported locale"
                        },
                        {
                            "type": "validate",
                            "condition": "$field_name IN {{ translatable_fields }}",
                            "error": "Field is not translatable"
                        },
                        {
                            "type": "query",
                            "sql": """
                                SELECT COUNT(*) as exists_count
                                FROM {{ entity }}_translations
                                WHERE entity_id = $entity_id AND locale = $locale AND field_name = $field_name
                            """,
                            "into": "existing"
                        },
                        {
                            "type": "if",
                            "condition": "$existing.exists_count > 0",
                            "then": [
                                {
                                    "type": "update",
                                    "table": "{{ entity }}_translations",
                                    "where": "entity_id = $entity_id AND locale = $locale AND field_name = $field_name",
                                    "fields": {
                                        "field_value": "$field_value",
                                        "updated_at": "NOW()",
                                        "translated_by": "$user_id"
                                    }
                                }
                            ],
                            "else": [
                                {
                                    "type": "insert",
                                    "table": "{{ entity }}_translations",
                                    "fields": {
                                        "entity_id": "$entity_id",
                                        "locale": "$locale",
                                        "field_name": "$field_name",
                                        "field_value": "$field_value",
                                        "translated_by": "$user_id"
                                    }
                                }
                            ]
                        }
                    ]
                },
                {
                    "name": "get_translated_entity",
                    "parameters": [
                        {"name": "entity_id", "type": "uuid"},
                        {"name": "locale", "type": "varchar", "default": "{{ default_locale }}"}
                    ],
                    "steps": [
                        {
                            "type": "query",
                            "sql": "SELECT * FROM tb_{{ entity }} WHERE id = $entity_id",
                            "into": "base_entity"
                        },
                        {
                            "type": "query",
                            "sql": """
                                SELECT field_name, field_value
                                FROM {{ entity }}_translations
                                WHERE entity_id = $entity_id AND locale = $locale
                            """,
                            "into": "translations"
                        },
                        {
                            "type": "assign",
                            "variable": "translated_entity",
                            "value": "$base_entity"
                        },
                        {
                            "type": "foreach",
                            "collection": "$translations",
                            "item": "translation",
                            "steps": [
                                {
                                    "type": "assign",
                                    "variable": "translated_entity[$translation.field_name]",
                                    "value": "$translation.field_value"
                                }
                            ]
                        },
                        {"type": "return", "value": "$translated_entity"}
                    ]
                },
                {
                    "name": "get_available_locales",
                    "parameters": [
                        {"name": "entity_id", "type": "uuid"}
                    ],
                    "steps": [
                        {
                            "type": "query",
                            "sql": """
                                SELECT DISTINCT locale
                                FROM {{ entity }}_translations
                                WHERE entity_id = $entity_id
                                ORDER BY locale
                            """,
                            "into": "locales"
                        },
                        {"type": "return", "value": "$locales"}
                    ]
                },
                {
                    "name": "bulk_translate",
                    "parameters": [
                        {"name": "entity_ids", "type": "array"},
                        {"name": "from_locale", "type": "varchar"},
                        {"name": "to_locale", "type": "varchar"},
                        {"name": "translator_id", "type": "uuid"}
                    ],
                    "steps": [
                        {
                            "type": "query",
                            "sql": """
                                SELECT entity_id, field_name, field_value
                                FROM {{ entity }}_translations
                                WHERE entity_id = ANY($entity_ids) AND locale = $from_locale
                            """,
                            "into": "source_translations"
                        },
                        {
                            "type": "foreach",
                            "collection": "$source_translations",
                            "item": "translation",
                            "steps": [
                                {
                                    "type": "call",
                                    "function": "set_translation",
                                    "args": {
                                        "entity_id": "$translation.entity_id",
                                        "locale": "$to_locale",
                                        "field_name": "$translation.field_name",
                                        "field_value": "[AUTO_TRANSLATE:$translation.field_value]",
                                        "user_id": "$translator_id"
                                    }
                                }
                            ]
                        }
                    ]
                }
            ],
            "functions": [
                {
                    "name": "get_translation_completeness",
                    "parameters": ["entity_id", "locale"],
                    "logic": {
                        "steps": [
                            {
                                "type": "assign",
                                "variable": "total_fields",
                                "value": "len({{ translatable_fields }})"
                            },
                            {
                                "type": "query",
                                "sql": """
                                    SELECT COUNT(*) as translated_count
                                    FROM {{ entity }}_translations
                                    WHERE entity_id = $entity_id AND locale = $locale
                                """,
                                "into": "translated"
                            },
                            {
                                "type": "assign",
                                "variable": "completeness",
                                "value": "$translated.translated_count / $total_fields"
                            },
                            {"type": "return", "value": "$completeness"}
                        ]
                    }
                },
                {
                    "name": "get_missing_translations",
                    "parameters": ["entity_id", "locale"],
                    "logic": {
                        "steps": [
                            {
                                "type": "query",
                                "sql": """
                                    SELECT field_name
                                    FROM unnest(ARRAY{{ translatable_fields | map('tojson') | join(', ') }}) as field_name
                                    WHERE field_name NOT IN (
                                        SELECT field_name
                                        FROM {{ entity }}_translations
                                        WHERE entity_id = $entity_id AND locale = $locale
                                    )
                                """,
                                "into": "missing"
                            },
                            {"type": "return", "value": "$missing"}
                        ]
                    }
                }
            ],
            "views": [
                {
                    "name": "{{ entity }}_{{ default_locale }}",
                    "query": """
                        SELECT e.*,
                               COALESCE(t.field_value, e.field_name) as translated_field
                        FROM tb_{{ entity }} e
                        LEFT JOIN {{ entity }}_translations t
                          ON e.id = t.entity_id
                         AND t.locale = '{{ default_locale }}'
                         AND t.field_name = 'field_name'
                    """
                }
            ]
        },
        tags="i18n,internationalization,translation,locale,multi-language",
        icon="🌍"
    )

    print("✅ Seeded internationalization pattern")


def seed_file_attachment_pattern(library: PatternLibrary):
    """Seed file attachment domain pattern"""

    library.add_domain_pattern(
        name="file_attachment",
        category="file_management",
        description="File upload, storage, and management with metadata",
        parameters={
            "entity": {"type": "string", "required": True},
            "max_file_size": {"type": "integer", "required": False, "default": 10485760, "description": "Max file size in bytes (10MB default)"},
            "allowed_types": {"type": "array", "required": False, "default": [], "description": "Allowed MIME types (empty = all allowed)"},
            "enable_versions": {"type": "boolean", "required": False, "default": False, "description": "Enable file versioning"},
            "storage_path": {"type": "string", "required": False, "default": "uploads/{{ entity }}", "description": "Storage path template"}
        },
        implementation={
            "tables": [
                {
                    "name": "{{ entity }}_attachments",
                    "fields": [
                        {"name": "pk_{{ entity }}_attachments", "type": "integer", "primary_key": True},
                        {"name": "entity_id", "type": "uuid"},
                        {"name": "file_name", "type": "varchar", "length": 255},
                        {"name": "original_name", "type": "varchar", "length": 255},
                        {"name": "file_path", "type": "text"},
                        {"name": "file_size", "type": "bigint"},
                        {"name": "mime_type", "type": "varchar", "length": 100},
                        {"name": "file_hash", "type": "varchar", "length": 64},
                        {"name": "version", "type": "integer", "default": 1},
                        {"name": "is_current", "type": "boolean", "default": True},
                        {"name": "uploaded_by", "type": "uuid"},
                        {"name": "uploaded_at", "type": "timestamp", "default": "NOW()"},
                        {"name": "metadata", "type": "jsonb"}
                    ],
                    "indexes": [
                        {"fields": ["entity_id"], "name": "idx_{{ entity }}_attachments_entity"},
                        {"fields": ["file_hash"], "name": "idx_{{ entity }}_attachments_hash"},
                        {"fields": ["is_current"], "name": "idx_{{ entity }}_attachments_current"},
                        {"fields": ["uploaded_at"], "name": "idx_{{ entity }}_attachments_uploaded_at"}
                    ]
                }
            ],
            "actions": [
                {
                    "name": "attach_file",
                    "parameters": [
                        {"name": "entity_id", "type": "uuid"},
                        {"name": "file_name", "type": "varchar"},
                        {"name": "file_data", "type": "binary"},
                        {"name": "mime_type", "type": "varchar"},
                        {"name": "user_id", "type": "uuid"},
                        {"name": "metadata", "type": "jsonb", "default": {}}
                    ],
                    "steps": [
                        {
                            "type": "validate",
                            "condition": "len($file_data) <= {{ max_file_size }}",
                            "error": "File size exceeds maximum allowed size"
                        },
                        {
                            "type": "if",
                            "condition": "len({{ allowed_types }}) > 0",
                            "then": [
                                {
                                    "type": "validate",
                                    "condition": "$mime_type IN {{ allowed_types }}",
                                    "error": "File type not allowed"
                                }
                            ]
                        },
                        {
                            "type": "assign",
                            "variable": "file_hash",
                            "value": "sha256($file_data)"
                        },
                        {
                            "type": "assign",
                            "variable": "file_path",
                            "value": "{{ storage_path }} + '/' + $file_hash + '_' + str(uuid4())"
                        },
                        {
                            "type": "call",
                            "function": "save_file_to_storage",
                            "args": {"file_path": "$file_path", "file_data": "$file_data"}
                        },
                        {
                            "type": "if",
                            "condition": "{{ enable_versions }}",
                            "then": [
                                {
                                    "type": "update",
                                    "table": "{{ entity }}_attachments",
                                    "where": "entity_id = $entity_id AND file_name = $file_name AND is_current = true",
                                    "fields": {"is_current": False}
                                }
                            ]
                        },
                        {
                            "type": "query",
                            "sql": """
                                SELECT COALESCE(MAX(version), 0) + 1 as next_version
                                FROM {{ entity }}_attachments
                                WHERE entity_id = $entity_id AND file_name = $file_name
                            """,
                            "into": "version_info"
                        },
                        {
                            "type": "insert",
                            "table": "{{ entity }}_attachments",
                            "fields": {
                                "entity_id": "$entity_id",
                                "file_name": "$file_name",
                                "original_name": "$file_name",
                                "file_path": "$file_path",
                                "file_size": "len($file_data)",
                                "mime_type": "$mime_type",
                                "file_hash": "$file_hash",
                                "version": "$version_info.next_version",
                                "uploaded_by": "$user_id",
                                "metadata": "$metadata"
                            }
                        }
                    ]
                },
                {
                    "name": "get_attachments",
                    "parameters": [
                        {"name": "entity_id", "type": "uuid"},
                        {"name": "include_versions", "type": "boolean", "default": False}
                    ],
                    "steps": [
                        {
                            "type": "if",
                            "condition": "$include_versions",
                            "then": [
                                {
                                    "type": "query",
                                    "sql": """
                                        SELECT * FROM {{ entity }}_attachments
                                        WHERE entity_id = $entity_id
                                        ORDER BY file_name, version DESC
                                    """,
                                    "into": "attachments"
                                }
                            ],
                            "else": [
                                {
                                    "type": "query",
                                    "sql": """
                                        SELECT * FROM {{ entity }}_attachments
                                        WHERE entity_id = $entity_id AND is_current = true
                                        ORDER BY uploaded_at DESC
                                    """,
                                    "into": "attachments"
                                }
                            ]
                        },
                        {"type": "return", "value": "$attachments"}
                    ]
                },
                {
                    "name": "download_file",
                    "parameters": [
                        {"name": "attachment_id", "type": "integer"}
                    ],
                    "steps": [
                        {
                            "type": "query",
                            "sql": "SELECT * FROM {{ entity }}_attachments WHERE pk_{{ entity }}_attachments = $attachment_id",
                            "into": "attachment"
                        },
                        {
                            "type": "call",
                            "function": "read_file_from_storage",
                            "args": {"file_path": "$attachment.file_path"},
                            "into": "file_data"
                        },
                        {
                            "type": "return",
                            "value": {
                                "file_name": "$attachment.original_name",
                                "file_data": "$file_data",
                                "mime_type": "$attachment.mime_type",
                                "file_size": "$attachment.file_size"
                            }
                        }
                    ]
                },
                {
                    "name": "delete_attachment",
                    "parameters": [
                        {"name": "attachment_id", "type": "integer"},
                        {"name": "user_id", "type": "uuid"}
                    ],
                    "steps": [
                        {
                            "type": "query",
                            "sql": "SELECT * FROM {{ entity }}_attachments WHERE pk_{{ entity }}_attachments = $attachment_id",
                            "into": "attachment"
                        },
                        {
                            "type": "call",
                            "function": "delete_file_from_storage",
                            "args": {"file_path": "$attachment.file_path"}
                        },
                        {
                            "type": "delete",
                            "table": "{{ entity }}_attachments",
                            "where": "pk_{{ entity }}_attachments = $attachment_id"
                        }
                    ]
                }
            ],
            "functions": [
                {
                    "name": "get_storage_stats",
                    "parameters": ["entity_id"],
                    "logic": {
                        "steps": [
                            {
                                "type": "query",
                                "sql": """
                                    SELECT
                                        COUNT(*) as total_files,
                                        SUM(file_size) as total_size,
                                        COUNT(DISTINCT file_name) as unique_files
                                    FROM {{ entity }}_attachments
                                    WHERE entity_id = $entity_id AND is_current = true
                                """,
                                "into": "stats"
                            },
                            {"type": "return", "value": "$stats"}
                        ]
                    }
                },
                {
                    "name": "cleanup_old_versions",
                    "parameters": ["entity_id", "keep_versions"],
                    "logic": {
                        "steps": [
                            {
                                "type": "query",
                                "sql": """
                                    SELECT pk_{{ entity }}_attachments, file_path
                                    FROM {{ entity }}_attachments
                                    WHERE entity_id = $entity_id AND is_current = false
                                    AND version <= (SELECT MAX(version) - $keep_versions FROM {{ entity }}_attachments WHERE entity_id = $entity_id)
                                """,
                                "into": "old_versions"
                            },
                            {
                                "type": "foreach",
                                "collection": "$old_versions",
                                "item": "old_file",
                                "steps": [
                                    {
                                        "type": "call",
                                        "function": "delete_file_from_storage",
                                        "args": {"file_path": "$old_file.file_path"}
                                    },
                                    {
                                        "type": "delete",
                                        "table": "{{ entity }}_attachments",
                                        "where": "pk_{{ entity }}_attachments = $old_file.pk_{{ entity }}_attachments"
                                    }
                                ]
                            }
                        ]
                    }
                }
            ],
            "triggers": [
                {
                    "event": "after_delete",
                    "table": "{{ entity }}",
                    "action": "cleanup_attachments",
                    "logic": {
                        "steps": [
                            {
                                "type": "query",
                                "sql": "SELECT file_path FROM {{ entity }}_attachments WHERE entity_id = old.id",
                                "into": "files_to_delete"
                            },
                            {
                                "type": "foreach",
                                "collection": "$files_to_delete",
                                "item": "file_path",
                                "steps": [
                                    {
                                        "type": "call",
                                        "function": "delete_file_from_storage",
                                        "args": {"file_path": "$file_path"}
                                    }
                                ]
                            },
                            {
                                "type": "delete",
                                "table": "{{ entity }}_attachments",
                                "where": "entity_id = old.id"
                            }
                        ]
                    }
                }
            ]
        },
        tags="file,attachment,upload,storage,versioning",
        icon="📎"
    )

    print("✅ Seeded file_attachment pattern")


def seed_tagging_pattern(library: PatternLibrary):
    """Seed tagging domain pattern"""

    library.add_domain_pattern(
        name="tagging",
        category="organization",
        description="Flexible tagging system with categories and metadata",
        parameters={
            "entity": {"type": "string", "required": True},
            "enable_categories": {"type": "boolean", "required": False, "default": True, "description": "Enable tag categories"},
            "allow_custom_tags": {"type": "boolean", "required": False, "default": True, "description": "Allow users to create custom tags"},
            "max_tags_per_entity": {"type": "integer", "required": False, "default": 50, "description": "Maximum tags per entity"}
        },
        implementation={
            "tables": [
                {
                    "name": "{{ entity }}_tags",
                    "fields": [
                        {"name": "pk_{{ entity }}_tags", "type": "integer", "primary_key": True},
                        {"name": "entity_id", "type": "uuid"},
                        {"name": "tag_name", "type": "varchar", "length": 100},
                        {"name": "tag_category", "type": "varchar", "length": 50},
                        {"name": "tag_color", "type": "varchar", "length": 7},
                        {"name": "tag_metadata", "type": "jsonb"},
                        {"name": "created_by", "type": "uuid"},
                        {"name": "created_at", "type": "timestamp", "default": "NOW()"}
                    ],
                    "indexes": [
                        {"fields": ["entity_id"], "name": "idx_{{ entity }}_tags_entity"},
                        {"fields": ["tag_name"], "name": "idx_{{ entity }}_tags_name"},
                        {"fields": ["tag_category"], "name": "idx_{{ entity }}_tags_category"}
                    ]
                },
                {
                    "name": "tag_definitions",
                    "fields": [
                        {"name": "pk_tag_definitions", "type": "integer", "primary_key": True},
                        {"name": "tag_name", "type": "varchar", "length": 100, "unique": True},
                        {"name": "tag_category", "type": "varchar", "length": 50},
                        {"name": "tag_color", "type": "varchar", "length": 7},
                        {"name": "tag_description", "type": "text"},
                        {"name": "usage_count", "type": "integer", "default": 0},
                        {"name": "is_system_tag", "type": "boolean", "default": False},
                        {"name": "created_by", "type": "uuid"},
                        {"name": "created_at", "type": "timestamp", "default": "NOW()"}
                    ],
                    "indexes": [
                        {"fields": ["tag_category"], "name": "idx_tag_definitions_category"},
                        {"fields": ["usage_count"], "name": "idx_tag_definitions_usage"}
                    ]
                }
            ],
            "actions": [
                {
                    "name": "add_tag",
                    "parameters": [
                        {"name": "entity_id", "type": "uuid"},
                        {"name": "tag_name", "type": "varchar"},
                        {"name": "tag_category", "type": "varchar", "default": None},
                        {"name": "user_id", "type": "uuid"},
                        {"name": "tag_metadata", "type": "jsonb", "default": {}}
                    ],
                    "steps": [
                        {
                            "type": "query",
                            "sql": "SELECT COUNT(*) as tag_count FROM {{ entity }}_tags WHERE entity_id = $entity_id",
                            "into": "current_tags"
                        },
                        {
                            "type": "validate",
                            "condition": "$current_tags.tag_count < {{ max_tags_per_entity }}",
                            "error": "Maximum tags per entity exceeded"
                        },
                        {
                            "type": "query",
                            "sql": """
                                SELECT COUNT(*) as exists_count
                                FROM {{ entity }}_tags
                                WHERE entity_id = $entity_id AND tag_name = $tag_name
                            """,
                            "into": "existing"
                        },
                        {
                            "type": "validate",
                            "condition": "$existing.exists_count == 0",
                            "error": "Tag already exists on this entity"
                        },
                        {
                            "type": "if",
                            "condition": "{{ enable_categories }} AND $tag_category IS NOT NULL",
                            "then": [
                                {
                                    "type": "call",
                                    "function": "validate_tag_category",
                                    "args": {"category": "$tag_category"}
                                }
                            ]
                        },
                        {
                            "type": "assign",
                            "variable": "tag_color",
                            "value": None
                        },
                        {
                            "type": "if",
                            "condition": "{{ allow_custom_tags }}",
                            "then": [
                                {
                                    "type": "call",
                                    "function": "ensure_tag_definition",
                                    "args": {"tag_name": "$tag_name", "tag_category": "$tag_category", "user_id": "$user_id"},
                                    "into": "tag_def"
                                },
                                {
                                    "type": "assign",
                                    "variable": "tag_color",
                                    "value": "$tag_def.tag_color"
                                }
                            ]
                        },
                        {
                            "type": "insert",
                            "table": "{{ entity }}_tags",
                            "fields": {
                                "entity_id": "$entity_id",
                                "tag_name": "$tag_name",
                                "tag_category": "$tag_category",
                                "tag_color": "$tag_color",
                                "tag_metadata": "$tag_metadata",
                                "created_by": "$user_id"
                            }
                        },
                        {
                            "type": "call",
                            "function": "increment_tag_usage",
                            "args": {"tag_name": "$tag_name"}
                        }
                    ]
                },
                {
                    "name": "remove_tag",
                    "parameters": [
                        {"name": "entity_id", "type": "uuid"},
                        {"name": "tag_name", "type": "varchar"}
                    ],
                    "steps": [
                        {
                            "type": "delete",
                            "table": "{{ entity }}_tags",
                            "where": "entity_id = $entity_id AND tag_name = $tag_name"
                        },
                        {
                            "type": "call",
                            "function": "decrement_tag_usage",
                            "args": {"tag_name": "$tag_name"}
                        }
                    ]
                },
                {
                    "name": "get_entity_tags",
                    "parameters": [
                        {"name": "entity_id", "type": "uuid"}
                    ],
                    "steps": [
                        {
                            "type": "query",
                            "sql": """
                                SELECT t.*, td.tag_color, td.tag_description
                                FROM {{ entity }}_tags t
                                LEFT JOIN tag_definitions td ON t.tag_name = td.tag_name
                                WHERE t.entity_id = $entity_id
                                ORDER BY t.created_at
                            """,
                            "into": "tags"
                        },
                        {"type": "return", "value": "$tags"}
                    ]
                },
                {
                    "name": "search_by_tags",
                    "parameters": [
                        {"name": "tag_names", "type": "array"},
                        {"name": "match_all", "type": "boolean", "default": False}
                    ],
                    "steps": [
                        {
                            "type": "if",
                            "condition": "$match_all",
                            "then": [
                                {
                                    "type": "query",
                                    "sql": """
                                        SELECT e.*
                                        FROM tb_{{ entity }} e
                                        WHERE e.id IN (
                                            SELECT entity_id
                                            FROM {{ entity }}_tags
                                            WHERE tag_name = ANY($tag_names)
                                            GROUP BY entity_id
                                            HAVING COUNT(DISTINCT tag_name) = array_length($tag_names, 1)
                                        )
                                    """,
                                    "into": "results"
                                }
                            ],
                            "else": [
                                {
                                    "type": "query",
                                    "sql": """
                                        SELECT DISTINCT e.*
                                        FROM tb_{{ entity }} e
                                        JOIN {{ entity }}_tags t ON e.id = t.entity_id
                                        WHERE t.tag_name = ANY($tag_names)
                                    """,
                                    "into": "results"
                                }
                            ]
                        },
                        {"type": "return", "value": "$results"}
                    ]
                }
            ],
            "functions": [
                {
                    "name": "validate_tag_category",
                    "parameters": ["category"],
                    "logic": {
                        "steps": [
                            {
                                "type": "query",
                                "sql": "SELECT COUNT(*) as category_count FROM tag_definitions WHERE tag_category = $category",
                                "into": "category_check"
                            },
                            {
                                "type": "validate",
                                "condition": "$category_check.category_count > 0",
                                "error": "Invalid tag category"
                            }
                        ]
                    }
                },
                {
                    "name": "ensure_tag_definition",
                    "parameters": ["tag_name", "tag_category", "user_id"],
                    "logic": {
                        "steps": [
                            {
                                "type": "query",
                                "sql": "SELECT * FROM tag_definitions WHERE tag_name = $tag_name",
                                "into": "existing_def"
                            },
                            {
                                "type": "if",
                                "condition": "len($existing_def) == 0",
                                "then": [
                                    {
                                        "type": "insert",
                                        "table": "tag_definitions",
                                        "fields": {
                                            "tag_name": "$tag_name",
                                            "tag_category": "$tag_category",
                                            "tag_color": "generate_random_color()",
                                            "created_by": "$user_id"
                                        }
                                    },
                                    {
                                        "type": "query",
                                        "sql": "SELECT * FROM tag_definitions WHERE tag_name = $tag_name",
                                        "into": "new_def"
                                    },
                                    {"type": "return", "value": "$new_def"}
                                ],
                                "else": [
                                    {"type": "return", "value": "$existing_def"}
                                ]
                            }
                        ]
                    }
                },
                {
                    "name": "increment_tag_usage",
                    "parameters": ["tag_name"],
                    "logic": {
                        "steps": [
                            {
                                "type": "update",
                                "table": "tag_definitions",
                                "where": "tag_name = $tag_name",
                                "fields": {"usage_count": "usage_count + 1"}
                            }
                        ]
                    }
                },
                {
                    "name": "decrement_tag_usage",
                    "parameters": ["tag_name"],
                    "logic": {
                        "steps": [
                            {
                                "type": "update",
                                "table": "tag_definitions",
                                "where": "tag_name = $tag_name",
                                "fields": {"usage_count": "GREATEST(usage_count - 1, 0)"}
                            }
                        ]
                    }
                },
                {
                    "name": "get_popular_tags",
                    "parameters": ["limit"],
                    "logic": {
                        "steps": [
                            {
                                "type": "query",
                                "sql": """
                                    SELECT tag_name, tag_category, usage_count, tag_color
                                    FROM tag_definitions
                                    ORDER BY usage_count DESC
                                    LIMIT $limit
                                """,
                                "into": "popular_tags"
                            },
                            {"type": "return", "value": "$popular_tags"}
                        ]
                    }
                }
            ],
            "views": [
                {
                    "name": "{{ entity }}_with_tags",
                    "query": """
                        SELECT e.*,
                               array_agg(t.tag_name ORDER BY t.created_at) as tags,
                               array_agg(t.tag_category ORDER BY t.created_at) as tag_categories
                        FROM tb_{{ entity }} e
                        LEFT JOIN {{ entity }}_tags t ON e.id = t.entity_id
                        GROUP BY e.id
                    """
                }
            ]
        },
        tags="tag,tagging,categorization,organization,metadata",
        icon="🏷️"
    )

    print("✅ Seeded tagging pattern")


def seed_commenting_pattern(library: PatternLibrary):
    """Seed commenting domain pattern"""

    library.add_domain_pattern(
        name="commenting",
        category="collaboration",
        description="Comments and notes system with threading and mentions",
        parameters={
            "entity": {"type": "string", "required": True},
            "enable_threading": {"type": "boolean", "required": False, "default": True, "description": "Enable threaded replies"},
            "enable_mentions": {"type": "boolean", "required": False, "default": True, "description": "Enable @mentions"},
            "max_comment_length": {"type": "integer", "required": False, "default": 5000, "description": "Maximum comment length"}
        },
        implementation={
            "tables": [
                {
                    "name": "{{ entity }}_comments",
                    "fields": [
                        {"name": "pk_{{ entity }}_comments", "type": "integer", "primary_key": True},
                        {"name": "entity_id", "type": "uuid"},
                        {"name": "parent_comment_id", "type": "integer", "nullable": True},
                        {"name": "comment_text", "type": "text"},
                        {"name": "comment_html", "type": "text"},
                        {"name": "author_id", "type": "uuid"},
                        {"name": "author_name", "type": "varchar", "length": 255},
                        {"name": "mentions", "type": "jsonb", "default": []},
                        {"name": "is_edited", "type": "boolean", "default": False},
                        {"name": "edited_at", "type": "timestamp"},
                        {"name": "edited_by", "type": "uuid"},
                        {"name": "created_at", "type": "timestamp", "default": "NOW()"},
                        {"name": "updated_at", "type": "timestamp", "default": "NOW()"}
                    ],
                    "indexes": [
                        {"fields": ["entity_id"], "name": "idx_{{ entity }}_comments_entity"},
                        {"fields": ["parent_comment_id"], "name": "idx_{{ entity }}_comments_parent"},
                        {"fields": ["author_id"], "name": "idx_{{ entity }}_comments_author"},
                        {"fields": ["created_at"], "name": "idx_{{ entity }}_comments_created_at"}
                    ]
                }
            ],
            "actions": [
                {
                    "name": "add_comment",
                    "parameters": [
                        {"name": "entity_id", "type": "uuid"},
                        {"name": "comment_text", "type": "text"},
                        {"name": "author_id", "type": "uuid"},
                        {"name": "author_name", "type": "varchar"},
                        {"name": "parent_comment_id", "type": "integer", "default": None}
                    ],
                    "steps": [
                        {
                            "type": "validate",
                            "condition": "len($comment_text) <= {{ max_comment_length }}",
                            "error": "Comment text exceeds maximum length"
                        },
                        {
                            "type": "if",
                            "condition": "{{ enable_threading }} AND $parent_comment_id IS NOT NULL",
                            "then": [
                                {
                                    "type": "validate",
                                    "condition": "comment_exists($parent_comment_id)",
                                    "error": "Parent comment does not exist"
                                }
                            ]
                        },
                        {
                            "type": "assign",
                            "variable": "mentions",
                            "value": []
                        },
                        {
                            "type": "if",
                            "condition": "{{ enable_mentions }}",
                            "then": [
                                {
                                    "type": "call",
                                    "function": "extract_mentions",
                                    "args": {"text": "$comment_text"},
                                    "into": "mentions"
                                }
                            ]
                        },
                        {
                            "type": "assign",
                            "variable": "comment_html",
                            "value": "markdown_to_html($comment_text)"
                        },
                        {
                            "type": "insert",
                            "table": "{{ entity }}_comments",
                            "fields": {
                                "entity_id": "$entity_id",
                                "parent_comment_id": "$parent_comment_id",
                                "comment_text": "$comment_text",
                                "comment_html": "$comment_html",
                                "author_id": "$author_id",
                                "author_name": "$author_name",
                                "mentions": "$mentions"
                            }
                        },
                        {
                            "type": "call",
                            "function": "notify_mentions",
                            "args": {"comment_id": "last_insert_id()", "mentions": "$mentions"}
                        }
                    ]
                },
                {
                    "name": "get_comments",
                    "parameters": [
                        {"name": "entity_id", "type": "uuid"},
                        {"name": "include_replies", "type": "boolean", "default": True}
                    ],
                    "steps": [
                        {
                            "type": "if",
                            "condition": "$include_replies",
                            "then": [
                                {
                                    "type": "query",
                                    "sql": """
                                        SELECT c.*,
                                               COUNT(r.pk_{{ entity }}_comments) as reply_count
                                        FROM {{ entity }}_comments c
                                        LEFT JOIN {{ entity }}_comments r ON c.pk_{{ entity }}_comments = r.parent_comment_id
                                        WHERE c.entity_id = $entity_id AND c.parent_comment_id IS NULL
                                        GROUP BY c.pk_{{ entity }}_comments
                                        ORDER BY c.created_at
                                    """,
                                    "into": "comments"
                                }
                            ],
                            "else": [
                                {
                                    "type": "query",
                                    "sql": """
                                        SELECT * FROM {{ entity }}_comments
                                        WHERE entity_id = $entity_id
                                        ORDER BY created_at
                                    """,
                                    "into": "comments"
                                }
                            ]
                        },
                        {"type": "return", "value": "$comments"}
                    ]
                }
            ],
            "functions": [
                {
                    "name": "extract_mentions",
                    "parameters": ["text"],
                    "logic": {
                        "steps": [
                            {
                                "type": "assign",
                                "variable": "mention_pattern",
                                "value": "r'@(\\w+)'"
                            },
                            {
                                "type": "assign",
                                "variable": "mentions",
                                "value": "re.findall($mention_pattern, $text)"
                            },
                            {"type": "return", "value": "$mentions"}
                        ]
                    }
                },
                {
                    "name": "comment_exists",
                    "parameters": ["comment_id"],
                    "logic": {
                        "steps": [
                            {
                                "type": "query",
                                "sql": "SELECT COUNT(*) as count FROM {{ entity }}_comments WHERE pk_{{ entity }}_comments = $comment_id",
                                "into": "result"
                            },
                            {"type": "return", "value": "$result.count > 0"}
                        ]
                    }
                }
            ]
        },
        tags="comment,threading,mention,collaboration,discussion",
        icon="💬"
    )

    print("✅ Seeded commenting pattern")


def seed_notification_pattern(library: PatternLibrary):
    """Seed notification domain pattern"""

    library.add_domain_pattern(
        name="notification",
        category="communication",
        description="Event-triggered notifications with delivery channels",
        parameters={
            "entity": {"type": "string", "required": True},
            "channels": {"type": "array", "required": False, "default": ["email", "in_app"], "description": "Notification channels"},
            "enable_preferences": {"type": "boolean", "required": False, "default": True, "description": "Enable user notification preferences"}
        },
        implementation={
            "tables": [
                {
                    "name": "{{ entity }}_notifications",
                    "fields": [
                        {"name": "pk_{{ entity }}_notifications", "type": "integer", "primary_key": True},
                        {"name": "entity_id", "type": "uuid"},
                        {"name": "recipient_id", "type": "uuid"},
                        {"name": "notification_type", "type": "varchar", "length": 50},
                        {"name": "title", "type": "varchar", "length": 255},
                        {"name": "message", "type": "text"},
                        {"name": "data", "type": "jsonb"},
                        {"name": "channels", "type": "jsonb"},
                        {"name": "is_read", "type": "boolean", "default": False},
                        {"name": "read_at", "type": "timestamp"},
                        {"name": "sent_at", "type": "timestamp"},
                        {"name": "created_at", "type": "timestamp", "default": "NOW()"}
                    ],
                    "indexes": [
                        {"fields": ["entity_id"], "name": "idx_{{ entity }}_notifications_entity"},
                        {"fields": ["recipient_id"], "name": "idx_{{ entity }}_notifications_recipient"},
                        {"fields": ["is_read"], "name": "idx_{{ entity }}_notifications_read"},
                        {"fields": ["created_at"], "name": "idx_{{ entity }}_notifications_created_at"}
                    ]
                },
                {
                    "name": "notification_preferences",
                    "fields": [
                        {"name": "pk_notification_preferences", "type": "integer", "primary_key": True},
                        {"name": "user_id", "type": "uuid"},
                        {"name": "notification_type", "type": "varchar", "length": 50},
                        {"name": "channel", "type": "varchar", "length": 20},
                        {"name": "enabled", "type": "boolean", "default": True},
                        {"name": "created_at", "type": "timestamp", "default": "NOW()"},
                        {"name": "updated_at", "type": "timestamp", "default": "NOW()"}
                    ],
                    "indexes": [
                        {"fields": ["user_id", "notification_type"], "name": "idx_notification_preferences_user_type"}
                    ]
                }
            ],
            "actions": [
                {
                    "name": "send_notification",
                    "parameters": [
                        {"name": "entity_id", "type": "uuid"},
                        {"name": "recipient_ids", "type": "array"},
                        {"name": "notification_type", "type": "varchar"},
                        {"name": "title", "type": "varchar"},
                        {"name": "message", "type": "text"},
                        {"name": "data", "type": "jsonb", "default": {}}
                    ],
                    "steps": [
                        {
                            "type": "foreach",
                            "collection": "$recipient_ids",
                            "item": "recipient_id",
                            "steps": [
                                {
                                    "type": "call",
                                    "function": "get_user_channels",
                                    "args": {"user_id": "$recipient_id", "notification_type": "$notification_type"},
                                    "into": "user_channels"
                                },
                                {
                                    "type": "insert",
                                    "table": "{{ entity }}_notifications",
                                    "fields": {
                                        "entity_id": "$entity_id",
                                        "recipient_id": "$recipient_id",
                                        "notification_type": "$notification_type",
                                        "title": "$title",
                                        "message": "$message",
                                        "data": "$data",
                                        "channels": "$user_channels"
                                    }
                                },
                                {
                                    "type": "call",
                                    "function": "deliver_notification",
                                    "args": {
                                        "notification_id": "last_insert_id()",
                                        "channels": "$user_channels",
                                        "title": "$title",
                                        "message": "$message"
                                    }
                                }
                            ]
                        }
                    ]
                },
                {
                    "name": "mark_as_read",
                    "parameters": [
                        {"name": "notification_id", "type": "integer"},
                        {"name": "user_id", "type": "uuid"}
                    ],
                    "steps": [
                        {
                            "type": "update",
                            "table": "{{ entity }}_notifications",
                            "where": "pk_{{ entity }}_notifications = $notification_id AND recipient_id = $user_id",
                            "fields": {
                                "is_read": True,
                                "read_at": "NOW()"
                            }
                        }
                    ]
                }
            ],
            "functions": [
                {
                    "name": "get_user_channels",
                    "parameters": ["user_id", "notification_type"],
                    "logic": {
                        "steps": [
                            {
                                "type": "if",
                                "condition": "{{ enable_preferences }}",
                                "then": [
                                    {
                                        "type": "query",
                                        "sql": """
                                            SELECT channel
                                            FROM notification_preferences
                                            WHERE user_id = $user_id
                                              AND notification_type = $notification_type
                                              AND enabled = true
                                        """,
                                        "into": "user_prefs"
                                    },
                                    {
                                        "type": "assign",
                                        "variable": "channels",
                                        "value": "[p.channel for p in $user_prefs]"
                                    }
                                ],
                                "else": [
                                    {
                                        "type": "assign",
                                        "variable": "channels",
                                        "value": "{{ channels }}"
                                    }
                                ]
                            },
                            {"type": "return", "value": "$channels"}
                        ]
                    }
                }
            ]
        },
        tags="notification,alert,communication,channel,preference",
        icon="🔔"
    )

    print("✅ Seeded notification pattern")


def seed_scheduling_pattern(library: PatternLibrary):
    """Seed scheduling domain pattern"""

    library.add_domain_pattern(
        name="scheduling",
        category="time_management",
        description="Date-based scheduling with recurring events and reminders",
        parameters={
            "entity": {"type": "string", "required": True},
            "enable_recurring": {"type": "boolean", "required": False, "default": True, "description": "Enable recurring schedules"},
            "enable_reminders": {"type": "boolean", "required": False, "default": True, "description": "Enable reminder notifications"},
            "timezone_support": {"type": "boolean", "required": False, "default": True, "description": "Support multiple timezones"}
        },
        implementation={
            "fields": [
                {"name": "scheduled_at", "type": "timestamp"},
                {"name": "duration_minutes", "type": "integer"},
                {"name": "timezone", "type": "varchar", "length": 50},
                {"name": "is_recurring", "type": "boolean", "default": False},
                {"name": "recurrence_rule", "type": "varchar", "length": 200},
                {"name": "next_occurrence", "type": "timestamp"},
                {"name": "reminder_minutes_before", "type": "integer"},
                {"name": "reminder_sent", "type": "boolean", "default": False}
            ],
            "tables": [
                {
                    "name": "{{ entity }}_schedule_history",
                    "fields": [
                        {"name": "pk_{{ entity }}_schedule_history", "type": "integer", "primary_key": True},
                        {"name": "entity_id", "type": "uuid"},
                        {"name": "scheduled_at", "type": "timestamp"},
                        {"name": "actual_at", "type": "timestamp"},
                        {"name": "status", "type": "enum", "values": ["scheduled", "completed", "cancelled", "missed"]},
                        {"name": "notes", "type": "text"}
                    ]
                }
            ],
            "actions": [
                {
                    "name": "schedule_event",
                    "parameters": [
                        {"name": "entity_id", "type": "uuid"},
                        {"name": "scheduled_at", "type": "timestamp"},
                        {"name": "duration_minutes", "type": "integer", "default": 60},
                        {"name": "timezone", "type": "varchar", "default": "UTC"},
                        {"name": "recurrence_rule", "type": "varchar", "default": None},
                        {"name": "reminder_minutes_before", "type": "integer", "default": 15}
                    ],
                    "steps": [
                        {
                            "type": "validate",
                            "condition": "$scheduled_at > NOW()",
                            "error": "Cannot schedule events in the past"
                        },
                        {
                            "type": "assign",
                            "variable": "is_recurring",
                            "value": "$recurrence_rule IS NOT NULL"
                        },
                        {
                            "type": "assign",
                            "variable": "next_occurrence",
                            "value": "$scheduled_at"
                        },
                        {
                            "type": "if",
                            "condition": "$is_recurring",
                            "then": [
                                {
                                    "type": "call",
                                    "function": "calculate_next_occurrence",
                                    "args": {"rule": "$recurrence_rule", "from_date": "$scheduled_at"},
                                    "into": "next_occurrence"
                                }
                            ]
                        },
                        {
                            "type": "update",
                            "entity": "{{ entity }}",
                            "where": "id = $entity_id",
                            "fields": {
                                "scheduled_at": "$scheduled_at",
                                "duration_minutes": "$duration_minutes",
                                "timezone": "$timezone",
                                "is_recurring": "$is_recurring",
                                "recurrence_rule": "$recurrence_rule",
                                "next_occurrence": "$next_occurrence",
                                "reminder_minutes_before": "$reminder_minutes_before",
                                "reminder_sent": False
                            }
                        }
                    ]
                },
                {
                    "name": "get_upcoming_events",
                    "parameters": [
                        {"name": "days_ahead", "type": "integer", "default": 7}
                    ],
                    "steps": [
                        {
                            "type": "query",
                            "sql": """
                                SELECT * FROM tb_{{ entity }}
                                WHERE next_occurrence IS NOT NULL
                                  AND next_occurrence <= NOW() + INTERVAL '$days_ahead days'
                                ORDER BY next_occurrence
                            """,
                            "into": "upcoming"
                        },
                        {"type": "return", "value": "$upcoming"}
                    ]
                }
            ],
            "functions": [
                {
                    "name": "calculate_next_occurrence",
                    "parameters": ["rule", "from_date"],
                    "logic": {
                        "steps": [
                            {
                                "type": "assign",
                                "variable": "next_date",
                                "value": "parse_rrule($rule).after($from_date)"
                            },
                            {"type": "return", "value": "$next_date"}
                        ]
                    }
                },
                {
                    "name": "process_due_events",
                    "logic": {
                        "steps": [
                            {
                                "type": "query",
                                "sql": """
                                    SELECT * FROM tb_{{ entity }}
                                    WHERE next_occurrence <= NOW()
                                      AND status NOT IN ('completed', 'cancelled')
                                """,
                                "into": "due_events"
                            },
                            {
                                "type": "foreach",
                                "collection": "$due_events",
                                "item": "event",
                                "steps": [
                                    {
                                        "type": "call",
                                        "function": "process_event",
                                        "args": {"event": "$event"}
                                    }
                                ]
                            }
                        ]
                    }
                }
            ],
            "triggers": [
                {
                    "event": "after_update",
                    "condition": "new.status = 'completed'",
                    "action": "record_schedule_history"
                }
            ]
        },
        tags="schedule,time,recurring,event,reminder,calendar",
        icon="📅"
    )

    print("✅ Seeded scheduling pattern")


def seed_rate_limiting_pattern(library: PatternLibrary):
    """Seed rate limiting domain pattern"""

    library.add_domain_pattern(
        name="rate_limiting",
        category="performance",
        description="API rate limiting with sliding window and burst handling",
        parameters={
            "entity": {"type": "string", "required": True},
            "requests_per_minute": {"type": "integer", "required": False, "default": 60, "description": "Requests per minute limit"},
            "burst_limit": {"type": "integer", "required": False, "default": 10, "description": "Burst request limit"},
            "window_minutes": {"type": "integer", "required": False, "default": 1, "description": "Rate limit window in minutes"}
        },
        implementation={
            "tables": [
                {
                    "name": "{{ entity }}_rate_limits",
                    "fields": [
                        {"name": "pk_{{ entity }}_rate_limits", "type": "integer", "primary_key": True},
                        {"name": "identifier", "type": "varchar", "length": 255},
                        {"name": "request_count", "type": "integer", "default": 0},
                        {"name": "window_start", "type": "timestamp", "default": "NOW()"},
                        {"name": "last_request", "type": "timestamp", "default": "NOW()"},
                        {"name": "blocked_until", "type": "timestamp"}
                    ],
                    "indexes": [
                        {"fields": ["identifier"], "name": "idx_{{ entity }}_rate_limits_identifier"},
                        {"fields": ["window_start"], "name": "idx_{{ entity }}_rate_limits_window"}
                    ]
                }
            ],
            "actions": [
                {
                    "name": "check_rate_limit",
                    "parameters": [
                        {"name": "identifier", "type": "varchar"},
                        {"name": "action", "type": "varchar", "default": "default"}
                    ],
                    "steps": [
                        {
                            "type": "call",
                            "function": "get_rate_limit_record",
                            "args": {"identifier": "$identifier"},
                            "into": "record"
                        },
                        {
                            "type": "assign",
                            "variable": "current_time",
                            "value": "NOW()"
                        },
                        {
                            "type": "assign",
                            "variable": "window_start",
                            "value": "$current_time - INTERVAL '{{ window_minutes }} minutes'"
                        },
                        {
                            "type": "if",
                            "condition": "$record.window_start < $window_start",
                            "then": [
                                {
                                    "type": "update",
                                    "table": "{{ entity }}_rate_limits",
                                    "where": "identifier = $identifier",
                                    "fields": {
                                        "request_count": 1,
                                        "window_start": "$current_time",
                                        "last_request": "$current_time",
                                        "blocked_until": None
                                    }
                                },
                                {"type": "return", "value": {"allowed": True, "remaining": "{{ requests_per_minute }} - 1"}}
                            ],
                            "else": [
                                {
                                    "type": "if",
                                    "condition": "$record.blocked_until IS NOT NULL AND $current_time < $record.blocked_until",
                                    "then": [
                                        {"type": "return", "value": {"allowed": False, "retry_after": "$record.blocked_until"}}
                                    ]
                                },
                                {
                                    "type": "assign",
                                    "variable": "new_count",
                                    "value": "$record.request_count + 1"
                                },
                                {
                                    "type": "if",
                                    "condition": "$new_count > {{ requests_per_minute }}",
                                    "then": [
                                        {
                                            "type": "assign",
                                            "variable": "blocked_until",
                                            "value": "$current_time + INTERVAL '{{ window_minutes }} minutes'"
                                        },
                                        {
                                            "type": "update",
                                            "table": "{{ entity }}_rate_limits",
                                            "where": "identifier = $identifier",
                                            "fields": {
                                                "blocked_until": "$blocked_until",
                                                "last_request": "$current_time"
                                            }
                                        },
                                        {"type": "return", "value": {"allowed": False, "retry_after": "$blocked_until"}}
                                    ],
                                    "else": [
                                        {
                                            "type": "update",
                                            "table": "{{ entity }}_rate_limits",
                                            "where": "identifier = $identifier",
                                            "fields": {
                                                "request_count": "$new_count",
                                                "last_request": "$current_time"
                                            }
                                        },
                                        {
                                            "type": "assign",
                                            "variable": "remaining",
                                            "value": "{{ requests_per_minute }} - $new_count"
                                        },
                                        {"type": "return", "value": {"allowed": True, "remaining": "$remaining"}}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ],
            "functions": [
                {
                    "name": "get_rate_limit_record",
                    "parameters": ["identifier"],
                    "logic": {
                        "steps": [
                            {
                                "type": "query",
                                "sql": "SELECT * FROM {{ entity }}_rate_limits WHERE identifier = $identifier",
                                "into": "record"
                            },
                            {
                                "type": "if",
                                "condition": "len($record) == 0",
                                "then": [
                                    {
                                        "type": "insert",
                                        "table": "{{ entity }}_rate_limits",
                                        "fields": {"identifier": "$identifier"}
                                    },
                                    {
                                        "type": "query",
                                        "sql": "SELECT * FROM {{ entity }}_rate_limits WHERE identifier = $identifier",
                                        "into": "record"
                                    }
                                ]
                            },
                            {"type": "return", "value": "$record"}
                        ]
                    }
                },
                {
                    "name": "cleanup_old_records",
                    "logic": {
                        "steps": [
                            {
                                "type": "assign",
                                "variable": "cutoff",
                                "value": "NOW() - INTERVAL '24 hours'"
                            },
                            {
                                "type": "delete",
                                "table": "{{ entity }}_rate_limits",
                                "where": "last_request < $cutoff AND blocked_until IS NULL"
                            }
                        ]
                    }
                }
            ]
        },
        tags="rate-limit,throttling,performance,api,security",
        icon="⏱️"
    )

    print("✅ Seeded rate_limiting pattern")


def seed_expanded_domain_patterns(library: PatternLibrary):
    """Seed all 12 expanded domain patterns for Phase C2"""
    seed_validation_chain_pattern(library)
    seed_approval_workflow_pattern(library)
    seed_hierarchy_navigation_pattern(library)
    seed_computed_fields_pattern(library)
    seed_search_optimization_pattern(library)
    seed_internationalization_pattern(library)
    seed_file_attachment_pattern(library)
    seed_tagging_pattern(library)
    seed_commenting_pattern(library)
    seed_notification_pattern(library)
    seed_scheduling_pattern(library)
    seed_rate_limiting_pattern(library)
    print("✅ Seeded all 12 expanded domain patterns")


def seed_core_domain_patterns(library: PatternLibrary):
    """Seed all 3 core domain patterns"""
    seed_state_machine_pattern(library)
    seed_audit_trail_pattern(library)
    seed_soft_delete_pattern(library)
    print("✅ Seeded all 3 core domain patterns")


if __name__ == "__main__":
    # For testing
    library = PatternLibrary(db_path=":memory:")
    seed_core_domain_patterns(library)