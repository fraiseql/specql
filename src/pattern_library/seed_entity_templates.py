"""Seed entity templates for Tier 3"""

from .api import PatternLibrary


def seed_crm_contact_template(library: PatternLibrary):
    """Seed CRM Contact entity template"""

    library.add_entity_template(
        template_name="contact",
        template_namespace="crm",
        description="CRM contact with state machine, audit trail, and soft delete",
        default_fields={
            # Core fields
            "first_name": {"type": "text", "required": True},
            "last_name": {"type": "text", "required": True},
            "email": {"type": "email", "required": True, "unique": True},
            "phone": {"type": "text"},
            "company": {"type": "ref", "entity": "Company"},

            # Address
            "street": {"type": "text"},
            "city": {"type": "text"},
            "state": {"type": "text"},
            "postal_code": {"type": "text"},
            "country": {"type": "text", "default": "US"},

            # Metadata
            "source": {"type": "enum", "values": ["website", "referral", "import", "manual"]},
            "tags": {"type": "array"},
            "notes": {"type": "text"}
        },
        default_patterns={
            "state_machine": {
                "states": ["lead", "prospect", "qualified", "customer", "inactive"],
                "transitions": {
                    "lead->prospect": {"action": "initial_contact"},
                    "prospect->qualified": {"action": "qualify", "guard": "has_budget"},
                    "qualified->customer": {"action": "convert", "guard": "has_signed_contract"},
                    "customer->inactive": {"action": "deactivate"}
                },
                "initial_state": "lead"
            },
            "audit_trail": {
                "track_versions": True
            },
            "soft_delete": {}
        },
        default_actions={
            "qualify": {
                "description": "Qualify lead as prospect",
                "parameters": [
                    {"name": "user_id", "type": "uuid"}
                ],
                "steps": [
                    {"type": "validate", "condition": "state == 'lead'", "error": "Can only qualify leads"},
                    {"type": "validate", "condition": "email IS NOT NULL", "error": "Email is required"},
                    {"type": "call", "function": "transition_to", "args": {"target_state": "prospect", "user_id": "$user_id"}}
                ]
            },
            "convert_to_customer": {
                "description": "Convert qualified prospect to customer",
                "parameters": [
                    {"name": "user_id", "type": "uuid"}
                ],
                "steps": [
                    {"type": "validate", "condition": "state == 'qualified'", "error": "Can only convert qualified prospects"},
                    {"type": "call", "function": "transition_to", "args": {"target_state": "customer", "user_id": "$user_id"}},
                    {"type": "notify", "recipients": ["sales_team"], "message": "New customer: {first_name} {last_name}"}
                ]
            },
            "update_contact_info": {
                "description": "Update contact information",
                "parameters": [
                    {"name": "updates", "type": "object"},
                    {"name": "user_id", "type": "uuid"}
                ],
                "steps": [
                    {"type": "update", "entity": "Contact", "where": "id = $id", "fields": "$updates"},
                    {"type": "log", "message": "Contact updated by user {user_id}"}
                ]
            }
        },
        configuration_options={
            "enable_duplicates_detection": {"type": "boolean", "default": True},
            "require_phone": {"type": "boolean", "default": False},
            "enable_lead_scoring": {"type": "boolean", "default": False}
        },
        icon="👤",
        tags="crm,contact,lead,customer,sales"
    )

    print("✅ Seeded CRM Contact template")


def seed_crm_lead_template(library: PatternLibrary):
    """Seed CRM Lead entity template"""

    library.add_entity_template(
        template_name="lead",
        template_namespace="crm",
        description="CRM lead with scoring and conversion tracking",
        default_fields={
            # Core fields
            "first_name": {"type": "text", "required": True},
            "last_name": {"type": "text", "required": True},
            "email": {"type": "email", "required": True, "unique": True},
            "phone": {"type": "text"},
            "company": {"type": "text"},
            "job_title": {"type": "text"},

            # Lead scoring
            "score": {"type": "integer", "default": 0},
            "source": {"type": "enum", "values": ["website", "referral", "cold_outreach", "event", "import"]},
            "campaign": {"type": "text"},

            # Qualification
            "budget": {"type": "decimal", "precision": 10, "scale": 2},
            "timeline": {"type": "enum", "values": ["immediate", "1-3_months", "3-6_months", "6+_months"]},
            "authority": {"type": "enum", "values": ["decision_maker", "influencer", "user"]},

            # Tracking
            "last_contacted": {"type": "timestamp"},
            "next_followup": {"type": "timestamp"},
            "notes": {"type": "text"}
        },
        default_patterns={
            "state_machine": {
                "states": ["new", "contacted", "qualified", "nurturing", "disqualified"],
                "transitions": {
                    "new->contacted": {"action": "initial_contact"},
                    "contacted->qualified": {"action": "qualify", "guard": "meets_criteria"},
                    "qualified->nurturing": {"action": "nurture"},
                    "nurturing->qualified": {"action": "requalify"},
                    "any->disqualified": {"action": "disqualify"}
                },
                "initial_state": "new"
            },
            "audit_trail": {
                "track_versions": True
            },
            "computed_fields": {
                "computed_fields": {
                    "qualified_score": {
                        "type": "expression",
                        "expression": "score + (10 if budget > 10000 else 0) + (5 if timeline == 'immediate' else 0)"
                    },
                    "days_since_last_contact": {
                        "type": "expression",
                        "expression": "(NOW() - last_contacted).days if last_contacted else None"
                    }
                }
            }
        },
        default_actions={
            "update_score": {
                "description": "Update lead score based on activity",
                "parameters": [
                    {"name": "points", "type": "integer"},
                    {"name": "reason", "type": "text"}
                ],
                "steps": [
                    {"type": "update", "entity": "Lead", "where": "id = $id", "fields": {"score": "score + $points"}},
                    {"type": "log", "message": "Lead score updated: +{points} points ({reason})"}
                ]
            },
            "schedule_followup": {
                "description": "Schedule next followup",
                "parameters": [
                    {"name": "followup_date", "type": "timestamp"},
                    {"name": "notes", "type": "text"}
                ],
                "steps": [
                    {"type": "update", "entity": "Lead", "where": "id = $id", "fields": {"next_followup": "$followup_date"}},
                    {"type": "log", "message": "Followup scheduled for {followup_date}"}
                ]
            }
        },
        configuration_options={
            "auto_qualification_threshold": {"type": "integer", "default": 50},
            "enable_auto_scoring": {"type": "boolean", "default": True}
        },
        icon="🎯",
        tags="crm,lead,qualification,sales"
    )

    print("✅ Seeded CRM Lead template")


def seed_crm_opportunity_template(library: PatternLibrary):
    """Seed CRM Opportunity entity template"""

    library.add_entity_template(
        template_name="opportunity",
        template_namespace="crm",
        description="CRM opportunity with pipeline management and forecasting",
        default_fields={
            # Core fields
            "name": {"type": "text", "required": True},
            "description": {"type": "text"},
            "contact": {"type": "ref", "entity": "Contact", "required": True},
            "account": {"type": "ref", "entity": "Account"},

            # Financial
            "amount": {"type": "decimal", "precision": 12, "scale": 2, "required": True},
            "currency": {"type": "text", "default": "USD"},
            "probability": {"type": "integer", "min": 0, "max": 100, "default": 50},

            # Pipeline
            "stage": {"type": "enum", "values": ["prospecting", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"]},
            "expected_close_date": {"type": "date"},
            "actual_close_date": {"type": "date"},

            # Assignment
            "owner": {"type": "ref", "entity": "User", "required": True},
            "team": {"type": "ref", "entity": "Team"},

            # Tracking
            "source": {"type": "text"},
            "campaign": {"type": "text"},
            "competitors": {"type": "array"},
            "next_steps": {"type": "text"}
        },
        default_patterns={
            "state_machine": {
                "states": ["prospecting", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"],
                "transitions": {
                    "prospecting->qualification": {"action": "qualify"},
                    "qualification->proposal": {"action": "create_proposal"},
                    "proposal->negotiation": {"action": "start_negotiation"},
                    "negotiation->closed_won": {"action": "win_deal"},
                    "negotiation->closed_lost": {"action": "lose_deal"},
                    "any->closed_lost": {"action": "disqualify"}
                },
                "initial_state": "prospecting"
            },
            "audit_trail": {
                "track_versions": True
            },
            "computed_fields": {
                "computed_fields": {
                    "weighted_amount": {
                        "type": "expression",
                        "expression": "amount * (probability / 100.0)"
                    },
                    "days_in_stage": {
                        "type": "expression",
                        "expression": "(NOW() - created_at).days if stage == created_at_stage else 0"
                    },
                    "forecast_category": {
                        "type": "expression",
                        "expression": "'commit' if probability >= 80 else 'best_case' if probability >= 50 else 'pipeline'"
                    }
                }
            },
            "approval_workflow": {
                "stages": [
                    {"name": "manager_approval", "approvers": ["manager"], "threshold": 50000},
                    {"name": "director_approval", "approvers": ["director"], "threshold": 100000}
                ],
                "auto_approve_threshold": 10000
            }
        },
        default_actions={
            "update_probability": {
                "description": "Update opportunity probability",
                "parameters": [
                    {"name": "probability", "type": "integer"},
                    {"name": "reason", "type": "text"}
                ],
                "steps": [
                    {"type": "validate", "condition": "probability >= 0 AND probability <= 100", "error": "Probability must be between 0 and 100"},
                    {"type": "update", "entity": "Opportunity", "where": "id = $id", "fields": {"probability": "$probability"}},
                    {"type": "log", "message": "Probability updated to {probability}%: {reason}"}
                ]
            },
            "change_stage": {
                "description": "Move opportunity to different stage",
                "parameters": [
                    {"name": "new_stage", "type": "text"},
                    {"name": "user_id", "type": "uuid"}
                ],
                "steps": [
                    {"type": "call", "function": "transition_to", "args": {"target_state": "$new_stage", "user_id": "$user_id"}},
                    {"type": "if", "condition": "new_stage IN ('closed_won', 'closed_lost')", "then": [
                        {"type": "update", "entity": "Opportunity", "where": "id = $id", "fields": {"actual_close_date": "NOW()"}}
                    ]}
                ]
            }
        },
        configuration_options={
            "enable_forecasting": {"type": "boolean", "default": True},
            "require_approval_workflow": {"type": "boolean", "default": True},
            "default_currency": {"type": "text", "default": "USD"}
        },
        icon="💰",
        tags="crm,opportunity,pipeline,sales,deals"
    )

    print("✅ Seeded CRM Opportunity template")


def seed_crm_account_template(library: PatternLibrary):
    """Seed CRM Account entity template"""

    library.add_entity_template(
        template_name="account",
        template_namespace="crm",
        description="CRM account/company with hierarchy and relationship management",
        default_fields={
            # Core fields
            "name": {"type": "text", "required": True},
            "description": {"type": "text"},
            "website": {"type": "url"},
            "industry": {"type": "enum", "values": ["technology", "healthcare", "finance", "manufacturing", "retail", "consulting", "other"]},
            "employee_count": {"type": "integer"},
            "annual_revenue": {"type": "decimal", "precision": 15, "scale": 2},

            # Address
            "billing_street": {"type": "text"},
            "billing_city": {"type": "text"},
            "billing_state": {"type": "text"},
            "billing_postal_code": {"type": "text"},
            "billing_country": {"type": "text", "default": "US"},

            # Classification
            "type": {"type": "enum", "values": ["prospect", "customer", "partner", "competitor"]},
            "status": {"type": "enum", "values": ["active", "inactive", "suspended"]},
            "rating": {"type": "enum", "values": ["hot", "warm", "cold"]},

            # Relationships
            "parent_account": {"type": "ref", "entity": "Account"},
            "primary_contact": {"type": "ref", "entity": "Contact"},

            # Metadata
            "tags": {"type": "array"},
            "notes": {"type": "text"}
        },
        default_patterns={
            "hierarchy_navigation": {
                "parent_field": "parent_account",
                "max_depth": 5,
                "enable_circular_check": True
            },
            "audit_trail": {
                "track_versions": True
            },
            "computed_fields": {
                "computed_fields": {
                    "total_opportunities": {
                        "type": "aggregate",
                        "query": "SELECT COUNT(*) FROM opportunities WHERE account_id = id AND stage NOT IN ('closed_lost')"
                    },
                    "total_revenue": {
                        "type": "aggregate",
                        "query": "SELECT SUM(amount) FROM opportunities WHERE account_id = id AND stage = 'closed_won'"
                    },
                    "account_health_score": {
                        "type": "expression",
                        "expression": "(total_opportunities * 10) + (total_revenue / 1000) + (20 if rating == 'hot' else 10 if rating == 'warm' else 0)"
                    }
                }
            },
            "tagging": {
                "enable_categories": True,
                "allow_custom_tags": True
            }
        },
        default_actions={
            "add_contact": {
                "description": "Add a contact to this account",
                "parameters": [
                    {"name": "contact_id", "type": "uuid"}
                ],
                "steps": [
                    {"type": "validate", "condition": "contact_id IS NOT NULL", "error": "Contact ID is required"},
                    {"type": "update", "entity": "Contact", "where": "id = $contact_id", "fields": {"company": "$id"}},
                    {"type": "log", "message": "Contact {contact_id} added to account {id}"}
                ]
            },
            "set_primary_contact": {
                "description": "Set the primary contact for this account",
                "parameters": [
                    {"name": "contact_id", "type": "uuid"}
                ],
                "steps": [
                    {"type": "validate", "condition": "contact_id IS NOT NULL", "error": "Contact ID is required"},
                    {"type": "update", "entity": "Account", "where": "id = $id", "fields": {"primary_contact": "$contact_id"}},
                    {"type": "log", "message": "Primary contact set to {contact_id}"}
                ]
            },
            "get_account_hierarchy": {
                "description": "Get the full account hierarchy",
                "steps": [
                    {"type": "call", "function": "get_tree", "args": {"root_id": "$id"}, "into": "hierarchy"},
                    {"type": "return", "value": "$hierarchy"}
                ]
            }
        },
        configuration_options={
            "enable_hierarchy": {"type": "boolean", "default": True},
            "max_hierarchy_depth": {"type": "integer", "default": 5},
            "require_primary_contact": {"type": "boolean", "default": False}
        },
        icon="🏢",
        tags="crm,account,company,hierarchy,organization"
    )

    print("✅ Seeded CRM Account template")


def seed_all_crm_templates(library: PatternLibrary):
    """Seed all CRM entity templates"""
    print("🌱 Seeding CRM entity templates...")

    seed_crm_contact_template(library)
    seed_crm_lead_template(library)
    seed_crm_opportunity_template(library)
    seed_crm_account_template(library)

    print("✅ All CRM templates seeded!")


def seed_ecommerce_product_template(library: PatternLibrary):
    """Seed E-Commerce Product entity template"""

    library.add_entity_template(
        template_name="product",
        template_namespace="ecommerce",
        description="E-commerce product with inventory, pricing, and variants",
        default_fields={
            # Core fields
            "name": {"type": "text", "required": True},
            "description": {"type": "text"},
            "sku": {"type": "text", "required": True, "unique": True},
            "upc": {"type": "text", "unique": True},

            # Pricing
            "price": {"type": "decimal", "precision": 10, "scale": 2, "required": True},
            "compare_at_price": {"type": "decimal", "precision": 10, "scale": 2},
            "cost_price": {"type": "decimal", "precision": 10, "scale": 2},
            "currency": {"type": "text", "default": "USD"},

            # Inventory
            "inventory_quantity": {"type": "integer", "default": 0},
            "inventory_policy": {"type": "enum", "values": ["deny", "allow"], "default": "deny"},
            "inventory_tracking": {"type": "boolean", "default": True},

            # Categories and tags
            "category": {"type": "ref", "entity": "Category"},
            "tags": {"type": "array"},
            "vendor": {"type": "text"},

            # Media
            "images": {"type": "array"},  # Array of image URLs
            "featured_image": {"type": "text"},

            # Variants
            "variants": {"type": "array"},  # Array of variant objects
            "options": {"type": "array"},   # Size, Color, etc.

            # Status
            "status": {"type": "enum", "values": ["active", "draft", "archived"], "default": "draft"},
            "published": {"type": "boolean", "default": False},
            "published_at": {"type": "timestamp"}
        },
        default_patterns={
            "audit_trail": {
                "track_versions": True
            },
            "soft_delete": {},
            "computed_fields": {
                "computed_fields": {
                    "profit_margin": {
                        "type": "expression",
                        "expression": "((price - cost_price) / price) * 100 if price > 0 else 0"
                    },
                    "is_in_stock": {
                        "type": "expression",
                        "expression": "inventory_quantity > 0 if inventory_tracking else True"
                    },
                    "on_sale": {
                        "type": "expression",
                        "expression": "compare_at_price is not None and compare_at_price > price"
                    },
                    "discount_percentage": {
                        "type": "expression",
                        "expression": "((compare_at_price - price) / compare_at_price) * 100 if compare_at_price and compare_at_price > price else 0"
                    }
                }
            },
            "search_optimization": {
                "full_text_fields": ["name", "description", "tags"],
                "searchable_fields": ["sku", "vendor", "category"]
            }
        },
        default_actions={
            "update_inventory": {
                "description": "Update product inventory",
                "parameters": [
                    {"name": "quantity", "type": "integer"},
                    {"name": "reason", "type": "text"}
                ],
                "steps": [
                    {"type": "update", "entity": "Product", "where": "id = $id", "fields": {"inventory_quantity": "$quantity"}},
                    {"type": "log", "message": "Inventory updated to {quantity}: {reason}"}
                ]
            },
            "publish_product": {
                "description": "Publish product to storefront",
                "steps": [
                    {"type": "validate", "condition": "status == 'draft'", "error": "Product must be in draft status"},
                    {"type": "validate", "condition": "name IS NOT NULL AND price IS NOT NULL", "error": "Name and price are required"},
                    {"type": "update", "entity": "Product", "where": "id = $id", "fields": {"status": "active", "published": True, "published_at": "NOW()"}},
                    {"type": "log", "message": "Product published"}
                ]
            },
            "add_variant": {
                "description": "Add product variant",
                "parameters": [
                    {"name": "variant_data", "type": "object"}
                ],
                "steps": [
                    {"type": "update", "entity": "Product", "where": "id = $id", "fields": {"variants": "variants || $variant_data"}},
                    {"type": "log", "message": "Variant added to product"}
                ]
            }
        },
        configuration_options={
            "enable_inventory_tracking": {"type": "boolean", "default": True},
            "allow_backorders": {"type": "boolean", "default": False},
            "default_currency": {"type": "text", "default": "USD"},
            "enable_variants": {"type": "boolean", "default": True}
        },
        icon="📦",
        tags="ecommerce,product,inventory,pricing,variants"
    )

    print("✅ Seeded E-Commerce Product template")


def seed_ecommerce_order_template(library: PatternLibrary):
    """Seed E-Commerce Order entity template"""

    library.add_entity_template(
        template_name="order",
        template_namespace="ecommerce",
        description="E-commerce order with state machine, payments, and fulfillment",
        default_fields={
            # Core fields
            "order_number": {"type": "text", "required": True, "unique": True},
            "customer": {"type": "ref", "entity": "Customer", "required": True},

            # Financial
            "subtotal": {"type": "decimal", "precision": 10, "scale": 2, "required": True},
            "tax_amount": {"type": "decimal", "precision": 10, "scale": 2, "default": 0},
            "shipping_amount": {"type": "decimal", "precision": 10, "scale": 2, "default": 0},
            "discount_amount": {"type": "decimal", "precision": 10, "scale": 2, "default": 0},
            "total": {"type": "decimal", "precision": 10, "scale": 2, "required": True},
            "currency": {"type": "text", "default": "USD"},

            # Items
            "line_items": {"type": "array", "required": True},  # Array of order line items

            # Addresses
            "billing_address": {"type": "object", "required": True},
            "shipping_address": {"type": "object", "required": True},

            # Payment
            "payment_method": {"type": "text"},
            "payment_status": {"type": "enum", "values": ["pending", "paid", "failed", "refunded"], "default": "pending"},
            "payment_id": {"type": "text"},

            # Shipping
            "shipping_method": {"type": "text"},
            "tracking_number": {"type": "text"},
            "shipped_at": {"type": "timestamp"},
            "delivered_at": {"type": "timestamp"},

            # Metadata
            "notes": {"type": "text"},
            "tags": {"type": "array"}
        },
        default_patterns={
            "state_machine": {
                "states": ["pending", "confirmed", "paid", "processing", "shipped", "delivered", "cancelled", "refunded"],
                "transitions": {
                    "pending->confirmed": {"action": "confirm_order"},
                    "confirmed->paid": {"action": "process_payment"},
                    "paid->processing": {"action": "start_processing"},
                    "processing->shipped": {"action": "ship_order"},
                    "shipped->delivered": {"action": "deliver_order"},
                    "any->cancelled": {"action": "cancel_order"},
                    "paid->refunded": {"action": "refund_order"}
                },
                "initial_state": "pending"
            },
            "audit_trail": {
                "track_versions": True
            },
            "computed_fields": {
                "computed_fields": {
                    "item_count": {
                        "type": "expression",
                        "expression": "sum(item.quantity for item in line_items)"
                    },
                    "is_fulfilled": {
                        "type": "expression",
                        "expression": "status in ('shipped', 'delivered')"
                    },
                    "days_to_delivery": {
                        "type": "expression",
                        "expression": "(delivered_at - created_at).days if delivered_at else None"
                    }
                }
            }
        },
        default_actions={
            "add_line_item": {
                "description": "Add item to order",
                "parameters": [
                    {"name": "product_id", "type": "uuid"},
                    {"name": "quantity", "type": "integer"},
                    {"name": "price", "type": "decimal"}
                ],
                "steps": [
                    {"type": "validate", "condition": "quantity > 0", "error": "Quantity must be positive"},
                    {"type": "query", "sql": "SELECT inventory_quantity, inventory_policy FROM products WHERE id = $product_id", "into": "product"},
                    {"type": "validate", "condition": "product.inventory_quantity >= quantity OR product.inventory_policy == 'allow'", "error": "Insufficient inventory"},
                    {"type": "update", "entity": "Order", "where": "id = $id", "fields": {"line_items": "line_items || {'product_id': $product_id, 'quantity': $quantity, 'price': $price}"}},
                    {"type": "update", "entity": "Product", "where": "id = $product_id", "fields": {"inventory_quantity": "inventory_quantity - $quantity"}},
                    {"type": "call", "function": "recalculate_total"}
                ]
            },
            "recalculate_total": {
                "description": "Recalculate order total",
                "steps": [
                    {"type": "query", "sql": "SELECT line_items FROM orders WHERE id = $id", "into": "order_data"},
                    {"type": "assign", "variable": "subtotal", "value": "sum(item.price * item.quantity for item in order_data.line_items)"},
                    {"type": "assign", "variable": "tax_amount", "value": "subtotal * 0.08"},  # 8% tax
                    {"type": "assign", "variable": "total", "value": "subtotal + tax_amount + shipping_amount - discount_amount"},
                    {"type": "update", "entity": "Order", "where": "id = $id", "fields": {"subtotal": "$subtotal", "tax_amount": "$tax_amount", "total": "$total"}}
                ]
            },
            "process_refund": {
                "description": "Process order refund",
                "parameters": [
                    {"name": "refund_amount", "type": "decimal"},
                    {"name": "reason", "type": "text"}
                ],
                "steps": [
                    {"type": "validate", "condition": "status == 'paid'", "error": "Can only refund paid orders"},
                    {"type": "validate", "condition": "refund_amount <= total", "error": "Refund amount cannot exceed order total"},
                    {"type": "call", "function": "transition_to", "args": {"target_state": "refunded"}},
                    {"type": "log", "message": "Order refunded: ${refund_amount} - {reason}"}
                ]
            }
        },
        configuration_options={
            "auto_confirm_orders": {"type": "boolean", "default": True},
            "default_currency": {"type": "text", "default": "USD"},
            "tax_rate": {"type": "decimal", "default": 0.08},
            "enable_inventory_deduction": {"type": "boolean", "default": True}
        },
        icon="🛒",
        tags="ecommerce,order,payment,shipping,fulfillment"
    )

    print("✅ Seeded E-Commerce Order template")


def seed_ecommerce_cart_template(library: PatternLibrary):
    """Seed E-Commerce Cart entity template"""

    library.add_entity_template(
        template_name="cart",
        template_namespace="ecommerce",
        description="Shopping cart with expiration, calculation, and conversion tracking",
        default_fields={
            # Core fields
            "customer": {"type": "ref", "entity": "Customer"},
            "session_id": {"type": "text", "required": True},

            # Items
            "line_items": {"type": "array", "default": []},

            # Financial
            "subtotal": {"type": "decimal", "precision": 10, "scale": 2, "default": 0},
            "tax_amount": {"type": "decimal", "precision": 10, "scale": 2, "default": 0},
            "shipping_amount": {"type": "decimal", "precision": 10, "scale": 2, "default": 0},
            "discount_amount": {"type": "decimal", "precision": 10, "scale": 2, "default": 0},
            "total": {"type": "decimal", "precision": 10, "scale": 2, "default": 0},
            "currency": {"type": "text", "default": "USD"},

            # Discounts
            "discount_codes": {"type": "array"},

            # Expiration
            "expires_at": {"type": "timestamp", "required": True},

            # Conversion
            "converted_to_order": {"type": "ref", "entity": "Order"},
            "converted_at": {"type": "timestamp"}
        },
        default_patterns={
            "audit_trail": {
                "track_versions": False  # Carts don't need full versioning
            },
            "computed_fields": {
                "computed_fields": {
                    "item_count": {
                        "type": "expression",
                        "expression": "sum(item.quantity for item in line_items)"
                    },
                    "is_expired": {
                        "type": "expression",
                        "expression": "NOW() > expires_at"
                    },
                    "is_empty": {
                        "type": "expression",
                        "expression": "len(line_items) == 0"
                    },
                    "conversion_rate": {
                        "type": "expression",
                        "expression": "1.0 if converted_to_order else 0.0"
                    }
                }
            },
            "scheduling": {
                "cleanup_schedule": "daily",
                "cleanup_condition": "is_expired AND NOT converted_to_order"
            }
        },
        default_actions={
            "add_item": {
                "description": "Add item to cart",
                "parameters": [
                    {"name": "product_id", "type": "uuid"},
                    {"name": "quantity", "type": "integer"},
                    {"name": "variant_id", "type": "uuid"}
                ],
                "steps": [
                    {"type": "validate", "condition": "quantity > 0", "error": "Quantity must be positive"},
                    {"type": "query", "sql": "SELECT id, price, inventory_quantity FROM products WHERE id = $product_id", "into": "product"},
                    {"type": "validate", "condition": "product.id IS NOT NULL", "error": "Product not found"},
                    {"type": "assign", "variable": "existing_item", "value": "next((item for item in line_items if item.product_id == product_id and item.variant_id == variant_id), None)"},
                    {"type": "if", "condition": "existing_item", "then": [
                        {"type": "update", "entity": "Cart", "where": "id = $id", "fields": {"line_items": "update_item_quantity(line_items, product_id, variant_id, existing_item.quantity + quantity)"}}
                    ], "else": [
                        {"type": "update", "entity": "Cart", "where": "id = $id", "fields": {"line_items": "line_items || {'product_id': $product_id, 'quantity': $quantity, 'price': product.price, 'variant_id': $variant_id}"}}
                    ]},
                    {"type": "call", "function": "recalculate_total"},
                    {"type": "update", "entity": "Cart", "where": "id = $id", "fields": {"expires_at": "NOW() + INTERVAL '24 hours'"}}
                ]
            },
            "remove_item": {
                "description": "Remove item from cart",
                "parameters": [
                    {"name": "product_id", "type": "uuid"},
                    {"name": "variant_id", "type": "uuid"}
                ],
                "steps": [
                    {"type": "update", "entity": "Cart", "where": "id = $id", "fields": {"line_items": "remove_item(line_items, product_id, variant_id)"}},
                    {"type": "call", "function": "recalculate_total"}
                ]
            },
            "apply_discount": {
                "description": "Apply discount code to cart",
                "parameters": [
                    {"name": "code", "type": "text"}
                ],
                "steps": [
                    {"type": "query", "sql": "SELECT * FROM discount_codes WHERE code = $code AND active = true", "into": "discount"},
                    {"type": "validate", "condition": "discount.id IS NOT NULL", "error": "Invalid discount code"},
                    {"type": "validate", "condition": "code NOT IN discount_codes", "error": "Discount code already applied"},
                    {"type": "update", "entity": "Cart", "where": "id = $id", "fields": {"discount_codes": "discount_codes || $code"}},
                    {"type": "call", "function": "recalculate_total"}
                ]
            },
            "convert_to_order": {
                "description": "Convert cart to order",
                "parameters": [
                    {"name": "billing_address", "type": "object"},
                    {"name": "shipping_address", "type": "object"}
                ],
                "steps": [
                    {"type": "validate", "condition": "NOT is_expired", "error": "Cart has expired"},
                    {"type": "validate", "condition": "NOT is_empty", "error": "Cart is empty"},
                    {"type": "validate", "condition": "customer IS NOT NULL", "error": "Customer is required"},
                    {"type": "create", "entity": "Order", "data": {
                        "customer": "$customer",
                        "line_items": "$line_items",
                        "billing_address": "$billing_address",
                        "shipping_address": "$shipping_address",
                        "subtotal": "$subtotal",
                        "total": "$total"
                    }, "into": "order_id"},
                    {"type": "update", "entity": "Cart", "where": "id = $id", "fields": {"converted_to_order": "$order_id", "converted_at": "NOW()"}},
                    {"type": "return", "value": "$order_id"}
                ]
            },
            "recalculate_total": {
                "description": "Recalculate cart total",
                "steps": [
                    {"type": "assign", "variable": "subtotal", "value": "sum(item.price * item.quantity for item in line_items)"},
                    {"type": "assign", "variable": "discount_amount", "value": "calculate_discount_amount(subtotal, discount_codes)"},
                    {"type": "assign", "variable": "tax_amount", "value": "(subtotal - discount_amount) * 0.08"},
                    {"type": "assign", "variable": "total", "value": "subtotal - discount_amount + tax_amount + shipping_amount"},
                    {"type": "update", "entity": "Cart", "where": "id = $id", "fields": {"subtotal": "$subtotal", "discount_amount": "$discount_amount", "tax_amount": "$tax_amount", "total": "$total"}}
                ]
            }
        },
        configuration_options={
            "cart_expiration_hours": {"type": "integer", "default": 24},
            "max_items_per_cart": {"type": "integer", "default": 50},
            "enable_discount_codes": {"type": "boolean", "default": True},
            "tax_rate": {"type": "decimal", "default": 0.08}
        },
        icon="🛒",
        tags="ecommerce,cart,shopping,checkout,conversion"
    )

    print("✅ Seeded E-Commerce Cart template")


def seed_ecommerce_customer_template(library: PatternLibrary):
    """Seed E-Commerce Customer entity template"""

    library.add_entity_template(
        template_name="customer",
        template_namespace="ecommerce",
        description="E-commerce customer with loyalty, payment methods, and order history",
        default_fields={
            # Core fields
            "first_name": {"type": "text", "required": True},
            "last_name": {"type": "text", "required": True},
            "email": {"type": "email", "required": True, "unique": True},
            "phone": {"type": "text"},

            # Addresses
            "default_billing_address": {"type": "object"},
            "default_shipping_address": {"type": "object"},
            "saved_addresses": {"type": "array"},

            # Payment methods
            "payment_methods": {"type": "array"},  # Array of payment method objects
            "default_payment_method": {"type": "object"},

            # Loyalty and preferences
            "loyalty_points": {"type": "integer", "default": 0},
            "loyalty_tier": {"type": "enum", "values": ["bronze", "silver", "gold", "platinum"], "default": "bronze"},
            "total_spent": {"type": "decimal", "precision": 10, "scale": 2, "default": 0},
            "order_count": {"type": "integer", "default": 0},
            "last_order_date": {"type": "timestamp"},

            # Preferences
            "marketing_opt_in": {"type": "boolean", "default": True},
            "preferred_currency": {"type": "text", "default": "USD"},
            "preferred_language": {"type": "text", "default": "en"},
            "tags": {"type": "array"},

            # Status
            "status": {"type": "enum", "values": ["active", "inactive", "suspended"], "default": "active"},
            "email_verified": {"type": "boolean", "default": False},
            "email_verified_at": {"type": "timestamp"}
        },
        default_patterns={
            "audit_trail": {
                "track_versions": True
            },
            "soft_delete": {},
            "computed_fields": {
                "computed_fields": {
                    "full_name": {
                        "type": "expression",
                        "expression": "first_name + ' ' + last_name"
                    },
                    "average_order_value": {
                        "type": "expression",
                        "expression": "total_spent / order_count if order_count > 0 else 0"
                    },
                    "customer_lifetime_value": {
                        "type": "expression",
                        "expression": "total_spent * 1.5"  # Estimated CLV calculation
                    },
                    "days_since_last_order": {
                        "type": "expression",
                        "expression": "(NOW() - last_order_date).days if last_order_date else None"
                    },
                    "loyalty_tier_threshold": {
                        "type": "expression",
                        "expression": "'gold' if total_spent > 1000 else 'silver' if total_spent > 500 else 'bronze'"
                    }
                }
            },
            "tagging": {
                "enable_categories": True,
                "allow_custom_tags": True
            }
        },
        default_actions={
            "add_payment_method": {
                "description": "Add payment method to customer",
                "parameters": [
                    {"name": "payment_data", "type": "object"}
                ],
                "steps": [
                    {"type": "validate", "condition": "payment_data.type IN ('credit_card', 'paypal', 'bank_account')", "error": "Invalid payment method type"},
                    {"type": "update", "entity": "Customer", "where": "id = $id", "fields": {"payment_methods": "payment_methods || $payment_data"}},
                    {"type": "log", "message": "Payment method added"}
                ]
            },
            "update_loyalty_points": {
                "description": "Update customer loyalty points",
                "parameters": [
                    {"name": "points", "type": "integer"},
                    {"name": "reason", "type": "text"}
                ],
                "steps": [
                    {"type": "update", "entity": "Customer", "where": "id = $id", "fields": {"loyalty_points": "loyalty_points + $points"}},
                    {"type": "call", "function": "update_loyalty_tier"},
                    {"type": "log", "message": "Loyalty points updated: {points} ({reason})"}
                ]
            },
            "update_loyalty_tier": {
                "description": "Update customer loyalty tier based on spending",
                "steps": [
                    {"type": "assign", "variable": "new_tier", "value": "'platinum' if total_spent > 5000 else 'gold' if total_spent > 2000 else 'silver' if total_spent > 500 else 'bronze'"},
                    {"type": "if", "condition": "new_tier != loyalty_tier", "then": [
                        {"type": "update", "entity": "Customer", "where": "id = $id", "fields": {"loyalty_tier": "$new_tier"}},
                        {"type": "log", "message": "Loyalty tier updated to {new_tier}"}
                    ]}
                ]
            },
            "record_order": {
                "description": "Record a completed order for customer",
                "parameters": [
                    {"name": "order_total", "type": "decimal"},
                    {"name": "order_date", "type": "timestamp"}
                ],
                "steps": [
                    {"type": "update", "entity": "Customer", "where": "id = $id", "fields": {
                        "total_spent": "total_spent + $order_total",
                        "order_count": "order_count + 1",
                        "last_order_date": "$order_date"
                    }},
                    {"type": "call", "function": "update_loyalty_points", "args": {"points": "floor(order_total / 10)", "reason": "Order completion"}},  # 1 point per $10
                    {"type": "call", "function": "update_loyalty_tier"}
                ]
            },
            "add_address": {
                "description": "Add address to customer",
                "parameters": [
                    {"name": "address_data", "type": "object"},
                    {"name": "set_as_default", "type": "boolean", "default": False}
                ],
                "steps": [
                    {"type": "update", "entity": "Customer", "where": "id = $id", "fields": {"saved_addresses": "saved_addresses || $address_data"}},
                    {"type": "if", "condition": "set_as_default", "then": [
                        {"type": "update", "entity": "Customer", "where": "id = $id", "fields": {"default_shipping_address": "$address_data", "default_billing_address": "$address_data"}}
                    ]}
                ]
            }
        },
        configuration_options={
            "enable_loyalty_program": {"type": "boolean", "default": True},
            "points_per_dollar": {"type": "decimal", "default": 0.1},
            "tier_thresholds": {"type": "object", "default": {"silver": 500, "gold": 2000, "platinum": 5000}},
            "require_email_verification": {"type": "boolean", "default": True}
        },
        icon="👤",
        tags="ecommerce,customer,loyalty,payment,orders"
    )

    print("✅ Seeded E-Commerce Customer template")


def seed_all_ecommerce_templates(library: PatternLibrary):
    """Seed all E-Commerce entity templates"""
    print("🌱 Seeding E-Commerce entity templates...")

    seed_ecommerce_product_template(library)
    seed_ecommerce_order_template(library)
    seed_ecommerce_cart_template(library)
    seed_ecommerce_customer_template(library)

    print("✅ All E-Commerce templates seeded!")


def seed_healthcare_patient_template(library: PatternLibrary):
    """Seed Healthcare Patient entity template"""

    library.add_entity_template(
        template_name="patient",
        template_namespace="healthcare",
        description="Healthcare patient with privacy, consent, and medical records",
        default_fields={
            # Personal Information
            "first_name": {"type": "text", "required": True},
            "last_name": {"type": "text", "required": True},
            "date_of_birth": {"type": "date", "required": True},
            "gender": {"type": "enum", "values": ["male", "female", "other", "prefer_not_to_say"]},
            "ssn": {"type": "text", "encrypted": True},  # PHI - encrypted

            # Contact Information
            "email": {"type": "email"},
            "phone": {"type": "text"},
            "emergency_contact": {"type": "object"},  # {name, relationship, phone}

            # Address
            "address": {"type": "object"},

            # Medical Information
            "medical_record_number": {"type": "text", "required": True, "unique": True},
            "blood_type": {"type": "enum", "values": ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]},
            "allergies": {"type": "array"},
            "current_medications": {"type": "array"},
            "chronic_conditions": {"type": "array"},
            "insurance_provider": {"type": "text"},
            "insurance_id": {"type": "text", "encrypted": True},

            # Consent and Privacy
            "consent_given": {"type": "boolean", "default": False},
            "consent_date": {"type": "timestamp"},
            "hipaa_authorization": {"type": "boolean", "default": False},
            "privacy_restrictions": {"type": "array"},

            # Status
            "status": {"type": "enum", "values": ["active", "inactive", "deceased"], "default": "active"},
            "last_visit_date": {"type": "timestamp"},
            "next_appointment_date": {"type": "timestamp"}
        },
        default_patterns={
            "audit_trail": {
                "track_versions": True
            },
            "soft_delete": {},
            "computed_fields": {
                "computed_fields": {
                    "full_name": {
                        "type": "expression",
                        "expression": "first_name + ' ' + last_name"
                    },
                    "age": {
                        "type": "expression",
                        "expression": "(NOW() - date_of_birth).years"
                    },
                    "is_minor": {
                        "type": "expression",
                        "expression": "age < 18"
                    },
                    "days_since_last_visit": {
                        "type": "expression",
                        "expression": "(NOW() - last_visit_date).days if last_visit_date else None"
                    }
                }
            },
            "internationalization": {
                "fields": ["first_name", "last_name", "address"],
                "supported_languages": ["en", "es", "fr"]
            }
        },
        default_actions={
            "update_medical_record": {
                "description": "Update patient medical record",
                "parameters": [
                    {"name": "updates", "type": "object"},
                    {"name": "provider_id", "type": "uuid"}
                ],
                "steps": [
                    {"type": "validate", "condition": "consent_given", "error": "Patient consent required"},
                    {"type": "validate", "condition": "hipaa_authorization", "error": "HIPAA authorization required"},
                    {"type": "update", "entity": "Patient", "where": "id = $id", "fields": "$updates"},
                    {"type": "log", "message": "Medical record updated by provider {provider_id}"}
                ]
            },
            "record_visit": {
                "description": "Record patient visit",
                "parameters": [
                    {"name": "visit_date", "type": "timestamp"},
                    {"name": "provider_id", "type": "uuid"},
                    {"name": "notes", "type": "text"}
                ],
                "steps": [
                    {"type": "update", "entity": "Patient", "where": "id = $id", "fields": {"last_visit_date": "$visit_date"}},
                    {"type": "create", "entity": "Visit", "data": {
                        "patient_id": "$id",
                        "provider_id": "$provider_id",
                        "visit_date": "$visit_date",
                        "notes": "$notes"
                    }},
                    {"type": "log", "message": "Visit recorded for patient"}
                ]
            },
            "grant_consent": {
                "description": "Grant patient consent for treatment",
                "steps": [
                    {"type": "update", "entity": "Patient", "where": "id = $id", "fields": {"consent_given": True, "consent_date": "NOW()"}},
                    {"type": "log", "message": "Patient consent granted"}
                ]
            },
            "add_allergy": {
                "description": "Add allergy to patient record",
                "parameters": [
                    {"name": "allergy", "type": "text"},
                    {"name": "severity", "type": "enum", "values": ["mild", "moderate", "severe"]}
                ],
                "steps": [
                    {"type": "update", "entity": "Patient", "where": "id = $id", "fields": {"allergies": "allergies || {'allergy': $allergy, 'severity': $severity, 'date_added': NOW()}"}},
                    {"type": "log", "message": "Allergy added: {allergy} ({severity})"}
                ]
            }
        },
        configuration_options={
            "require_consent": {"type": "boolean", "default": True},
            "enable_phi_encryption": {"type": "boolean", "default": True},
            "hipaa_compliance_mode": {"type": "boolean", "default": True},
            "allow_minors": {"type": "boolean", "default": True}
        },
        icon="🏥",
        tags="healthcare,patient,medical,phi,hipaa,consent"
    )

    print("✅ Seeded Healthcare Patient template")


def seed_healthcare_appointment_template(library: PatternLibrary):
    """Seed Healthcare Appointment entity template"""

    library.add_entity_template(
        template_name="appointment",
        template_namespace="healthcare",
        description="Healthcare appointment with scheduling, reminders, and status tracking",
        default_fields={
            # Core fields
            "patient": {"type": "ref", "entity": "Patient", "required": True},
            "provider": {"type": "ref", "entity": "Provider", "required": True},
            "appointment_type": {"type": "enum", "values": ["consultation", "follow_up", "procedure", "checkup", "emergency"], "required": True},

            # Scheduling
            "scheduled_date": {"type": "timestamp", "required": True},
            "duration_minutes": {"type": "integer", "default": 30},
            "end_time": {"type": "timestamp"},

            # Status
            "status": {"type": "enum", "values": ["scheduled", "confirmed", "in_progress", "completed", "cancelled", "no_show"], "default": "scheduled"},
            "check_in_time": {"type": "timestamp"},
            "start_time": {"type": "timestamp"},
            "end_time_actual": {"type": "timestamp"},

            # Details
            "reason": {"type": "text"},
            "notes": {"type": "text"},
            "room": {"type": "text"},
            "equipment_needed": {"type": "array"},

            # Follow-up
            "follow_up_required": {"type": "boolean", "default": False},
            "follow_up_date": {"type": "timestamp"},
            "referral_to": {"type": "ref", "entity": "Provider"},

            # Communication
            "reminder_sent": {"type": "boolean", "default": False},
            "reminder_sent_at": {"type": "timestamp"},
            "confirmation_sent": {"type": "boolean", "default": False}
        },
        default_patterns={
            "state_machine": {
                "states": ["scheduled", "confirmed", "in_progress", "completed", "cancelled", "no_show"],
                "transitions": {
                    "scheduled->confirmed": {"action": "confirm_appointment"},
                    "confirmed->in_progress": {"action": "check_in"},
                    "in_progress->completed": {"action": "complete_appointment"},
                    "any->cancelled": {"action": "cancel_appointment"},
                    "confirmed->no_show": {"action": "mark_no_show"}
                },
                "initial_state": "scheduled"
            },
            "audit_trail": {
                "track_versions": True
            },
            "computed_fields": {
                "computed_fields": {
                    "is_overdue": {
                        "type": "expression",
                        "expression": "NOW() > scheduled_date and status in ('scheduled', 'confirmed')"
                    },
                    "duration_actual": {
                        "type": "expression",
                        "expression": "(end_time_actual - start_time).minutes if start_time and end_time_actual else None"
                    },
                    "wait_time": {
                        "type": "expression",
                        "expression": "(start_time - check_in_time).minutes if check_in_time and start_time else None"
                    }
                }
            },
            "scheduling": {
                "reminder_schedule": "24_hours_before",
                "confirmation_deadline": "48_hours_before"
            },
            "notification": {
                "events": ["scheduled", "confirmed", "reminder", "cancelled"],
                "channels": ["email", "sms", "app"]
            }
        },
        default_actions={
            "schedule_appointment": {
                "description": "Schedule new appointment",
                "parameters": [
                    {"name": "patient_id", "type": "uuid"},
                    {"name": "provider_id", "type": "uuid"},
                    {"name": "appointment_type", "type": "text"},
                    {"name": "scheduled_date", "type": "timestamp"},
                    {"name": "duration", "type": "integer"}
                ],
                "steps": [
                    {"type": "validate", "condition": "scheduled_date > NOW()", "error": "Cannot schedule appointments in the past"},
                    {"type": "query", "sql": "SELECT id FROM appointments WHERE provider_id = $provider_id AND scheduled_date <= $scheduled_date AND end_time > $scheduled_date", "into": "conflicts"},
                    {"type": "validate", "condition": "len(conflicts) == 0", "error": "Provider has scheduling conflict"},
                    {"type": "create", "entity": "Appointment", "data": {
                        "patient": "$patient_id",
                        "provider": "$provider_id",
                        "appointment_type": "$appointment_type",
                        "scheduled_date": "$scheduled_date",
                        "duration_minutes": "$duration",
                        "end_time": "$scheduled_date + INTERVAL '$duration minutes'"
                    }},
                    {"type": "call", "function": "send_confirmation"}
                ]
            },
            "reschedule_appointment": {
                "description": "Reschedule existing appointment",
                "parameters": [
                    {"name": "new_date", "type": "timestamp"},
                    {"name": "reason", "type": "text"}
                ],
                "steps": [
                    {"type": "validate", "condition": "status IN ('scheduled', 'confirmed')", "error": "Cannot reschedule appointment with status: {status}"},
                    {"type": "query", "sql": "SELECT id FROM appointments WHERE provider_id = provider AND new_date <= $new_date AND end_time > $new_date", "into": "conflicts"},
                    {"type": "validate", "condition": "len(conflicts) == 0", "error": "Provider has scheduling conflict"},
                    {"type": "update", "entity": "Appointment", "where": "id = $id", "fields": {"scheduled_date": "$new_date", "end_time": "$new_date + INTERVAL 'duration_minutes minutes'"}},
                    {"type": "log", "message": "Appointment rescheduled: {reason}"},
                    {"type": "call", "function": "send_reschedule_notification"}
                ]
            },
            "check_in_patient": {
                "description": "Check in patient for appointment",
                "steps": [
                    {"type": "validate", "condition": "status == 'confirmed'", "error": "Appointment must be confirmed"},
                    {"type": "validate", "condition": "scheduled_date <= NOW() + INTERVAL '15 minutes'", "error": "Too early to check in"},
                    {"type": "update", "entity": "Appointment", "where": "id = $id", "fields": {"check_in_time": "NOW()", "status": "in_progress", "start_time": "NOW()"}},
                    {"type": "log", "message": "Patient checked in"}
                ]
            },
            "send_reminder": {
                "description": "Send appointment reminder",
                "steps": [
                    {"type": "validate", "condition": "NOT reminder_sent", "error": "Reminder already sent"},
                    {"type": "query", "sql": "SELECT email, phone FROM patients WHERE id = patient", "into": "patient_contact"},
                    {"type": "notify", "recipients": ["$patient_contact.email"], "message": "Appointment reminder: {scheduled_date} with {provider.name}"},
                    {"type": "update", "entity": "Appointment", "where": "id = $id", "fields": {"reminder_sent": True, "reminder_sent_at": "NOW()"}}
                ]
            }
        },
        configuration_options={
            "enable_reminders": {"type": "boolean", "default": True},
            "reminder_hours_before": {"type": "integer", "default": 24},
            "allow_rescheduling": {"type": "boolean", "default": True},
            "check_in_window_minutes": {"type": "integer", "default": 15}
        },
        icon="📅",
        tags="healthcare,appointment,scheduling,reminder,calendar"
    )

    print("✅ Seeded Healthcare Appointment template")


def seed_healthcare_prescription_template(library: PatternLibrary):
    """Seed Healthcare Prescription entity template"""

    library.add_entity_template(
        template_name="prescription",
        template_namespace="healthcare",
        description="Healthcare prescription with validation, refills, and tracking",
        default_fields={
            # Core fields
            "patient": {"type": "ref", "entity": "Patient", "required": True},
            "provider": {"type": "ref", "entity": "Provider", "required": True},
            "medication": {"type": "text", "required": True},
            "dosage": {"type": "text", "required": True},
            "frequency": {"type": "text", "required": True},  # e.g., "twice daily", "every 8 hours"

            # Prescription details
            "quantity": {"type": "integer", "required": True},
            "refills_allowed": {"type": "integer", "default": 0},
            "refills_remaining": {"type": "integer", "default": 0},
            "days_supply": {"type": "integer", "required": True},

            # Dates
            "prescribed_date": {"type": "timestamp", "default": "NOW()"},
            "start_date": {"type": "timestamp", "required": True},
            "end_date": {"type": "timestamp"},

            # Status and tracking
            "status": {"type": "enum", "values": ["active", "completed", "cancelled", "expired"], "default": "active"},
            "filled_date": {"type": "timestamp"},
            "last_refill_date": {"type": "timestamp"},
            "pharmacy": {"type": "text"},

            # Instructions
            "instructions": {"type": "text"},
            "indications": {"type": "text"},  # What it's for
            "warnings": {"type": "text"},

            # Controlled substance info (if applicable)
            "controlled_substance": {"type": "boolean", "default": False},
            "dea_schedule": {"type": "enum", "values": ["II", "III", "IV", "V"]},

            # Pharmacy info
            "rx_number": {"type": "text"},  # Pharmacy prescription number
            "filled_quantity": {"type": "integer"}
        },
        default_patterns={
            "state_machine": {
                "states": ["active", "completed", "cancelled", "expired"],
                "transitions": {
                    "active->completed": {"action": "complete_prescription"},
                    "active->cancelled": {"action": "cancel_prescription"},
                    "active->expired": {"action": "expire_prescription"}
                },
                "initial_state": "active"
            },
            "audit_trail": {
                "track_versions": True
            },
            "computed_fields": {
                "computed_fields": {
                    "is_expired": {
                        "type": "expression",
                        "expression": "NOW() > end_date if end_date else False"
                    },
                    "days_remaining": {
                        "type": "expression",
                        "expression": "(end_date - NOW()).days if end_date else None"
                    },
                    "can_refill": {
                        "type": "expression",
                        "expression": "refills_remaining > 0 and not is_expired and status == 'active'"
                    },
                    "adherence_rate": {
                        "type": "expression",
                        "expression": "filled_quantity / quantity if filled_quantity else 0"
                    }
                }
            },
            "validation_chain": {
                "rules": [
                    {"field": "medication", "rule": "not_empty", "error": "Medication is required"},
                    {"field": "dosage", "rule": "not_empty", "error": "Dosage is required"},
                    {"field": "quantity", "rule": "positive_integer", "error": "Quantity must be positive"},
                    {"field": "controlled_substance", "rule": "dea_validation", "error": "DEA validation required for controlled substances"}
                ]
            }
        },
        default_actions={
            "prescribe_medication": {
                "description": "Create new prescription",
                "parameters": [
                    {"name": "patient_id", "type": "uuid"},
                    {"name": "medication", "type": "text"},
                    {"name": "dosage", "type": "text"},
                    {"name": "frequency", "type": "text"},
                    {"name": "quantity", "type": "integer"},
                    {"name": "days_supply", "type": "integer"},
                    {"name": "refills", "type": "integer"}
                ],
                "steps": [
                    {"type": "validate", "condition": "quantity > 0", "error": "Quantity must be positive"},
                    {"type": "validate", "condition": "days_supply > 0", "error": "Days supply must be positive"},
                    {"type": "create", "entity": "Prescription", "data": {
                        "patient": "$patient_id",
                        "provider": "$id",  # Assuming called by provider
                        "medication": "$medication",
                        "dosage": "$dosage",
                        "frequency": "$frequency",
                        "quantity": "$quantity",
                        "days_supply": "$days_supply",
                        "refills_allowed": "$refills",
                        "refills_remaining": "$refills",
                        "start_date": "NOW()",
                        "end_date": "NOW() + INTERVAL '$days_supply days'"
                    }},
                    {"type": "log", "message": "Prescription created: {medication} {dosage}"}
                ]
            },
            "refill_prescription": {
                "description": "Process prescription refill",
                "steps": [
                    {"type": "validate", "condition": "can_refill", "error": "Prescription cannot be refilled"},
                    {"type": "validate", "condition": "last_refill_date IS NULL OR NOW() > last_refill_date + INTERVAL '1 day'", "error": "Too soon for refill"},
                    {"type": "update", "entity": "Prescription", "where": "id = $id", "fields": {
                        "refills_remaining": "refills_remaining - 1",
                        "last_refill_date": "NOW()",
                        "end_date": "NOW() + INTERVAL 'days_supply days'"
                    }},
                    {"type": "log", "message": "Prescription refilled, {refills_remaining} refills remaining"}
                ]
            },
            "discontinue_prescription": {
                "description": "Discontinue prescription",
                "parameters": [
                    {"name": "reason", "type": "text"}
                ],
                "steps": [
                    {"type": "validate", "condition": "status == 'active'", "error": "Prescription is not active"},
                    {"type": "call", "function": "transition_to", "args": {"target_state": "cancelled"}},
                    {"type": "log", "message": "Prescription discontinued: {reason}"}
                ]
            },
            "record_fill": {
                "description": "Record prescription fill at pharmacy",
                "parameters": [
                    {"name": "pharmacy", "type": "text"},
                    {"name": "quantity_filled", "type": "integer"},
                    {"name": "rx_number", "type": "text"}
                ],
                "steps": [
                    {"type": "update", "entity": "Prescription", "where": "id = $id", "fields": {
                        "filled_date": "NOW()",
                        "pharmacy": "$pharmacy",
                        "filled_quantity": "$quantity_filled",
                        "rx_number": "$rx_number"
                    }},
                    {"type": "log", "message": "Prescription filled at {pharmacy}: {quantity_filled} units"}
                ]
            }
        },
        configuration_options={
            "enable_refills": {"type": "boolean", "default": True},
            "max_refills": {"type": "integer", "default": 5},
            "controlled_substance_validation": {"type": "boolean", "default": True},
            "early_refill_window_days": {"type": "integer", "default": 2}
        },
        icon="💊",
        tags="healthcare,prescription,medication,pharmacy,refills"
    )

    print("✅ Seeded Healthcare Prescription template")


def seed_healthcare_provider_template(library: PatternLibrary):
    """Seed Healthcare Provider entity template"""

    library.add_entity_template(
        template_name="provider",
        template_namespace="healthcare",
        description="Healthcare provider with credentials, specialties, and scheduling",
        default_fields={
            # Personal Information
            "first_name": {"type": "text", "required": True},
            "last_name": {"type": "text", "required": True},
            "email": {"type": "email", "required": True, "unique": True},
            "phone": {"type": "text"},

            # Professional Information
            "license_number": {"type": "text", "required": True, "unique": True},
            "license_state": {"type": "text", "required": True},
            "license_expiration": {"type": "date", "required": True},
            "dea_number": {"type": "text"},  # For controlled substances

            # Credentials and Specialties
            "specialty": {"type": "enum", "values": ["family_medicine", "internal_medicine", "pediatrics", "cardiology", "dermatology", "psychiatry", "surgery", "other"]},
            "subspecialties": {"type": "array"},
            "board_certifications": {"type": "array"},
            "education": {"type": "array"},  # Array of education records

            # Employment
            "employment_status": {"type": "enum", "values": ["active", "inactive", "retired", "terminated"], "default": "active"},
            "hire_date": {"type": "date"},
            "termination_date": {"type": "date"},

            # Scheduling
            "working_hours": {"type": "object"},  # {monday: {start: "09:00", end: "17:00"}, ...}
            "appointment_types": {"type": "array"},  # Types of appointments they can do
            "average_visit_time": {"type": "integer", "default": 15},  # minutes

            # Performance Metrics
            "patient_count": {"type": "integer", "default": 0},
            "average_rating": {"type": "decimal", "precision": 3, "scale": 2},
            "on_time_percentage": {"type": "decimal", "precision": 5, "scale": 2},

            # Preferences
            "languages_spoken": {"type": "array", "default": ["English"]},
            "telemedicine_enabled": {"type": "boolean", "default": False}
        },
        default_patterns={
            "audit_trail": {
                "track_versions": True
            },
            "computed_fields": {
                "computed_fields": {
                    "full_name": {
                        "type": "expression",
                        "expression": "first_name + ' ' + last_name"
                    },
                    "license_expiring_soon": {
                        "type": "expression",
                        "expression": "(license_expiration - NOW()).days < 90"
                    },
                    "is_available_today": {
                        "type": "expression",
                        "expression": "check_working_hours_today(working_hours)"
                    },
                    "years_experience": {
                        "type": "expression",
                        "expression": "(NOW() - hire_date).years if hire_date else 0"
                    }
                }
            },
            "validation_chain": {
                "rules": [
                    {"field": "license_number", "rule": "not_empty", "error": "License number is required"},
                    {"field": "license_expiration", "rule": "future_date", "error": "License expiration must be in the future"},
                    {"field": "specialty", "rule": "not_empty", "error": "Specialty is required"}
                ]
            }
        },
        default_actions={
            "update_credentials": {
                "description": "Update provider credentials",
                "parameters": [
                    {"name": "credentials", "type": "object"}
                ],
                "steps": [
                    {"type": "validate", "condition": "credentials.license_expiration > NOW()", "error": "License cannot be expired"},
                    {"type": "update", "entity": "Provider", "where": "id = $id", "fields": "$credentials"},
                    {"type": "log", "message": "Provider credentials updated"}
                ]
            },
            "add_certification": {
                "description": "Add board certification",
                "parameters": [
                    {"name": "certification", "type": "text"},
                    {"name": "issue_date", "type": "date"},
                    {"name": "expiration_date", "type": "date"}
                ],
                "steps": [
                    {"type": "update", "entity": "Provider", "where": "id = $id", "fields": {"board_certifications": "board_certifications || {'certification': $certification, 'issue_date': $issue_date, 'expiration_date': $expiration_date}"}},
                    {"type": "log", "message": "Certification added: {certification}"}
                ]
            },
            "update_schedule": {
                "description": "Update provider working hours",
                "parameters": [
                    {"name": "working_hours", "type": "object"}
                ],
                "steps": [
                    {"type": "validate", "condition": "validate_working_hours($working_hours)", "error": "Invalid working hours format"},
                    {"type": "update", "entity": "Provider", "where": "id = $id", "fields": {"working_hours": "$working_hours"}},
                    {"type": "log", "message": "Working hours updated"}
                ]
            },
            "deactivate_provider": {
                "description": "Deactivate provider account",
                "parameters": [
                    {"name": "reason", "type": "text"}
                ],
                "steps": [
                    {"type": "update", "entity": "Provider", "where": "id = $id", "fields": {"employment_status": "inactive", "termination_date": "NOW()"}},
                    {"type": "log", "message": "Provider deactivated: {reason}"}
                ]
            },
            "get_availability": {
                "description": "Get provider availability for scheduling",
                "parameters": [
                    {"name": "date", "type": "date"},
                    {"name": "appointment_type", "type": "text"}
                ],
                "steps": [
                    {"type": "query", "sql": "SELECT working_hours, appointment_types FROM providers WHERE id = $id", "into": "provider_info"},
                    {"type": "query", "sql": "SELECT scheduled_date, duration_minutes FROM appointments WHERE provider_id = $id AND DATE(scheduled_date) = $date AND status IN ('scheduled', 'confirmed')", "into": "existing_appointments"},
                    {"type": "assign", "variable": "available_slots", "value": "calculate_available_slots(provider_info.working_hours, existing_appointments, $appointment_type)"},
                    {"type": "return", "value": "$available_slots"}
                ]
            }
        },
        configuration_options={
            "require_dea_number": {"type": "boolean", "default": False},
            "enable_telemedicine": {"type": "boolean", "default": True},
            "license_renewal_reminder_days": {"type": "integer", "default": 90},
            "track_performance_metrics": {"type": "boolean", "default": True}
        },
        icon="👨‍⚕️",
        tags="healthcare,provider,doctor,credentials,scheduling"
    )

    print("✅ Seeded Healthcare Provider template")


def seed_all_healthcare_templates(library: PatternLibrary):
    """Seed all Healthcare entity templates"""
    print("🌱 Seeding Healthcare entity templates...")

    seed_healthcare_patient_template(library)
    seed_healthcare_appointment_template(library)
    seed_healthcare_prescription_template(library)
    seed_healthcare_provider_template(library)

    print("✅ All Healthcare templates seeded!")


def seed_project_mgmt_project_template(library: PatternLibrary):
    """Seed Project Management Project entity template"""

    library.add_entity_template(
        template_name="project",
        template_namespace="project_management",
        description="Project with task hierarchy, milestones, and progress tracking",
        default_fields={
            # Core fields
            "name": {"type": "text", "required": True},
            "description": {"type": "text"},
            "code": {"type": "text", "unique": True},  # Project code like "PROJ-001"

            # Timeline
            "start_date": {"type": "date"},
            "end_date": {"type": "date"},
            "actual_start_date": {"type": "date"},
            "actual_end_date": {"type": "date"},

            # Status and Progress
            "status": {"type": "enum", "values": ["planning", "active", "on_hold", "completed", "cancelled"], "default": "planning"},
            "priority": {"type": "enum", "values": ["low", "medium", "high", "critical"], "default": "medium"},
            "progress_percentage": {"type": "integer", "min": 0, "max": 100, "default": 0},

            # Budget and Resources
            "budget": {"type": "decimal", "precision": 12, "scale": 2},
            "actual_cost": {"type": "decimal", "precision": 12, "scale": 2},
            "currency": {"type": "text", "default": "USD"},

            # Team
            "owner": {"type": "ref", "entity": "User", "required": True},
            "manager": {"type": "ref", "entity": "User"},
            "team_members": {"type": "array"},  # Array of user IDs

            # Classification
            "category": {"type": "text"},
            "tags": {"type": "array"},
            "department": {"type": "text"},

            # Metrics
            "total_tasks": {"type": "integer", "default": 0},
            "completed_tasks": {"type": "integer", "default": 0},
            "overdue_tasks": {"type": "integer", "default": 0}
        },
        default_patterns={
            "state_machine": {
                "states": ["planning", "active", "on_hold", "completed", "cancelled"],
                "transitions": {
                    "planning->active": {"action": "start_project"},
                    "active->on_hold": {"action": "pause_project"},
                    "on_hold->active": {"action": "resume_project"},
                    "active->completed": {"action": "complete_project"},
                    "any->cancelled": {"action": "cancel_project"}
                },
                "initial_state": "planning"
            },
            "audit_trail": {
                "track_versions": True
            },
            "computed_fields": {
                "computed_fields": {
                    "is_overdue": {
                        "type": "expression",
                        "expression": "NOW() > end_date and status in ('planning', 'active', 'on_hold')"
                    },
                    "days_remaining": {
                        "type": "expression",
                        "expression": "(end_date - NOW()).days if end_date and not is_overdue else 0"
                    },
                    "budget_variance": {
                        "type": "expression",
                        "expression": "((actual_cost - budget) / budget) * 100 if budget and budget > 0 else 0"
                    },
                    "task_completion_rate": {
                        "type": "expression",
                        "expression": "(completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0"
                    },
                    "is_on_track": {
                        "type": "expression",
                        "expression": "progress_percentage >= ((NOW() - start_date).days / (end_date - start_date).days) * 100 if start_date and end_date else True"
                    }
                }
            },
            "hierarchy_navigation": {
                "child_entity": "Task",
                "parent_field": "project_id"
            }
        },
        default_actions={
            "create_task": {
                "description": "Create a new task in this project",
                "parameters": [
                    {"name": "task_data", "type": "object"}
                ],
                "steps": [
                    {"type": "validate", "condition": "status IN ('planning', 'active')", "error": "Cannot add tasks to project with status: {status}"},
                    {"type": "create", "entity": "Task", "data": "$task_data"},
                    {"type": "update", "entity": "Project", "where": "id = $id", "fields": {"total_tasks": "total_tasks + 1"}},
                    {"type": "log", "message": "Task created in project"}
                ]
            },
            "add_milestone": {
                "description": "Add milestone to project",
                "parameters": [
                    {"name": "milestone_data", "type": "object"}
                ],
                "steps": [
                    {"type": "create", "entity": "Milestone", "data": "$milestone_data"},
                    {"type": "log", "message": "Milestone added to project"}
                ]
            },
            "update_progress": {
                "description": "Update project progress based on task completion",
                "steps": [
                    {"type": "query", "sql": "SELECT COUNT(*) as total, COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed FROM tasks WHERE project_id = $id", "into": "task_stats"},
                    {"type": "assign", "variable": "progress", "value": "(task_stats.completed / task_stats.total) * 100 if task_stats.total > 0 else 0"},
                    {"type": "update", "entity": "Project", "where": "id = $id", "fields": {"progress_percentage": "$progress", "total_tasks": "task_stats.total", "completed_tasks": "task_stats.completed"}},
                    {"type": "log", "message": "Project progress updated to {progress}%"}
                ]
            },
            "add_team_member": {
                "description": "Add team member to project",
                "parameters": [
                    {"name": "user_id", "type": "uuid"},
                    {"name": "role", "type": "text"}
                ],
                "steps": [
                    {"type": "validate", "condition": "user_id NOT IN team_members", "error": "User is already a team member"},
                    {"type": "update", "entity": "Project", "where": "id = $id", "fields": {"team_members": "team_members || {'user_id': $user_id, 'role': $role, 'added_date': NOW()}"}},
                    {"type": "log", "message": "Team member added: {user_id} as {role}"}
                ]
            }
        },
        configuration_options={
            "enable_budget_tracking": {"type": "boolean", "default": True},
            "auto_calculate_progress": {"type": "boolean", "default": True},
            "require_milestones": {"type": "boolean", "default": False},
            "max_team_size": {"type": "integer", "default": 20}
        },
        icon="📋",
        tags="project,management,tasks,milestones,team"
    )

    print("✅ Seeded Project Management Project template")


def seed_project_mgmt_task_template(library: PatternLibrary):
    """Seed Project Management Task entity template"""

    library.add_entity_template(
        template_name="task",
        template_namespace="project_management",
        description="Task with dependencies, time tracking, and assignment",
        default_fields={
            # Core fields
            "title": {"type": "text", "required": True},
            "description": {"type": "text"},
            "project": {"type": "ref", "entity": "Project", "required": True},

            # Assignment
            "assignee": {"type": "ref", "entity": "User"},
            "reporter": {"type": "ref", "entity": "User"},
            "reviewer": {"type": "ref", "entity": "User"},

            # Status and Priority
            "status": {"type": "enum", "values": ["todo", "in_progress", "in_review", "completed", "cancelled"], "default": "todo"},
            "priority": {"type": "enum", "values": ["low", "medium", "high", "critical"], "default": "medium"},

            # Timeline
            "due_date": {"type": "date"},
            "estimated_hours": {"type": "decimal", "precision": 6, "scale": 2},
            "actual_hours": {"type": "decimal", "precision": 6, "scale": 2},
            "start_date": {"type": "timestamp"},
            "completed_date": {"type": "timestamp"},

            # Dependencies
            "depends_on": {"type": "array"},  # Array of task IDs
            "blocks": {"type": "array"},      # Array of task IDs this blocks

            # Progress
            "progress_percentage": {"type": "integer", "min": 0, "max": 100, "default": 0},
            "subtasks": {"type": "array"},    # Array of subtask objects

            # Classification
            "labels": {"type": "array"},
            "story_points": {"type": "integer"},

            # Comments and attachments
            "comments": {"type": "array"},
            "attachments": {"type": "array"}
        },
        default_patterns={
            "state_machine": {
                "states": ["todo", "in_progress", "in_review", "completed", "cancelled"],
                "transitions": {
                    "todo->in_progress": {"action": "start_task"},
                    "in_progress->in_review": {"action": "submit_for_review"},
                    "in_review->completed": {"action": "complete_task"},
                    "in_review->in_progress": {"action": "request_changes"},
                    "any->cancelled": {"action": "cancel_task"}
                },
                "initial_state": "todo"
            },
            "audit_trail": {
                "track_versions": True
            },
            "computed_fields": {
                "computed_fields": {
                    "is_overdue": {
                        "type": "expression",
                        "expression": "NOW() > due_date and status != 'completed'"
                    },
                    "is_blocked": {
                        "type": "expression",
                        "expression": "len([dep for dep in depends_on if get_task_status(dep) != 'completed']) > 0"
                    },
                    "can_start": {
                        "type": "expression",
                        "expression": "not is_blocked and status == 'todo'"
                    },
                    "time_variance": {
                        "type": "expression",
                        "expression": "((actual_hours - estimated_hours) / estimated_hours) * 100 if estimated_hours and estimated_hours > 0 else 0"
                    },
                    "days_overdue": {
                        "type": "expression",
                        "expression": "(NOW() - due_date).days if is_overdue else 0"
                    }
                }
            },
            "commenting": {
                "enable_comments": True,
                "allow_attachments": True
            }
        },
        default_actions={
            "assign_task": {
                "description": "Assign task to user",
                "parameters": [
                    {"name": "user_id", "type": "uuid"}
                ],
                "steps": [
                    {"type": "validate", "condition": "status != 'completed'", "error": "Cannot assign completed task"},
                    {"type": "update", "entity": "Task", "where": "id = $id", "fields": {"assignee": "$user_id"}},
                    {"type": "log", "message": "Task assigned to user {user_id}"}
                ]
            },
            "add_dependency": {
                "description": "Add task dependency",
                "parameters": [
                    {"name": "depends_on_task_id", "type": "uuid"}
                ],
                "steps": [
                    {"type": "validate", "condition": "depends_on_task_id != $id", "error": "Task cannot depend on itself"},
                    {"type": "validate", "condition": "depends_on_task_id NOT IN depends_on", "error": "Dependency already exists"},
                    {"type": "query", "sql": "SELECT project_id FROM tasks WHERE id = $depends_on_task_id", "into": "dep_project"},
                    {"type": "validate", "condition": "dep_project.project_id == project", "error": "Dependency must be in same project"},
                    {"type": "update", "entity": "Task", "where": "id = $id", "fields": {"depends_on": "depends_on || $depends_on_task_id"}},
                    {"type": "update", "entity": "Task", "where": "id = $depends_on_task_id", "fields": {"blocks": "blocks || $id"}},
                    {"type": "log", "message": "Task dependency added"}
                ]
            },
            "log_time": {
                "description": "Log time spent on task",
                "parameters": [
                    {"name": "hours", "type": "decimal"},
                    {"name": "description", "type": "text"}
                ],
                "steps": [
                    {"type": "validate", "condition": "hours > 0", "error": "Hours must be positive"},
                    {"type": "update", "entity": "Task", "where": "id = $id", "fields": {"actual_hours": "actual_hours + $hours"}},
                    {"type": "create", "entity": "TimeEntry", "data": {
                        "task_id": "$id",
                        "user_id": "$current_user_id",
                        "hours": "$hours",
                        "description": "$description",
                        "date": "NOW()"
                    }},
                    {"type": "log", "message": "Time logged: {hours} hours - {description}"}
                ]
            },
            "add_subtask": {
                "description": "Add subtask to this task",
                "parameters": [
                    {"name": "subtask_data", "type": "object"}
                ],
                "steps": [
                    {"type": "update", "entity": "Task", "where": "id = $id", "fields": {"subtasks": "subtasks || $subtask_data"}},
                    {"type": "log", "message": "Subtask added"}
                ]
            },
            "add_comment": {
                "description": "Add comment to task",
                "parameters": [
                    {"name": "comment", "type": "text"}
                ],
                "steps": [
                    {"type": "update", "entity": "Task", "where": "id = $id", "fields": {"comments": "comments || {'text': $comment, 'user_id': $current_user_id, 'timestamp': NOW()}"}},
                    {"type": "log", "message": "Comment added to task"}
                ]
            }
        },
        configuration_options={
            "enable_time_tracking": {"type": "boolean", "default": True},
            "enable_dependencies": {"type": "boolean", "default": True},
            "enable_subtasks": {"type": "boolean", "default": True},
            "require_due_dates": {"type": "boolean", "default": False}
        },
        icon="✅",
        tags="task,project,assignment,dependencies,time_tracking"
    )

    print("✅ Seeded Project Management Task template")


def seed_project_mgmt_milestone_template(library: PatternLibrary):
    """Seed Project Management Milestone entity template"""

    library.add_entity_template(
        template_name="milestone",
        template_namespace="project_management",
        description="Project milestone with deliverables and completion criteria",
        default_fields={
            # Core fields
            "name": {"type": "text", "required": True},
            "description": {"type": "text"},
            "project": {"type": "ref", "entity": "Project", "required": True},

            # Timeline
            "target_date": {"type": "date", "required": True},
            "actual_date": {"type": "date"},
            "reminder_date": {"type": "date"},

            # Status and Progress
            "status": {"type": "enum", "values": ["planned", "in_progress", "completed", "missed"], "default": "planned"},
            "progress_percentage": {"type": "integer", "min": 0, "max": 100, "default": 0},

            # Deliverables
            "deliverables": {"type": "array"},  # Array of deliverable descriptions
            "completion_criteria": {"type": "array"},  # What needs to be done

            # Assignment
            "owner": {"type": "ref", "entity": "User"},
            "reviewer": {"type": "ref", "entity": "User"},

            # Dependencies
            "depends_on_milestones": {"type": "array"},  # Other milestone IDs
            "required_tasks": {"type": "array"},         # Task IDs that must be completed

            # Budget
            "budget_allocated": {"type": "decimal", "precision": 10, "scale": 2},
            "actual_cost": {"type": "decimal", "precision": 10, "scale": 2},

            # Metadata
            "priority": {"type": "enum", "values": ["low", "medium", "high", "critical"], "default": "medium"},
            "tags": {"type": "array"}
        },
        default_patterns={
            "state_machine": {
                "states": ["planned", "in_progress", "completed", "missed"],
                "transitions": {
                    "planned->in_progress": {"action": "start_milestone"},
                    "in_progress->completed": {"action": "complete_milestone"},
                    "planned->missed": {"action": "miss_milestone"},
                    "in_progress->missed": {"action": "miss_milestone"}
                },
                "initial_state": "planned"
            },
            "audit_trail": {
                "track_versions": True
            },
            "computed_fields": {
                "computed_fields": {
                    "is_overdue": {
                        "type": "expression",
                        "expression": "NOW() > target_date and status in ('planned', 'in_progress')"
                    },
                    "days_overdue": {
                        "type": "expression",
                        "expression": "(NOW() - target_date).days if is_overdue else 0"
                    },
                    "is_on_track": {
                        "type": "expression",
                        "expression": "progress_percentage >= ((NOW() - project.start_date).days / (target_date - project.start_date).days) * 100 if project.start_date else True"
                    },
                    "all_tasks_completed": {
                        "type": "expression",
                        "expression": "all(get_task_status(task_id) == 'completed' for task_id in required_tasks)"
                    },
                    "budget_variance": {
                        "type": "expression",
                        "expression": "((actual_cost - budget_allocated) / budget_allocated) * 100 if budget_allocated and budget_allocated > 0 else 0"
                    }
                }
            },
            "notification": {
                "events": ["overdue", "completed", "missed"],
                "channels": ["email", "app"]
            }
        },
        default_actions={
            "mark_completed": {
                "description": "Mark milestone as completed",
                "steps": [
                    {"type": "validate", "condition": "all_tasks_completed", "error": "Required tasks must be completed first"},
                    {"type": "validate", "condition": "len([d for d in deliverables if not d.get('completed', False)]) == 0", "error": "All deliverables must be completed"},
                    {"type": "call", "function": "transition_to", "args": {"target_state": "completed"}},
                    {"type": "update", "entity": "Milestone", "where": "id = $id", "fields": {"actual_date": "NOW()", "progress_percentage": 100}},
                    {"type": "log", "message": "Milestone completed"}
                ]
            },
            "add_deliverable": {
                "description": "Add deliverable to milestone",
                "parameters": [
                    {"name": "deliverable", "type": "text"}
                ],
                "steps": [
                    {"type": "update", "entity": "Milestone", "where": "id = $id", "fields": {"deliverables": "deliverables || {'description': $deliverable, 'completed': False}"}},
                    {"type": "log", "message": "Deliverable added: {deliverable}"}
                ]
            },
            "complete_deliverable": {
                "description": "Mark deliverable as completed",
                "parameters": [
                    {"name": "deliverable_index", "type": "integer"}
                ],
                "steps": [
                    {"type": "update", "entity": "Milestone", "where": "id = $id", "fields": {"deliverables": "update_deliverable_status(deliverables, $deliverable_index, True)"}},
                    {"type": "call", "function": "update_progress"},
                    {"type": "log", "message": "Deliverable completed"}
                ]
            },
            "update_progress": {
                "description": "Update milestone progress based on deliverables",
                "steps": [
                    {"type": "assign", "variable": "total_deliverables", "value": "len(deliverables)"},
                    {"type": "assign", "variable": "completed_deliverables", "value": "len([d for d in deliverables if d.get('completed', False)])"},
                    {"type": "assign", "variable": "progress", "value": "(completed_deliverables / total_deliverables) * 100 if total_deliverables > 0 else 0"},
                    {"type": "update", "entity": "Milestone", "where": "id = $id", "fields": {"progress_percentage": "$progress"}},
                    {"type": "log", "message": "Milestone progress updated to {progress}%"}
                ]
            },
            "add_required_task": {
                "description": "Add required task for milestone completion",
                "parameters": [
                    {"name": "task_id", "type": "uuid"}
                ],
                "steps": [
                    {"type": "query", "sql": "SELECT project_id FROM tasks WHERE id = $task_id", "into": "task_project"},
                    {"type": "validate", "condition": "task_project.project_id == project", "error": "Task must belong to same project"},
                    {"type": "update", "entity": "Milestone", "where": "id = $id", "fields": {"required_tasks": "required_tasks || $task_id"}},
                    {"type": "log", "message": "Required task added to milestone"}
                ]
            }
        },
        configuration_options={
            "require_deliverables": {"type": "boolean", "default": True},
            "auto_calculate_progress": {"type": "boolean", "default": True},
            "enable_budget_tracking": {"type": "boolean", "default": False},
            "reminder_days_before": {"type": "integer", "default": 7}
        },
        icon="🏁",
        tags="milestone,project,deliverables,deadline,progress"
    )

    print("✅ Seeded Project Management Milestone template")


def seed_all_project_mgmt_templates(library: PatternLibrary):
    """Seed all Project Management entity templates"""
    print("🌱 Seeding Project Management entity templates...")

    seed_project_mgmt_project_template(library)
    seed_project_mgmt_task_template(library)
    seed_project_mgmt_milestone_template(library)

    print("✅ All Project Management templates seeded!")


def seed_hr_employee_template(library: PatternLibrary):
    """Seed HR Employee entity template"""

    library.add_entity_template(
        template_name="employee",
        template_namespace="hr",
        description="Employee with personal info, employment details, and performance tracking",
        default_fields={
            # Personal Information
            "first_name": {"type": "text", "required": True},
            "last_name": {"type": "text", "required": True},
            "email": {"type": "email", "required": True, "unique": True},
            "phone": {"type": "text"},
            "date_of_birth": {"type": "date"},
            "ssn": {"type": "text", "encrypted": True},  # PII

            # Employment Details
            "employee_id": {"type": "text", "required": True, "unique": True},
            "position": {"type": "ref", "entity": "Position", "required": True},
            "department": {"type": "ref", "entity": "Department", "required": True},
            "manager": {"type": "ref", "entity": "Employee"},

            # Employment Dates
            "hire_date": {"type": "date", "required": True},
            "termination_date": {"type": "date"},
            "probation_end_date": {"type": "date"},

            # Compensation
            "salary": {"type": "decimal", "precision": 10, "scale": 2},
            "hourly_rate": {"type": "decimal", "precision": 6, "scale": 2},
            "currency": {"type": "text", "default": "USD"},
            "pay_frequency": {"type": "enum", "values": ["weekly", "biweekly", "monthly"], "default": "biweekly"},

            # Status and Type
            "employment_status": {"type": "enum", "values": ["active", "inactive", "terminated", "on_leave"], "default": "active"},
            "employment_type": {"type": "enum", "values": ["full_time", "part_time", "contract", "intern"], "default": "full_time"},

            # Address
            "address": {"type": "object"},

            # Emergency Contact
            "emergency_contact": {"type": "object"},

            # Performance and Development
            "performance_rating": {"type": "decimal", "precision": 3, "scale": 2, "min": 1, "max": 5},
            "last_review_date": {"type": "date"},
            "next_review_date": {"type": "date"},

            # Benefits and Policies
            "benefits_eligible": {"type": "boolean", "default": True},
            "vacation_days": {"type": "integer", "default": 10},
            "sick_days": {"type": "integer", "default": 5},
            "used_vacation_days": {"type": "integer", "default": 0},
            "used_sick_days": {"type": "integer", "default": 0}
        },
        default_patterns={
            "audit_trail": {
                "track_versions": True
            },
            "computed_fields": {
                "computed_fields": {
                    "full_name": {
                        "type": "expression",
                        "expression": "first_name + ' ' + last_name"
                    },
                    "age": {
                        "type": "expression",
                        "expression": "(NOW() - date_of_birth).years if date_of_birth else None"
                    },
                    "tenure_years": {
                        "type": "expression",
                        "expression": "(NOW() - hire_date).years if hire_date else 0"
                    },
                    "is_probationary": {
                        "type": "expression",
                        "expression": "NOW() <= probation_end_date if probation_end_date else False"
                    },
                    "remaining_vacation_days": {
                        "type": "expression",
                        "expression": "vacation_days - used_vacation_days"
                    },
                    "remaining_sick_days": {
                        "type": "expression",
                        "expression": "sick_days - used_sick_days"
                    },
                    "annual_salary": {
                        "type": "expression",
                        "expression": "salary * 12 if pay_frequency == 'monthly' else salary * 26 if pay_frequency == 'biweekly' else salary * 52"
                    }
                }
            },
            "hierarchy_navigation": {
                "parent_field": "manager",
                "max_depth": 5
            }
        },
        default_actions={
            "update_performance_rating": {
                "description": "Update employee performance rating",
                "parameters": [
                    {"name": "rating", "type": "decimal"},
                    {"name": "review_date", "type": "date"}
                ],
                "steps": [
                    {"type": "validate", "condition": "rating >= 1 AND rating <= 5", "error": "Rating must be between 1 and 5"},
                    {"type": "update", "entity": "Employee", "where": "id = $id", "fields": {"performance_rating": "$rating", "last_review_date": "$review_date"}},
                    {"type": "assign", "variable": "next_review", "value": "$review_date + INTERVAL '1 year'"},
                    {"type": "update", "entity": "Employee", "where": "id = $id", "fields": {"next_review_date": "$next_review"}},
                    {"type": "log", "message": "Performance rating updated to {rating}"}
                ]
            },
            "change_position": {
                "description": "Change employee position",
                "parameters": [
                    {"name": "new_position_id", "type": "uuid"},
                    {"name": "effective_date", "type": "date"}
                ],
                "steps": [
                    {"type": "query", "sql": "SELECT department_id FROM positions WHERE id = $new_position_id", "into": "position_info"},
                    {"type": "update", "entity": "Employee", "where": "id = $id", "fields": {"position": "$new_position_id", "department": "position_info.department_id"}},
                    {"type": "create", "entity": "PositionHistory", "data": {
                        "employee_id": "$id",
                        "old_position": "position",
                        "new_position": "$new_position_id",
                        "effective_date": "$effective_date"
                    }},
                    {"type": "log", "message": "Position changed to {new_position_id}"}
                ]
            },
            "record_time_off": {
                "description": "Record employee time off",
                "parameters": [
                    {"name": "time_off_type", "type": "enum", "values": ["vacation", "sick", "personal"]},
                    {"name": "days", "type": "integer"},
                    {"name": "start_date", "type": "date"}
                ],
                "steps": [
                    {"type": "validate", "condition": "days > 0", "error": "Days must be positive"},
                    {"type": "if", "condition": "time_off_type == 'vacation'", "then": [
                        {"type": "validate", "condition": "remaining_vacation_days >= days", "error": "Insufficient vacation days"},
                        {"type": "update", "entity": "Employee", "where": "id = $id", "fields": {"used_vacation_days": "used_vacation_days + days"}}
                    ]},
                    {"type": "if", "condition": "time_off_type == 'sick'", "then": [
                        {"type": "validate", "condition": "remaining_sick_days >= days", "error": "Insufficient sick days"},
                        {"type": "update", "entity": "Employee", "where": "id = $id", "fields": {"used_sick_days": "used_sick_days + days"}}
                    ]},
                    {"type": "create", "entity": "TimeOff", "data": {
                        "employee_id": "$id",
                        "type": "$time_off_type",
                        "days": "$days",
                        "start_date": "$start_date",
                        "status": "approved"
                    }},
                    {"type": "log", "message": "Time off recorded: {days} days {time_off_type}"}
                ]
            },
            "terminate_employment": {
                "description": "Terminate employee employment",
                "parameters": [
                    {"name": "termination_date", "type": "date"},
                    {"name": "reason", "type": "text"}
                ],
                "steps": [
                    {"type": "update", "entity": "Employee", "where": "id = $id", "fields": {"employment_status": "terminated", "termination_date": "$termination_date"}},
                    {"type": "log", "message": "Employment terminated: {reason}"}
                ]
            }
        },
        configuration_options={
            "enable_performance_reviews": {"type": "boolean", "default": True},
            "track_time_off": {"type": "boolean", "default": True},
            "require_probation_period": {"type": "boolean", "default": True},
            "encrypt_pii": {"type": "boolean", "default": True}
        },
        icon="👤",
        tags="hr,employee,personnel,performance,compensation"
    )

    print("✅ Seeded HR Employee template")


def seed_hr_position_template(library: PatternLibrary):
    """Seed HR Position entity template"""

    library.add_entity_template(
        template_name="position",
        template_namespace="hr",
        description="Job position with requirements, compensation, and organizational structure",
        default_fields={
            # Position Details
            "title": {"type": "text", "required": True},
            "code": {"type": "text", "unique": True},
            "description": {"type": "text"},
            "department": {"type": "ref", "entity": "Department", "required": True},

            # Classification
            "job_family": {"type": "text"},
            "job_level": {"type": "enum", "values": ["entry", "junior", "senior", "lead", "manager", "director", "executive"]},
            "employment_type": {"type": "enum", "values": ["full_time", "part_time", "contract", "temporary"], "default": "full_time"},

            # Compensation
            "min_salary": {"type": "decimal", "precision": 10, "scale": 2},
            "max_salary": {"type": "decimal", "precision": 10, "scale": 2},
            "target_salary": {"type": "decimal", "precision": 10, "scale": 2},
            "currency": {"type": "text", "default": "USD"},

            # Requirements
            "required_skills": {"type": "array"},
            "preferred_skills": {"type": "array"},
            "education_requirements": {"type": "array"},
            "experience_years": {"type": "integer"},
            "certifications": {"type": "array"},

            # Reporting Structure
            "reports_to": {"type": "ref", "entity": "Position"},
            "direct_reports": {"type": "integer", "default": 0},

            # Status
            "status": {"type": "enum", "values": ["open", "filled", "frozen", "eliminated"], "default": "open"},
            "is_managerial": {"type": "boolean", "default": False},

            # Metadata
            "created_date": {"type": "timestamp", "default": "NOW()"},
            "last_updated": {"type": "timestamp", "default": "NOW()"}
        },
        default_patterns={
            "audit_trail": {
                "track_versions": True
            },
            "computed_fields": {
                "computed_fields": {
                    "salary_range": {
                        "type": "expression",
                        "expression": "format('${:,} - ${:,}', min_salary, max_salary)"
                    },
                    "is_filled": {
                        "type": "expression",
                        "expression": "status == 'filled'"
                    },
                    "has_openings": {
                        "type": "expression",
                        "expression": "status == 'open'"
                    },
                    "salary_midpoint": {
                        "type": "expression",
                        "expression": "(min_salary + max_salary) / 2 if min_salary and max_salary else target_salary"
                    }
                }
            },
            "hierarchy_navigation": {
                "parent_field": "reports_to",
                "max_depth": 10
            }
        },
        default_actions={
            "create_job_requisition": {
                "description": "Create job requisition for this position",
                "parameters": [
                    {"name": "hiring_manager", "type": "uuid"},
                    {"name": "target_hire_date", "type": "date"}
                ],
                "steps": [
                    {"type": "validate", "condition": "status == 'open'", "error": "Position is not open"},
                    {"type": "create", "entity": "JobRequisition", "data": {
                        "position_id": "$id",
                        "hiring_manager": "$hiring_manager",
                        "target_hire_date": "$target_hire_date",
                        "status": "open"
                    }},
                    {"type": "log", "message": "Job requisition created for position"}
                ]
            },
            "update_compensation": {
                "description": "Update position compensation range",
                "parameters": [
                    {"name": "min_salary", "type": "decimal"},
                    {"name": "max_salary", "type": "decimal"},
                    {"name": "target_salary", "type": "decimal"}
                ],
                "steps": [
                    {"type": "validate", "condition": "min_salary <= target_salary <= max_salary", "error": "Target salary must be within range"},
                    {"type": "update", "entity": "Position", "where": "id = $id", "fields": {"min_salary": "$min_salary", "max_salary": "$max_salary", "target_salary": "$target_salary", "last_updated": "NOW()"}},
                    {"type": "log", "message": "Position compensation updated"}
                ]
            },
            "add_requirement": {
                "description": "Add requirement to position",
                "parameters": [
                    {"name": "requirement_type", "type": "enum", "values": ["skill", "education", "experience", "certification"]},
                    {"name": "requirement", "type": "text"}
                ],
                "steps": [
                    {"type": "if", "condition": "requirement_type == 'skill'", "then": [
                        {"type": "update", "entity": "Position", "where": "id = $id", "fields": {"required_skills": "required_skills || $requirement"}}
                    ]},
                    {"type": "if", "condition": "requirement_type == 'education'", "then": [
                        {"type": "update", "entity": "Position", "where": "id = $id", "fields": {"education_requirements": "education_requirements || $requirement"}}
                    ]},
                    {"type": "if", "condition": "requirement_type == 'certification'", "then": [
                        {"type": "update", "entity": "Position", "where": "id = $id", "fields": {"certifications": "certifications || $requirement"}}
                    ]},
                    {"type": "update", "entity": "Position", "where": "id = $id", "fields": {"last_updated": "NOW()"}},
                    {"type": "log", "message": "Requirement added: {requirement}"}
                ]
            },
            "close_position": {
                "description": "Close position (no longer hiring)",
                "steps": [
                    {"type": "update", "entity": "Position", "where": "id = $id", "fields": {"status": "frozen"}},
                    {"type": "log", "message": "Position closed"}
                ]
            }
        },
        configuration_options={
            "enable_job_requisitions": {"type": "boolean", "default": True},
            "require_compensation_approval": {"type": "boolean", "default": True},
            "track_position_history": {"type": "boolean", "default": True}
        },
        icon="💼",
        tags="hr,position,job,requisition,compensation"
    )

    print("✅ Seeded HR Position template")


def seed_hr_department_template(library: PatternLibrary):
    """Seed HR Department entity template"""

    library.add_entity_template(
        template_name="department",
        template_namespace="hr",
        description="Department with hierarchy, budget, and headcount management",
        default_fields={
            # Department Details
            "name": {"type": "text", "required": True},
            "code": {"type": "text", "required": True, "unique": True},
            "description": {"type": "text"},
            "parent_department": {"type": "ref", "entity": "Department"},

            # Leadership
            "head": {"type": "ref", "entity": "Employee"},
            "assistant_head": {"type": "ref", "entity": "Employee"},

            # Budget and Resources
            "annual_budget": {"type": "decimal", "precision": 12, "scale": 2},
            "budget_currency": {"type": "text", "default": "USD"},
            "allocated_budget": {"type": "decimal", "precision": 12, "scale": 2, "default": 0},

            # Headcount
            "target_headcount": {"type": "integer"},
            "current_headcount": {"type": "integer", "default": 0},
            "open_positions": {"type": "integer", "default": 0},

            # Location
            "location": {"type": "text"},
            "floor": {"type": "text"},
            "office_number": {"type": "text"},

            # Status
            "status": {"type": "enum", "values": ["active", "inactive", "dissolved"], "default": "active"},
            "established_date": {"type": "date"},

            # Performance
            "department_rating": {"type": "decimal", "precision": 3, "scale": 2, "min": 1, "max": 5}
        },
        default_patterns={
            "audit_trail": {
                "track_versions": True
            },
            "computed_fields": {
                "computed_fields": {
                    "budget_utilization": {
                        "type": "expression",
                        "expression": "(allocated_budget / annual_budget) * 100 if annual_budget > 0 else 0"
                    },
                    "headcount_variance": {
                        "type": "expression",
                        "expression": "current_headcount - target_headcount if target_headcount else 0"
                    },
                    "has_open_positions": {
                        "type": "expression",
                        "expression": "open_positions > 0"
                    },
                    "budget_remaining": {
                        "type": "expression",
                        "expression": "annual_budget - allocated_budget if annual_budget else 0"
                    }
                }
            },
            "hierarchy_navigation": {
                "parent_field": "parent_department",
                "max_depth": 5
            }
        },
        default_actions={
            "allocate_budget": {
                "description": "Allocate budget to department",
                "parameters": [
                    {"name": "amount", "type": "decimal"},
                    {"name": "purpose", "type": "text"}
                ],
                "steps": [
                    {"type": "validate", "condition": "amount > 0", "error": "Amount must be positive"},
                    {"type": "validate", "condition": "budget_remaining >= amount", "error": "Insufficient remaining budget"},
                    {"type": "update", "entity": "Department", "where": "id = $id", "fields": {"allocated_budget": "allocated_budget + amount"}},
                    {"type": "create", "entity": "BudgetAllocation", "data": {
                        "department_id": "$id",
                        "amount": "$amount",
                        "purpose": "$purpose",
                        "allocated_by": "$current_user_id",
                        "allocation_date": "NOW()"
                    }},
                    {"type": "log", "message": "Budget allocated: ${amount} for {purpose}"}
                ]
            },
            "update_headcount": {
                "description": "Update department headcount",
                "steps": [
                    {"type": "query", "sql": "SELECT COUNT(*) as employee_count FROM employees WHERE department_id = $id AND employment_status = 'active'", "into": "headcount"},
                    {"type": "query", "sql": "SELECT COUNT(*) as open_count FROM positions WHERE department_id = $id AND status = 'open'", "into": "open_pos"},
                    {"type": "update", "entity": "Department", "where": "id = $id", "fields": {"current_headcount": "headcount.employee_count", "open_positions": "open_pos.open_count"}},
                    {"type": "log", "message": "Headcount updated: {headcount.employee_count} current, {open_pos.open_count} open"}
                ]
            },
            "set_department_head": {
                "description": "Set department head",
                "parameters": [
                    {"name": "employee_id", "type": "uuid"}
                ],
                "steps": [
                    {"type": "query", "sql": "SELECT department_id FROM employees WHERE id = $employee_id", "into": "emp_dept"},
                    {"type": "validate", "condition": "emp_dept.department_id == $id", "error": "Employee must be in this department"},
                    {"type": "update", "entity": "Department", "where": "id = $id", "fields": {"head": "$employee_id"}},
                    {"type": "log", "message": "Department head set to employee {employee_id}"}
                ]
            },
            "create_subdepartment": {
                "description": "Create subdepartment under this department",
                "parameters": [
                    {"name": "name", "type": "text"},
                    {"name": "code", "type": "text"}
                ],
                "steps": [
                    {"type": "create", "entity": "Department", "data": {
                        "name": "$name",
                        "code": "$code",
                        "parent_department": "$id",
                        "status": "active",
                        "established_date": "NOW()"
                    }},
                    {"type": "log", "message": "Subdepartment created: {name}"}
                ]
            }
        },
        configuration_options={
            "enable_budget_tracking": {"type": "boolean", "default": True},
            "auto_update_headcount": {"type": "boolean", "default": True},
            "require_department_approval": {"type": "boolean", "default": True}
        },
        icon="🏢",
        tags="hr,department,organization,budget,headcount"
    )

    print("✅ Seeded HR Department template")


def seed_hr_timesheet_template(library: PatternLibrary):
    """Seed HR Timesheet entity template"""

    library.add_entity_template(
        template_name="timesheet",
        template_namespace="hr",
        description="Employee timesheet with time tracking, approval workflow, and payroll integration",
        default_fields={
            # Timesheet Details
            "employee": {"type": "ref", "entity": "Employee", "required": True},
            "period_start": {"type": "date", "required": True},
            "period_end": {"type": "date", "required": True},
            "week_number": {"type": "integer"},

            # Time Entries
            "time_entries": {"type": "array"},  # Array of time entry objects

            # Summary
            "total_hours": {"type": "decimal", "precision": 6, "scale": 2, "default": 0},
            "regular_hours": {"type": "decimal", "precision": 6, "scale": 2, "default": 0},
            "overtime_hours": {"type": "decimal", "precision": 6, "scale": 2, "default": 0},
            "vacation_hours": {"type": "decimal", "precision": 6, "scale": 2, "default": 0},
            "sick_hours": {"type": "decimal", "precision": 6, "scale": 2, "default": 0},

            # Status and Approval
            "status": {"type": "enum", "values": ["draft", "submitted", "approved", "rejected"], "default": "draft"},
            "submitted_date": {"type": "timestamp"},
            "approved_date": {"type": "timestamp"},
            "approved_by": {"type": "ref", "entity": "Employee"},
            "rejection_reason": {"type": "text"},

            # Payroll
            "processed_for_payroll": {"type": "boolean", "default": False},
            "payroll_period": {"type": "text"}
        },
        default_patterns={
            "state_machine": {
                "states": ["draft", "submitted", "approved", "rejected"],
                "transitions": {
                    "draft->submitted": {"action": "submit_timesheet"},
                    "submitted->approved": {"action": "approve_timesheet"},
                    "submitted->rejected": {"action": "reject_timesheet"},
                    "approved->draft": {"action": "unapprove_timesheet"}
                },
                "initial_state": "draft"
            },
            "audit_trail": {
                "track_versions": True
            },
            "computed_fields": {
                "computed_fields": {
                    "is_complete": {
                        "type": "expression",
                        "expression": "total_hours >= 40"  # Assuming 40-hour workweek
                    },
                    "overtime_eligible": {
                        "type": "expression",
                        "expression": "regular_hours > 40"
                    },
                    "billable_hours": {
                        "type": "expression",
                        "expression": "sum(entry.hours for entry in time_entries if entry.get('billable', False))"
                    },
                    "is_overdue": {
                        "type": "expression",
                        "expression": "NOW() > period_end + INTERVAL '1 day' and status == 'draft'"
                    }
                }
            },
            "approval_workflow": {
                "stages": [
                    {"name": "manager_approval", "approvers": ["manager"], "auto_approve_threshold": 45}
                ]
            }
        },
        default_actions={
            "add_time_entry": {
                "description": "Add time entry to timesheet",
                "parameters": [
                    {"name": "date", "type": "date"},
                    {"name": "hours", "type": "decimal"},
                    {"name": "project", "type": "text"},
                    {"name": "description", "type": "text"},
                    {"name": "billable", "type": "boolean", "default": True}
                ],
                "steps": [
                    {"type": "validate", "condition": "date >= period_start AND date <= period_end", "error": "Date must be within timesheet period"},
                    {"type": "validate", "condition": "hours > 0 AND hours <= 24", "error": "Hours must be between 0 and 24"},
                    {"type": "validate", "condition": "status == 'draft'", "error": "Cannot modify submitted timesheet"},
                    {"type": "update", "entity": "Timesheet", "where": "id = $id", "fields": {"time_entries": "time_entries || {'date': $date, 'hours': $hours, 'project': $project, 'description': $description, 'billable': $billable}"}},
                    {"type": "call", "function": "recalculate_totals"},
                    {"type": "log", "message": "Time entry added: {hours} hours on {date}"}
                ]
            },
            "recalculate_totals": {
                "description": "Recalculate timesheet totals",
                "steps": [
                    {"type": "assign", "variable": "total", "value": "sum(entry.hours for entry in time_entries)"},
                    {"type": "assign", "variable": "regular", "value": "min(total, 40)"},
                    {"type": "assign", "variable": "overtime", "value": "max(total - 40, 0)"},
                    {"type": "assign", "variable": "vacation", "value": "sum(entry.hours for entry in time_entries if entry.get('type') == 'vacation')"},
                    {"type": "assign", "variable": "sick", "value": "sum(entry.hours for entry in time_entries if entry.get('type') == 'sick')"},
                    {"type": "update", "entity": "Timesheet", "where": "id = $id", "fields": {"total_hours": "$total", "regular_hours": "$regular", "overtime_hours": "$overtime", "vacation_hours": "$vacation", "sick_hours": "$sick"}}
                ]
            },
            "submit_for_approval": {
                "description": "Submit timesheet for approval",
                "steps": [
                    {"type": "validate", "condition": "status == 'draft'", "error": "Timesheet already submitted"},
                    {"type": "validate", "condition": "total_hours > 0", "error": "Cannot submit empty timesheet"},
                    {"type": "call", "function": "transition_to", "args": {"target_state": "submitted"}},
                    {"type": "update", "entity": "Timesheet", "where": "id = $id", "fields": {"submitted_date": "NOW()"}},
                    {"type": "log", "message": "Timesheet submitted for approval"}
                ]
            },
            "approve_timesheet": {
                "description": "Approve timesheet",
                "steps": [
                    {"type": "validate", "condition": "status == 'submitted'", "error": "Timesheet not submitted"},
                    {"type": "call", "function": "transition_to", "args": {"target_state": "approved"}},
                    {"type": "update", "entity": "Timesheet", "where": "id = $id", "fields": {"approved_date": "NOW()", "approved_by": "$current_user_id"}},
                    {"type": "log", "message": "Timesheet approved"}
                ]
            },
            "reject_timesheet": {
                "description": "Reject timesheet",
                "parameters": [
                    {"name": "reason", "type": "text"}
                ],
                "steps": [
                    {"type": "validate", "condition": "status == 'submitted'", "error": "Timesheet not submitted"},
                    {"type": "call", "function": "transition_to", "args": {"target_state": "rejected"}},
                    {"type": "update", "entity": "Timesheet", "where": "id = $id", "fields": {"rejection_reason": "$reason"}},
                    {"type": "log", "message": "Timesheet rejected: {reason}"}
                ]
            }
        },
        configuration_options={
            "auto_submit_on_complete": {"type": "boolean", "default": False},
            "require_approval": {"type": "boolean", "default": True},
            "track_billable_hours": {"type": "boolean", "default": True},
            "standard_workweek_hours": {"type": "integer", "default": 40}
        },
        icon="⏰",
        tags="hr,timesheet,time_tracking,payroll,approval"
    )

    print("✅ Seeded HR Timesheet template")


def seed_all_hr_templates(library: PatternLibrary):
    """Seed all HR entity templates"""
    print("🌱 Seeding HR entity templates...")

    seed_hr_employee_template(library)
    seed_hr_position_template(library)
    seed_hr_department_template(library)
    seed_hr_timesheet_template(library)

    print("✅ All HR templates seeded!")


def seed_finance_invoice_template(library: PatternLibrary):
    """Seed Finance Invoice entity template"""

    library.add_entity_template(
        template_name="invoice",
        template_namespace="finance",
        description="Invoice with line items, tax calculation, and payment tracking",
        default_fields={
            # Invoice Details
            "invoice_number": {"type": "text", "required": True, "unique": True},
            "customer": {"type": "ref", "entity": "Customer", "required": True},
            "invoice_date": {"type": "date", "required": True, "default": "NOW()"},
            "due_date": {"type": "date", "required": True},

            # Financial Amounts
            "subtotal": {"type": "decimal", "precision": 10, "scale": 2, "required": True},
            "tax_amount": {"type": "decimal", "precision": 10, "scale": 2, "default": 0},
            "discount_amount": {"type": "decimal", "precision": 10, "scale": 2, "default": 0},
            "total_amount": {"type": "decimal", "precision": 10, "scale": 2, "required": True},
            "currency": {"type": "text", "default": "USD"},

            # Line Items
            "line_items": {"type": "array", "required": True},

            # Status and Payment
            "status": {"type": "enum", "values": ["draft", "sent", "paid", "overdue", "cancelled"], "default": "draft"},
            "payment_terms": {"type": "enum", "values": ["net_15", "net_30", "net_60", "due_on_receipt"], "default": "net_30"},
            "payment_method": {"type": "text"},
            "paid_date": {"type": "timestamp"},
            "paid_amount": {"type": "decimal", "precision": 10, "scale": 2, "default": 0},

            # Addresses
            "billing_address": {"type": "object", "required": True},
            "shipping_address": {"type": "object"},

            # Tax Information
            "tax_rate": {"type": "decimal", "precision": 5, "scale": 4, "default": 0.08},
            "tax_exempt": {"type": "boolean", "default": False},

            # Notes and References
            "notes": {"type": "text"},
            "po_number": {"type": "text"},  # Purchase order number
            "reference_number": {"type": "text"}
        },
        default_patterns={
            "state_machine": {
                "states": ["draft", "sent", "paid", "overdue", "cancelled"],
                "transitions": {
                    "draft->sent": {"action": "send_invoice"},
                    "sent->paid": {"action": "mark_paid"},
                    "sent->overdue": {"action": "mark_overdue"},
                    "any->cancelled": {"action": "cancel_invoice"}
                },
                "initial_state": "draft"
            },
            "audit_trail": {
                "track_versions": True
            },
            "computed_fields": {
                "computed_fields": {
                    "is_overdue": {
                        "type": "expression",
                        "expression": "NOW() > due_date and status in ('sent', 'overdue')"
                    },
                    "days_overdue": {
                        "type": "expression",
                        "expression": "(NOW() - due_date).days if is_overdue else 0"
                    },
                    "amount_due": {
                        "type": "expression",
                        "expression": "total_amount - paid_amount"
                    },
                    "is_fully_paid": {
                        "type": "expression",
                        "expression": "paid_amount >= total_amount"
                    },
                    "payment_status": {
                        "type": "expression",
                        "expression": "'paid' if is_fully_paid else 'partial' if paid_amount > 0 else 'unpaid'"
                    }
                }
            }
        },
        default_actions={
            "add_line_item": {
                "description": "Add line item to invoice",
                "parameters": [
                    {"name": "description", "type": "text"},
                    {"name": "quantity", "type": "decimal"},
                    {"name": "unit_price", "type": "decimal"},
                    {"name": "tax_rate", "type": "decimal"}
                ],
                "steps": [
                    {"type": "validate", "condition": "status == 'draft'", "error": "Cannot modify sent invoice"},
                    {"type": "assign", "variable": "line_total", "value": "quantity * unit_price"},
                    {"type": "assign", "variable": "line_tax", "value": "line_total * (tax_rate or 0)"},
                    {"type": "update", "entity": "Invoice", "where": "id = $id", "fields": {"line_items": "line_items || {'description': $description, 'quantity': $quantity, 'unit_price': $unit_price, 'tax_rate': $tax_rate, 'line_total': $line_total, 'line_tax': $line_tax}"}},
                    {"type": "call", "function": "recalculate_totals"},
                    {"type": "log", "message": "Line item added: {description}"}
                ]
            },
            "recalculate_totals": {
                "description": "Recalculate invoice totals",
                "steps": [
                    {"type": "assign", "variable": "subtotal", "value": "sum(item.line_total for item in line_items)"},
                    {"type": "assign", "variable": "tax_amount", "value": "sum(item.line_tax for item in line_items)"},
                    {"type": "assign", "variable": "total", "value": "subtotal + tax_amount - discount_amount"},
                    {"type": "update", "entity": "Invoice", "where": "id = $id", "fields": {"subtotal": "$subtotal", "tax_amount": "$tax_amount", "total_amount": "$total"}}
                ]
            },
            "send_invoice": {
                "description": "Send invoice to customer",
                "steps": [
                    {"type": "validate", "condition": "status == 'draft'", "error": "Invoice already sent"},
                    {"type": "validate", "condition": "total_amount > 0", "error": "Cannot send invoice with zero total"},
                    {"type": "call", "function": "transition_to", "args": {"target_state": "sent"}},
                    {"type": "log", "message": "Invoice sent to customer"}
                ]
            },
            "record_payment": {
                "description": "Record payment against invoice",
                "parameters": [
                    {"name": "amount", "type": "decimal"},
                    {"name": "payment_method", "type": "text"},
                    {"name": "payment_date", "type": "timestamp"}
                ],
                "steps": [
                    {"type": "validate", "condition": "amount > 0", "error": "Payment amount must be positive"},
                    {"type": "validate", "condition": "amount <= amount_due", "error": "Payment amount exceeds amount due"},
                    {"type": "update", "entity": "Invoice", "where": "id = $id", "fields": {"paid_amount": "paid_amount + amount", "payment_method": "$payment_method"}},
                    {"type": "if", "condition": "is_fully_paid", "then": [
                        {"type": "call", "function": "transition_to", "args": {"target_state": "paid"}},
                        {"type": "update", "entity": "Invoice", "where": "id = $id", "fields": {"paid_date": "$payment_date"}}
                    ]},
                    {"type": "create", "entity": "Payment", "data": {
                        "invoice_id": "$id",
                        "amount": "$amount",
                        "payment_method": "$payment_method",
                        "payment_date": "$payment_date"
                    }},
                    {"type": "log", "message": "Payment recorded: ${amount}"}
                ]
            },
            "apply_discount": {
                "description": "Apply discount to invoice",
                "parameters": [
                    {"name": "discount_amount", "type": "decimal"},
                    {"name": "reason", "type": "text"}
                ],
                "steps": [
                    {"type": "validate", "condition": "status == 'draft'", "error": "Cannot discount sent invoice"},
                    {"type": "validate", "condition": "discount_amount <= subtotal", "error": "Discount cannot exceed subtotal"},
                    {"type": "update", "entity": "Invoice", "where": "id = $id", "fields": {"discount_amount": "$discount_amount"}},
                    {"type": "call", "function": "recalculate_totals"},
                    {"type": "log", "message": "Discount applied: ${discount_amount} - {reason}"}
                ]
            }
        },
        configuration_options={
            "auto_calculate_tax": {"type": "boolean", "default": True},
            "default_tax_rate": {"type": "decimal", "default": 0.08},
            "require_po_number": {"type": "boolean", "default": False},
            "auto_send_on_create": {"type": "boolean", "default": False}
        },
        icon="📄",
        tags="finance,invoice,billing,payment,tax"
    )

    print("✅ Seeded Finance Invoice template")


def seed_finance_payment_template(library: PatternLibrary):
    """Seed Finance Payment entity template"""

    library.add_entity_template(
        template_name="payment",
        template_namespace="finance",
        description="Payment with processing, reconciliation, and refund capabilities",
        default_fields={
            # Payment Details
            "payment_id": {"type": "text", "unique": True},
            "invoice": {"type": "ref", "entity": "Invoice"},
            "customer": {"type": "ref", "entity": "Customer", "required": True},
            "amount": {"type": "decimal", "precision": 10, "scale": 2, "required": True},
            "currency": {"type": "text", "default": "USD"},

            # Payment Method
            "payment_method": {"type": "enum", "values": ["credit_card", "debit_card", "bank_transfer", "check", "cash", "paypal", "stripe"], "required": True},
            "payment_processor": {"type": "text"},  # stripe, paypal, etc.
            "processor_transaction_id": {"type": "text"},

            # Status and Processing
            "status": {"type": "enum", "values": ["pending", "processing", "completed", "failed", "refunded", "cancelled"], "default": "pending"},
            "payment_date": {"type": "timestamp", "required": True},
            "processed_date": {"type": "timestamp"},
            "failure_reason": {"type": "text"},

            # Refund Information
            "refund_amount": {"type": "decimal", "precision": 10, "scale": 2, "default": 0},
            "refund_date": {"type": "timestamp"},
            "refund_reason": {"type": "text"},

            # Reconciliation
            "reconciled": {"type": "boolean", "default": False},
            "reconciled_date": {"type": "timestamp"},
            "reconciled_by": {"type": "ref", "entity": "User"},

            # Additional Details
            "notes": {"type": "text"},
            "reference_number": {"type": "text"},
            "fee_amount": {"type": "decimal", "precision": 6, "scale": 2, "default": 0}  # Processing fee
        },
        default_patterns={
            "state_machine": {
                "states": ["pending", "processing", "completed", "failed", "refunded", "cancelled"],
                "transitions": {
                    "pending->processing": {"action": "process_payment"},
                    "processing->completed": {"action": "complete_payment"},
                    "processing->failed": {"action": "fail_payment"},
                    "completed->refunded": {"action": "refund_payment"},
                    "any->cancelled": {"action": "cancel_payment"}
                },
                "initial_state": "pending"
            },
            "audit_trail": {
                "track_versions": True
            },
            "computed_fields": {
                "computed_fields": {
                    "net_amount": {
                        "type": "expression",
                        "expression": "amount - fee_amount"
                    },
                    "is_successful": {
                        "type": "expression",
                        "expression": "status == 'completed'"
                    },
                    "can_refund": {
                        "type": "expression",
                        "expression": "status == 'completed' and refund_amount < amount"
                    },
                    "refundable_amount": {
                        "type": "expression",
                        "expression": "amount - refund_amount"
                    }
                }
            }
        },
        default_actions={
            "process_payment": {
                "description": "Process payment through payment processor",
                "steps": [
                    {"type": "validate", "condition": "status == 'pending'", "error": "Payment not in pending status"},
                    {"type": "call", "function": "transition_to", "args": {"target_state": "processing"}},
                    {"type": "update", "entity": "Payment", "where": "id = $id", "fields": {"processed_date": "NOW()"}},
                    {"type": "log", "message": "Payment processing started"}
                ]
            },
            "complete_payment": {
                "description": "Mark payment as completed",
                "parameters": [
                    {"name": "processor_transaction_id", "type": "text"}
                ],
                "steps": [
                    {"type": "call", "function": "transition_to", "args": {"target_state": "completed"}},
                    {"type": "update", "entity": "Payment", "where": "id = $id", "fields": {"processor_transaction_id": "$processor_transaction_id"}},
                    {"type": "if", "condition": "invoice", "then": [
                        {"type": "call", "function": "record_payment", "entity": "Invoice", "args": {"amount": "$amount", "payment_method": "$payment_method", "payment_date": "$payment_date"}}
                    ]},
                    {"type": "log", "message": "Payment completed: {processor_transaction_id}"}
                ]
            },
            "fail_payment": {
                "description": "Mark payment as failed",
                "parameters": [
                    {"name": "reason", "type": "text"}
                ],
                "steps": [
                    {"type": "call", "function": "transition_to", "args": {"target_state": "failed"}},
                    {"type": "update", "entity": "Payment", "where": "id = $id", "fields": {"failure_reason": "$reason"}},
                    {"type": "log", "message": "Payment failed: {reason}"}
                ]
            },
            "refund_payment": {
                "description": "Process refund for payment",
                "parameters": [
                    {"name": "refund_amount", "type": "decimal"},
                    {"name": "reason", "type": "text"}
                ],
                "steps": [
                    {"type": "validate", "condition": "can_refund", "error": "Payment cannot be refunded"},
                    {"type": "validate", "condition": "refund_amount <= refundable_amount", "error": "Refund amount exceeds refundable amount"},
                    {"type": "update", "entity": "Payment", "where": "id = $id", "fields": {"refund_amount": "refund_amount + $refund_amount", "refund_date": "NOW()", "refund_reason": "$reason"}},
                    {"type": "if", "condition": "refund_amount >= amount", "then": [
                        {"type": "call", "function": "transition_to", "args": {"target_state": "refunded"}}
                    ]},
                    {"type": "log", "message": "Refund processed: ${refund_amount} - {reason}"}
                ]
            },
            "reconcile_payment": {
                "description": "Mark payment as reconciled",
                "steps": [
                    {"type": "validate", "condition": "not reconciled", "error": "Payment already reconciled"},
                    {"type": "update", "entity": "Payment", "where": "id = $id", "fields": {"reconciled": True, "reconciled_date": "NOW()", "reconciled_by": "$current_user_id"}},
                    {"type": "log", "message": "Payment reconciled"}
                ]
            }
        },
        configuration_options={
            "auto_process_payments": {"type": "boolean", "default": False},
            "require_reconciliation": {"type": "boolean", "default": True},
            "allow_partial_refunds": {"type": "boolean", "default": True},
            "default_payment_processor": {"type": "text", "default": "stripe"}
        },
        icon="💳",
        tags="finance,payment,refund,reconciliation,processor"
    )

    print("✅ Seeded Finance Payment template")


def seed_finance_transaction_template(library: PatternLibrary):
    """Seed Finance Transaction entity template"""

    library.add_entity_template(
        template_name="transaction",
        template_namespace="finance",
        description="Financial transaction with double-entry bookkeeping and reconciliation",
        default_fields={
            # Transaction Details
            "transaction_id": {"type": "text", "unique": True},
            "date": {"type": "timestamp", "required": True, "default": "NOW()"},
            "description": {"type": "text", "required": True},
            "reference_number": {"type": "text"},

            # Double-Entry Bookkeeping
            "debit_account": {"type": "ref", "entity": "Account", "required": True},
            "credit_account": {"type": "ref", "entity": "Account", "required": True},
            "amount": {"type": "decimal", "precision": 12, "scale": 2, "required": True},
            "currency": {"type": "text", "default": "USD"},

            # Transaction Type
            "transaction_type": {"type": "enum", "values": ["income", "expense", "transfer", "adjustment", "fee"], "required": True},
            "category": {"type": "text"},

            # Related Entities
            "customer": {"type": "ref", "entity": "Customer"},
            "vendor": {"type": "ref", "entity": "Vendor"},
            "invoice": {"type": "ref", "entity": "Invoice"},
            "payment": {"type": "ref", "entity": "Payment"},
            "project": {"type": "ref", "entity": "Project"},

            # Status and Reconciliation
            "status": {"type": "enum", "values": ["pending", "posted", "reconciled", "voided"], "default": "pending"},
            "reconciled": {"type": "boolean", "default": False},
            "reconciled_date": {"type": "timestamp"},
            "reconciled_by": {"type": "ref", "entity": "User"},

            # Audit
            "created_by": {"type": "ref", "entity": "User", "required": True},
            "approved_by": {"type": "ref", "entity": "User"},
            "void_reason": {"type": "text"},

            # Tax Information
            "tax_category": {"type": "text"},
            "tax_amount": {"type": "decimal", "precision": 10, "scale": 2, "default": 0},
            "tax_rate": {"type": "decimal", "precision": 5, "scale": 4}
        },
        default_patterns={
            "state_machine": {
                "states": ["pending", "posted", "reconciled", "voided"],
                "transitions": {
                    "pending->posted": {"action": "post_transaction"},
                    "posted->reconciled": {"action": "reconcile_transaction"},
                    "any->voided": {"action": "void_transaction"}
                },
                "initial_state": "pending"
            },
            "audit_trail": {
                "track_versions": True
            },
            "computed_fields": {
                "computed_fields": {
                    "is_balanced": {
                        "type": "expression",
                        "expression": "debit_account and credit_account and debit_account != credit_account"
                    },
                    "net_impact": {
                        "type": "expression",
                        "expression": "amount if transaction_type in ('income', 'fee') else -amount"
                    },
                    "requires_approval": {
                        "type": "expression",
                        "expression": "amount > 1000 or transaction_type in ('adjustment', 'void')"
                    }
                }
            },
            "validation_chain": {
                "rules": [
                    {"field": "debit_account", "rule": "not_empty", "error": "Debit account is required"},
                    {"field": "credit_account", "rule": "not_empty", "error": "Credit account is required"},
                    {"field": "amount", "rule": "positive_number", "error": "Amount must be positive"},
                    {"field": "debit_account", "rule": "different_from_credit", "error": "Debit and credit accounts must be different"}
                ]
            }
        },
        default_actions={
            "post_transaction": {
                "description": "Post transaction to general ledger",
                "steps": [
                    {"type": "validate", "condition": "status == 'pending'", "error": "Transaction not in pending status"},
                    {"type": "validate", "condition": "is_balanced", "error": "Transaction is not balanced"},
                    {"type": "if", "condition": "requires_approval", "then": [
                        {"type": "validate", "condition": "approved_by IS NOT NULL", "error": "Transaction requires approval"}
                    ]},
                    {"type": "call", "function": "transition_to", "args": {"target_state": "posted"}},
                    {"type": "call", "function": "update_account_balances"},
                    {"type": "log", "message": "Transaction posted: {description}"}
                ]
            },
            "update_account_balances": {
                "description": "Update account balances after posting",
                "steps": [
                    {"type": "query", "sql": "SELECT balance FROM accounts WHERE id = $debit_account", "into": "debit_balance"},
                    {"type": "query", "sql": "SELECT balance FROM accounts WHERE id = $credit_account", "into": "credit_balance"},
                    {"type": "update", "entity": "Account", "where": "id = $debit_account", "fields": {"balance": "debit_balance.balance + $amount"}},
                    {"type": "update", "entity": "Account", "where": "id = $credit_account", "fields": {"balance": "credit_balance.balance - $amount"}},
                    {"type": "log", "message": "Account balances updated"}
                ]
            },
            "reconcile_transaction": {
                "description": "Mark transaction as reconciled",
                "steps": [
                    {"type": "validate", "condition": "status == 'posted'", "error": "Only posted transactions can be reconciled"},
                    {"type": "validate", "condition": "not reconciled", "error": "Transaction already reconciled"},
                    {"type": "update", "entity": "Transaction", "where": "id = $id", "fields": {"reconciled": True, "reconciled_date": "NOW()", "reconciled_by": "$current_user_id"}},
                    {"type": "call", "function": "transition_to", "args": {"target_state": "reconciled"}},
                    {"type": "log", "message": "Transaction reconciled"}
                ]
            },
            "void_transaction": {
                "description": "Void transaction",
                "parameters": [
                    {"name": "reason", "type": "text"}
                ],
                "steps": [
                    {"type": "validate", "condition": "status != 'reconciled'", "error": "Cannot void reconciled transaction"},
                    {"type": "call", "function": "transition_to", "args": {"target_state": "voided"}},
                    {"type": "update", "entity": "Transaction", "where": "id = $id", "fields": {"void_reason": "$reason"}},
                    {"type": "call", "function": "reverse_account_balances"},
                    {"type": "log", "message": "Transaction voided: {reason}"}
                ]
            },
            "reverse_account_balances": {
                "description": "Reverse account balance changes",
                "steps": [
                    {"type": "query", "sql": "SELECT balance FROM accounts WHERE id = $debit_account", "into": "debit_balance"},
                    {"type": "query", "sql": "SELECT balance FROM accounts WHERE id = $credit_account", "into": "credit_balance"},
                    {"type": "update", "entity": "Account", "where": "id = $debit_account", "fields": {"balance": "debit_balance.balance - $amount"}},
                    {"type": "update", "entity": "Account", "where": "id = $credit_account", "fields": {"balance": "credit_balance.balance + $amount"}},
                    {"type": "log", "message": "Account balances reversed"}
                ]
            },
            "approve_transaction": {
                "description": "Approve transaction for posting",
                "steps": [
                    {"type": "validate", "condition": "status == 'pending'", "error": "Transaction not pending"},
                    {"type": "update", "entity": "Transaction", "where": "id = $id", "fields": {"approved_by": "$current_user_id"}},
                    {"type": "log", "message": "Transaction approved by {current_user_id}"}
                ]
            }
        },
        configuration_options={
            "require_approval_threshold": {"type": "decimal", "default": 1000},
            "auto_post_small_transactions": {"type": "boolean", "default": False},
            "enable_double_entry_validation": {"type": "boolean", "default": True},
            "allow_transaction_voiding": {"type": "boolean", "default": True}
        },
        icon="💰",
        tags="finance,transaction,double_entry,ledger,reconciliation"
    )

    print("✅ Seeded Finance Transaction template")


def seed_all_finance_templates(library: PatternLibrary):
    """Seed all Finance entity templates"""
    print("🌱 Seeding Finance entity templates...")

    seed_finance_invoice_template(library)
    seed_finance_payment_template(library)
    seed_finance_transaction_template(library)

    print("✅ All Finance templates seeded!")


def seed_all_templates(library: PatternLibrary):
    """Seed all entity templates across all domains"""
    print("🌱 Seeding all entity templates...")

    seed_all_crm_templates(library)
    seed_all_ecommerce_templates(library)
    seed_all_healthcare_templates(library)
    seed_all_project_mgmt_templates(library)
    seed_all_hr_templates(library)
    seed_all_finance_templates(library)

    print("✅ All entity templates seeded!")


if __name__ == "__main__":
    # For testing
    library = PatternLibrary(":memory:")
    seed_all_templates(library)
    library.close()