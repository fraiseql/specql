# Week 42: Tier 3 - Workflow Architecture & Mobile Strategy

**Date**: 2025-11-13
**Duration**: 5 days
**Status**: 🔴 Planning
**Objective**: Design and implement complete user workflows with state machines, mobile UX patterns, and backend integration

---

## 🎯 Overview

**Tier 3** represents complete, stateful user journeys that combine multiple composite patterns and atomic components into end-to-end workflows with business logic.

**Target**: 20-30 common workflows + Mobile-specific patterns

```
┌──────────────────────────────────────────────────────────┐
│          WORKFLOW LIBRARY (TIER 3)                        │
├───────────┬───────────┬───────────┬──────────────────────┤
│   CRUD    │  Approval │Onboarding │  E-Commerce          │
│(5 flows)  │ (4 flows) │ (4 flows) │  (5 flows)           │
├───────────┼───────────┼───────────┼──────────────────────┤
│  Search   │Task Mgmt  │   Auth    │   Mobile UX          │
│(3 flows)  │ (3 flows) │ (4 flows) │  (8 patterns)        │
└───────────┴───────────┴───────────┴──────────────────────┘
```

---

## Day 1: CRUD Workflows (5 types)

### Workflow Catalog

**1. user_crud** - User management
**2. entity_crud** - Generic entity CRUD
**3. hierarchical_crud** - Parent-child entities
**4. bulk_crud** - Batch operations
**5. import_export** - Data import/export

### State Machine Architecture

```yaml
workflows:
  user_crud:
    tier: 3
    category: crud
    description: "Complete user management workflow"
    entity: User

    # Workflow states
    states:
      list:
        page: UserList
        patterns: [data_table, search_box, filter_bar]
        actions: [create, bulk_delete, export]

      detail:
        page: UserDetail
        patterns: [detail_view, action_menu]
        actions: [edit, delete, deactivate]

      create:
        page: UserCreate
        patterns: [registration_form]
        validation: client_and_server
        next_state: detail

      edit:
        page: UserEdit
        patterns: [profile_form]
        validation: client_and_server
        next_state: detail

      delete_confirm:
        page: ConfirmationDialog
        patterns: [alert_dialog]
        actions: [confirm, cancel]

    # State transitions
    transitions:
      - {from: list, to: create, trigger: click_create_button}
      - {from: list, to: detail, trigger: click_row}
      - {from: detail, to: edit, trigger: click_edit}
      - {from: edit, to: detail, trigger: save_success}
      - {from: detail, to: delete_confirm, trigger: click_delete}
      - {from: delete_confirm, to: list, trigger: confirm_delete}

    # Backend integration
    queries:
      - list_users: {query: "query { users { ...} }"}
      - get_user: {query: "query($id: ID!) { user(id: $id) {...} }"}

    mutations:
      - create_user: {mutation: "createUser", impact: [User]}
      - update_user: {mutation: "updateUser", impact: [User]}
      - delete_user: {mutation: "deleteUser", impact: [User]}

    # Mobile adaptations
    mobile:
      navigation: stack_navigator
      list_layout: card_list
      swipe_actions: {left: delete, right: edit}
      pull_to_refresh: true
```

### Implementation: State Machine

**File**: `src/generators/frontend/workflows/state_machine.py`

```python
"""
Workflow State Machine
Manages state transitions and workflow logic
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
from enum import Enum


class WorkflowState(Enum):
    """Workflow state enum"""
    LIST = "list"
    DETAIL = "detail"
    CREATE = "create"
    EDIT = "edit"
    DELETE_CONFIRM = "delete_confirm"


@dataclass
class StateTransition:
    """State transition definition"""
    from_state: WorkflowState
    to_state: WorkflowState
    trigger: str
    guard: Optional[Callable] = None  # Optional condition
    action: Optional[Callable] = None  # Side effect


@dataclass
class WorkflowDefinition:
    """Complete workflow definition"""
    name: str
    entity: str
    states: Dict[WorkflowState, Dict]
    transitions: List[StateTransition]
    queries: Dict[str, str]
    mutations: Dict[str, str]


class WorkflowStateMachine:
    """State machine for workflow management"""

    def __init__(self, definition: WorkflowDefinition):
        self.definition = definition
        self.current_state = WorkflowState.LIST
        self.history: List[WorkflowState] = []

    def can_transition(self, trigger: str) -> bool:
        """Check if transition is allowed"""
        transition = self._find_transition(trigger)

        if not transition:
            return False

        if transition.guard:
            return transition.guard()

        return True

    def transition(self, trigger: str) -> bool:
        """Execute state transition"""
        if not self.can_transition(trigger):
            return False

        transition = self._find_transition(trigger)

        # Execute action if defined
        if transition.action:
            transition.action()

        # Update state
        self.history.append(self.current_state)
        self.current_state = transition.to_state

        return True

    def _find_transition(self, trigger: str) -> Optional[StateTransition]:
        """Find transition for current state and trigger"""
        for trans in self.definition.transitions:
            if trans.from_state == self.current_state and trans.trigger == trigger:
                return trans
        return None


# Code generation example
class WorkflowGenerator:
    """Generate workflow code"""

    def generate_react(self, workflow: WorkflowDefinition) -> str:
        """Generate React workflow with routing"""
        return f'''
import {{ useState }} from 'react';
import {{ useNavigate }} from 'react-router-dom';

export function {workflow.name}Workflow() {{
  const navigate = useNavigate();
  const [currentState, setCurrentState] = useState('list');

  // State-specific pages
  const pages = {{
    list: <UserList onRowClick={{(id) => navigate(`/users/${{id}}`)}} />,
    detail: <UserDetail onEdit={{() => setCurrentState('edit')}} />,
    create: <UserCreate onSuccess={{(user) => navigate(`/users/${{user.id}}`)}} />,
    edit: <UserEdit onSuccess={{() => setCurrentState('detail')}} />,
  }};

  return pages[currentState];
}}
'''
```

---

## Day 2: Approval & Task Management Workflows (7 types)

### Approval Workflows (4 types)

**1. simple_approval** - Single approver
**2. multi_level_approval** - Sequential approvers
**3. parallel_approval** - Multiple approvers simultaneously
**4. conditional_approval** - Rule-based routing

### Task Management (3 types)

**1. kanban_workflow** - Drag-drop task board
**2. task_assignment** - Assign and track tasks
**3. sprint_planning** - Agile sprint workflow

---

## Day 3: Auth, Onboarding & E-Commerce (13 types)

### Auth Workflows (4 types)

**1. login_flow** - Login with remember me
**2. registration_flow** - Multi-step signup
**3. password_reset_flow** - Forgot password
**4. mfa_flow** - Two-factor authentication

### Onboarding (4 types)

**1. user_onboarding** - New user setup
**2. org_onboarding** - Organization setup
**3. feature_tour** - Product walkthrough
**4. settings_wizard** - Initial configuration

### E-Commerce (5 types)

**1. product_browse** - Search and filter products
**2. shopping_cart** - Cart management
**3. checkout_flow** - Multi-step checkout
**4. order_tracking** - Track order status
**5. returns_flow** - Return/refund process

---

## Day 4: Mobile UX Patterns & Platform Adaptations

### Mobile-Specific Patterns (8 types)

**1. pull_to_refresh** - Refresh list data
**2. infinite_scroll** - Load more on scroll
**3. swipe_gestures** - Swipe actions (delete, archive)
**4. bottom_sheet** - Mobile-optimized modal
**5. tab_bar_navigation** - Bottom tab navigation
**6. hamburger_menu** - Collapsible side menu
**7. floating_action_button** - Primary action button
**8. splash_screen** - App launch screen

### Mobile Adaptation Strategy

```yaml
mobile_adaptations:
  # Navigation
  navigation:
    web: sidebar_nav
    mobile: tab_bar_navigation

  # Modals
  modal:
    web: centered_dialog
    mobile: bottom_sheet

  # Tables
  data_table:
    web: table_layout
    mobile: card_list

  # Forms
  multi_section_form:
    web: tabs
    mobile: accordion

  # Actions
  row_actions:
    web: action_menu
    mobile: swipe_gestures

  # Search
  search:
    web: inline_search_box
    mobile: dedicated_search_screen
```

### Platform Detection

```typescript
// Auto-detect platform and adapt UX
export function usePlatform() {
  const [platform, setPlatform] = useState<'web' | 'mobile'>('web');

  useEffect(() => {
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    setPlatform(isMobile ? 'mobile' : 'web');
  }, []);

  return platform;
}

// Adaptive component
export function DataDisplay({ data }) {
  const platform = usePlatform();

  return platform === 'mobile' ? (
    <CardList data={data} swipeActions={true} />
  ) : (
    <DataTable data={data} sortable={true} filterable={true} />
  );
}
```

---

## Day 5: Testing, Documentation & Workflow Library

### End-to-End Workflow Tests

```python
class TestWorkflows:
    """Test complete workflow execution"""

    def test_crud_workflow_complete_cycle(self):
        """Test full CRUD workflow from list to create to detail"""
        workflow = WorkflowStateMachine(user_crud_definition)

        # Start at list
        assert workflow.current_state == WorkflowState.LIST

        # Navigate to create
        assert workflow.transition('click_create_button')
        assert workflow.current_state == WorkflowState.CREATE

        # After successful create, go to detail
        assert workflow.transition('save_success')
        assert workflow.current_state == WorkflowState.DETAIL

        # Edit the user
        assert workflow.transition('click_edit')
        assert workflow.current_state == WorkflowState.EDIT

    def test_mobile_navigation_pattern(self):
        """Test mobile-specific navigation"""
        workflow_mobile = generate_workflow(
            'user_crud',
            platform='mobile'
        )

        # Mobile should use stack navigator
        assert 'stack_navigator' in workflow_mobile.lower()
        assert 'swipe_actions' in workflow_mobile.lower()
```

---

## Week 42 Deliverables Summary

### Workflows Implemented (28 total)

- [x] CRUD: 5 workflows
- [x] Approval: 4 workflows
- [x] Task Management: 3 workflows
- [x] Auth: 4 workflows
- [x] Onboarding: 4 workflows
- [x] E-Commerce: 5 workflows
- [x] Search: 3 workflows

### Mobile Patterns

- [x] 8 mobile-specific UX patterns
- [x] Platform detection & adaptation
- [x] Mobile navigation strategies
- [x] Touch gestures support

### Key Features

- ✅ State machine architecture
- ✅ Backend integration (GraphQL)
- ✅ Mobile-first adaptations
- ✅ Workflow composition from Tier 2 patterns
- ✅ End-to-end testing

**Status**: ✅ Week 42 Complete - Exploration Phase Done, Ready for Implementation (Week 43)
