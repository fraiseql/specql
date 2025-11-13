# Week 56: E2E Testing & User Flow Specification

**Phase**: End-to-End Testing Infrastructure & Multi-Page Workflows
**Priority**: Critical - Enables complete user journey testing and cross-browser validation
**Timeline**: 5 working days
**Impact**: Universal E2E test specification, Playwright/Cypress parsers, user flow validation

---

## 🎯 Executive Summary

**Goal**: Create universal E2E test specification format for multi-page user flows:

```bash
# Reverse engineer existing E2E tests → Universal E2ETestSpec
specql reverse-e2e-tests tests/e2e/checkout.spec.ts --output test-specs/e2e/checkout.yaml
specql reverse-e2e-tests cypress/e2e/registration.cy.js --output test-specs/e2e/registration.yaml

# Validate E2E test coverage across user journeys
specql validate-e2e-coverage \
  --spec-dir test-specs/e2e/ \
  --app-url http://localhost:3000 \
  --report coverage-e2e.json

# Generate E2E tests in target framework from E2ETestSpec
specql generate-e2e-tests test-specs/e2e/**/*.yaml --framework playwright --output tests/e2e/
specql generate-e2e-tests test-specs/e2e/**/*.yaml --framework cypress --output cypress/e2e/
```

**Strategic Value**:
- **User Journey Validation**: Test complete multi-page workflows end-to-end
- **Cross-Browser Testing**: Ensure consistency across Chrome, Firefox, Safari, Edge
- **Framework Migration**: Migrate Cypress → Playwright with test preservation
- **API Mocking**: Network-level test isolation and deterministic tests
- **Page Object Reuse**: Extract and generate reusable page objects

**The Vision**:
```
Just as we have component tests (Week 55):
  FrontendTestSpec → Jest/Vitest/Flutter ✅

We should also have E2E tests (Week 56):
  E2ETestSpec → Playwright/Cypress/Selenium ❌ NEW

Then extend to complete user journey specifications:
  - Multi-page flows
  - Authentication journeys
  - Checkout workflows
  - Form wizards
```

---

## 📊 Current State Analysis

### ✅ What We Have (Reusable from Week 55)

1. **Component Test Infrastructure** (`src/testing/frontend_spec/`):
   - User interaction primitives ✅
   - Selector system ✅
   - Assertion types ✅
   - YAML serialization ✅

2. **Reverse Engineering Pipeline**:
   - Parser protocols ✅
   - AST mapping ✅
   - Pattern detection ✅

### 🔴 What We Need (New for E2E)

1. **E2E Test Specification** (`src/testing/e2e_spec/`):
   - `E2ETestSpec` AST (multi-page flows, navigation)
   - Page object model (selectors, actions per page)
   - Network request/response mocking
   - Browser context management (cookies, localStorage)
   - Cross-browser configuration

2. **E2E Test Parsers** (`src/reverse_engineering/e2e_tests/`):
   - Playwright test parser → E2ETestSpec
   - Cypress test parser → E2ETestSpec
   - Page object extractor
   - API mock pattern detector

3. **E2E Test Generators** (`src/generators/e2e_tests/`):
   - E2ETestSpec → Playwright
   - E2ETestSpec → Cypress
   - Page object code generation
   - API mock setup generation

---

## 🏗️ Architecture Design

### Universal E2ETestSpec AST

```python
# src/testing/e2e_spec/models.py

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Literal
from enum import Enum

class E2EFlowType(Enum):
    """Type of E2E flow"""
    SINGLE_PAGE = "single_page"  # Single page interactions
    MULTI_PAGE = "multi_page"  # Navigate across multiple pages
    AUTHENTICATION = "authentication"  # Login/signup flow
    CHECKOUT = "checkout"  # E-commerce checkout
    FORM_WIZARD = "form_wizard"  # Multi-step form
    CRUD_WORKFLOW = "crud_workflow"  # Create/read/update/delete
    SEARCH = "search"  # Search and filter

class NavigationType(Enum):
    """Types of navigation"""
    CLICK_LINK = "click_link"
    CLICK_BUTTON = "click_button"
    SUBMIT_FORM = "submit_form"
    BROWSER_BACK = "browser_back"
    BROWSER_FORWARD = "browser_forward"
    DIRECT_URL = "direct_url"
    REDIRECT = "redirect"

class WaitCondition(Enum):
    """Wait conditions for page transitions"""
    URL_MATCHES = "url_matches"
    ELEMENT_VISIBLE = "element_visible"
    ELEMENT_HIDDEN = "element_hidden"
    NETWORK_IDLE = "network_idle"
    LOAD_STATE = "load_state"
    CUSTOM_FUNCTION = "custom_function"

@dataclass
class PageDefinition:
    """
    Page object definition

    Examples:
        PageDefinition(
            name="HomePage",
            url="/",
            selectors={
                "nav_signup": {"type": "role", "value": "link", "options": {"name": "Sign Up"}},
                "search_input": {"type": "placeholder", "value": "Search..."},
                "user_menu": {"type": "test_id", "value": "user-menu"}
            },
            wait_for=[{"condition": "network_idle"}]
        )
    """
    name: str
    url: str
    selectors: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    wait_for: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class NavigationStep:
    """
    Navigation between pages

    Examples:
        NavigationStep(
            type=NavigationType.CLICK_LINK,
            selector={"type": "role", "value": "link", "options": {"name": "Sign Up"}},
            target_page="SignupPage",
            wait_for=[
                {"condition": "url_matches", "pattern": "/signup"},
                {"condition": "element_visible", "selector": {"type": "role", "value": "heading", "options": {"name": "Create Account"}}}
            ]
        )
    """
    type: NavigationType
    selector: Optional[Dict[str, Any]] = None
    target_page: str = ""
    target_url: Optional[str] = None
    wait_for: List[Dict[str, Any]] = field(default_factory=list)
    timeout: Optional[int] = None

@dataclass
class PageAction:
    """
    Action to perform on a page

    Examples:
        PageAction(
            page="SignupPage",
            actions=[
                {"type": "fill", "selector_name": "email_input", "value": "user@example.com"},
                {"type": "fill", "selector_name": "password_input", "value": "SecurePass123"},
                {"type": "click", "selector_name": "submit_button"}
            ]
        )
    """
    page: str
    actions: List[Dict[str, Any]] = field(default_factory=list)
    wait_before: Optional[int] = None  # Wait before executing actions (ms)
    wait_after: Optional[int] = None  # Wait after executing actions (ms)

@dataclass
class PageAssertion:
    """
    Assertion on a page

    Examples:
        PageAssertion(
            page="DashboardPage",
            assertions=[
                {"type": "url_matches", "pattern": "/dashboard"},
                {"type": "visible", "selector_name": "welcome_message"},
                {"type": "has_text", "selector_name": "user_name", "expected": "John Doe"}
            ]
        )
    """
    page: str
    assertions: List[Dict[str, Any]] = field(default_factory=list)
    timeout: Optional[int] = None

@dataclass
class NetworkMock:
    """
    Network request/response mock

    Examples:
        NetworkMock(
            method="GET",
            url_pattern="/api/user",
            response={
                "status": 200,
                "body": {"id": 1, "name": "John Doe", "email": "john@example.com"}
            },
            delay=100
        )

        NetworkMock(
            method="POST",
            url_pattern="/api/contacts",
            response={
                "status": 201,
                "body": {"id": 123, "status": "created"}
            }
        )
    """
    method: str  # GET, POST, PUT, DELETE, etc.
    url_pattern: str  # URL pattern to match (regex or glob)
    response: Dict[str, Any]  # {status, body, headers}
    delay: Optional[int] = None  # Response delay in ms
    match_params: Optional[Dict[str, Any]] = None  # Query params to match
    match_body: Optional[Dict[str, Any]] = None  # Request body to match

@dataclass
class BrowserContext:
    """
    Browser context configuration

    Examples:
        BrowserContext(
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone="America/New_York",
            permissions=["geolocation"],
            storage_state={
                "cookies": [{"name": "session", "value": "abc123", "domain": "example.com"}],
                "localStorage": [{"name": "user_id", "value": "12345"}]
            }
        )
    """
    viewport: Optional[Dict[str, int]] = None
    locale: Optional[str] = None
    timezone: Optional[str] = None
    permissions: List[str] = field(default_factory=list)
    geolocation: Optional[Dict[str, float]] = None
    storage_state: Optional[Dict[str, Any]] = None
    user_agent: Optional[str] = None

@dataclass
class E2ETestScenario:
    """
    Complete E2E test scenario

    Example:
        E2ETestScenario(
            name="complete_user_registration",
            description="User navigates from home page, signs up, and sees dashboard",
            flow_type=E2EFlowType.AUTHENTICATION,
            pages=[
                PageDefinition(name="HomePage", url="/"),
                PageDefinition(name="SignupPage", url="/signup"),
                PageDefinition(name="DashboardPage", url="/dashboard")
            ],
            steps=[
                # Navigate from home to signup
                NavigationStep(
                    type=NavigationType.CLICK_LINK,
                    selector={"type": "role", "value": "link", "options": {"name": "Sign Up"}},
                    target_page="SignupPage"
                ),
                # Fill signup form
                PageAction(
                    page="SignupPage",
                    actions=[
                        {"type": "fill", "selector_name": "email_input", "value": "user@example.com"},
                        {"type": "fill", "selector_name": "password_input", "value": "SecurePass123"},
                        {"type": "click", "selector_name": "submit_button"}
                    ]
                ),
                # Navigate to dashboard (automatic after submit)
                NavigationStep(
                    type=NavigationType.REDIRECT,
                    target_page="DashboardPage"
                ),
                # Assert we're on dashboard
                PageAssertion(
                    page="DashboardPage",
                    assertions=[
                        {"type": "url_matches", "pattern": "/dashboard"},
                        {"type": "visible", "selector_name": "welcome_message"}
                    ]
                )
            ],
            network_mocks=[
                NetworkMock(
                    method="POST",
                    url_pattern="/api/auth/signup",
                    response={"status": 201, "body": {"id": 1, "token": "abc123"}}
                )
            ]
        )
    """
    name: str
    description: str
    flow_type: E2EFlowType
    pages: List[PageDefinition]
    steps: List[Any]  # NavigationStep | PageAction | PageAssertion
    network_mocks: List[NetworkMock] = field(default_factory=list)
    browser_context: Optional[BrowserContext] = None
    setup: List[str] = field(default_factory=list)
    teardown: List[str] = field(default_factory=list)
    timeout: Optional[int] = None
    retry: Optional[int] = None

@dataclass
class E2ETestSpec:
    """
    Universal E2E test specification

    Example YAML:
    ```yaml
    e2e_test: UserRegistrationFlow
    flow_type: authentication
    base_url: http://localhost:3000

    pages:
      - name: HomePage
        url: /
        selectors:
          nav_signup: {type: role, value: link, options: {name: "Sign Up"}}

      - name: SignupPage
        url: /signup
        selectors:
          email_input: {type: label, value: "Email Address"}
          password_input: {type: label, value: "Password"}
          submit_button: {type: role, value: button, options: {name: "Create Account"}}

      - name: DashboardPage
        url: /dashboard
        selectors:
          welcome_message: {type: role, value: heading, options: {name: "Welcome"}}

    scenarios:
      - name: complete_user_registration
        description: User signs up and sees dashboard
        steps:
          - navigation:
              type: click_link
              selector: {type: role, value: link, options: {name: "Sign Up"}}
              target_page: SignupPage
              wait_for:
                - {condition: url_matches, pattern: "/signup"}

          - action:
              page: SignupPage
              actions:
                - {type: fill, selector_name: email_input, value: "user@example.com"}
                - {type: fill, selector_name: password_input, value: "SecurePass123"}
                - {type: click, selector_name: submit_button}

          - navigation:
              type: redirect
              target_page: DashboardPage

          - assertion:
              page: DashboardPage
              assertions:
                - {type: url_matches, pattern: "/dashboard"}
                - {type: visible, selector_name: welcome_message}

        network_mocks:
          - method: POST
            url_pattern: "/api/auth/signup"
            response:
              status: 201
              body: {id: 1, token: "abc123"}
    ```
    """
    test_name: str
    flow_type: E2EFlowType
    base_url: str
    pages: List[PageDefinition]
    scenarios: List[E2ETestScenario]
    browser_context: Optional[BrowserContext] = None
    global_network_mocks: List[NetworkMock] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_yaml(self) -> str:
        """Convert to YAML format"""
        import yaml

        data = {
            "e2e_test": self.test_name,
            "flow_type": self.flow_type.value,
            "base_url": self.base_url,
            "pages": [self._page_to_dict(p) for p in self.pages],
            "scenarios": [self._scenario_to_dict(s) for s in self.scenarios],
            "browser_context": self._context_to_dict(self.browser_context) if self.browser_context else None,
            "global_network_mocks": [self._mock_to_dict(m) for m in self.global_network_mocks],
            "metadata": self.metadata
        }

        return yaml.dump(data, sort_keys=False, allow_unicode=True)

    def _page_to_dict(self, page: PageDefinition) -> Dict[str, Any]:
        """Convert page to dictionary"""
        return {
            "name": page.name,
            "url": page.url,
            "selectors": page.selectors,
            "wait_for": page.wait_for,
            "metadata": page.metadata
        }

    def _scenario_to_dict(self, scenario: E2ETestScenario) -> Dict[str, Any]:
        """Convert scenario to dictionary"""
        return {
            "name": scenario.name,
            "description": scenario.description,
            "steps": [self._step_to_dict(s) for s in scenario.steps],
            "network_mocks": [self._mock_to_dict(m) for m in scenario.network_mocks],
            "setup": scenario.setup,
            "teardown": scenario.teardown,
            "timeout": scenario.timeout
        }

    def _step_to_dict(self, step: Any) -> Dict[str, Any]:
        """Convert step to dictionary"""
        if isinstance(step, NavigationStep):
            return {"navigation": {
                "type": step.type.value,
                "selector": step.selector,
                "target_page": step.target_page,
                "target_url": step.target_url,
                "wait_for": step.wait_for,
                "timeout": step.timeout
            }}
        elif isinstance(step, PageAction):
            return {"action": {
                "page": step.page,
                "actions": step.actions,
                "wait_before": step.wait_before,
                "wait_after": step.wait_after
            }}
        elif isinstance(step, PageAssertion):
            return {"assertion": {
                "page": step.page,
                "assertions": step.assertions,
                "timeout": step.timeout
            }}
        else:
            return {}

    def _mock_to_dict(self, mock: NetworkMock) -> Dict[str, Any]:
        """Convert network mock to dictionary"""
        return {
            "method": mock.method,
            "url_pattern": mock.url_pattern,
            "response": mock.response,
            "delay": mock.delay,
            "match_params": mock.match_params,
            "match_body": mock.match_body
        }

    def _context_to_dict(self, context: BrowserContext) -> Dict[str, Any]:
        """Convert browser context to dictionary"""
        return {
            "viewport": context.viewport,
            "locale": context.locale,
            "timezone": context.timezone,
            "permissions": context.permissions,
            "geolocation": context.geolocation,
            "storage_state": context.storage_state,
            "user_agent": context.user_agent
        }

    @classmethod
    def from_yaml(cls, yaml_content: str) -> "E2ETestSpec":
        """Parse YAML to E2ETestSpec"""
        import yaml
        data = yaml.safe_load(yaml_content)

        pages = [cls._dict_to_page(p) for p in data.get("pages", [])]
        scenarios = [cls._dict_to_scenario(s, pages) for s in data.get("scenarios", [])]

        browser_context = None
        if data.get("browser_context"):
            browser_context = cls._dict_to_context(data["browser_context"])

        global_mocks = [cls._dict_to_mock(m) for m in data.get("global_network_mocks", [])]

        return cls(
            test_name=data["e2e_test"],
            flow_type=E2EFlowType(data["flow_type"]),
            base_url=data["base_url"],
            pages=pages,
            scenarios=scenarios,
            browser_context=browser_context,
            global_network_mocks=global_mocks,
            metadata=data.get("metadata", {})
        )

    @classmethod
    def _dict_to_page(cls, data: Dict[str, Any]) -> PageDefinition:
        """Convert dictionary to PageDefinition"""
        return PageDefinition(
            name=data["name"],
            url=data["url"],
            selectors=data.get("selectors", {}),
            wait_for=data.get("wait_for", []),
            metadata=data.get("metadata", {})
        )

    @classmethod
    def _dict_to_scenario(cls, data: Dict[str, Any], pages: List[PageDefinition]) -> E2ETestScenario:
        """Convert dictionary to E2ETestScenario"""
        steps = [cls._dict_to_step(s) for s in data.get("steps", [])]
        mocks = [cls._dict_to_mock(m) for m in data.get("network_mocks", [])]

        return E2ETestScenario(
            name=data["name"],
            description=data.get("description", ""),
            flow_type=E2EFlowType.MULTI_PAGE,  # Inferred
            pages=pages,
            steps=steps,
            network_mocks=mocks,
            setup=data.get("setup", []),
            teardown=data.get("teardown", []),
            timeout=data.get("timeout")
        )

    @classmethod
    def _dict_to_step(cls, data: Dict[str, Any]) -> Any:
        """Convert dictionary to step"""
        if "navigation" in data:
            nav = data["navigation"]
            return NavigationStep(
                type=NavigationType(nav["type"]),
                selector=nav.get("selector"),
                target_page=nav.get("target_page", ""),
                target_url=nav.get("target_url"),
                wait_for=nav.get("wait_for", []),
                timeout=nav.get("timeout")
            )
        elif "action" in data:
            action = data["action"]
            return PageAction(
                page=action["page"],
                actions=action.get("actions", []),
                wait_before=action.get("wait_before"),
                wait_after=action.get("wait_after")
            )
        elif "assertion" in data:
            assertion = data["assertion"]
            return PageAssertion(
                page=assertion["page"],
                assertions=assertion.get("assertions", []),
                timeout=assertion.get("timeout")
            )
        else:
            raise ValueError(f"Unknown step type: {data}")

    @classmethod
    def _dict_to_mock(cls, data: Dict[str, Any]) -> NetworkMock:
        """Convert dictionary to NetworkMock"""
        return NetworkMock(
            method=data["method"],
            url_pattern=data["url_pattern"],
            response=data["response"],
            delay=data.get("delay"),
            match_params=data.get("match_params"),
            match_body=data.get("match_body")
        )

    @classmethod
    def _dict_to_context(cls, data: Dict[str, Any]) -> BrowserContext:
        """Convert dictionary to BrowserContext"""
        return BrowserContext(
            viewport=data.get("viewport"),
            locale=data.get("locale"),
            timezone=data.get("timezone"),
            permissions=data.get("permissions", []),
            geolocation=data.get("geolocation"),
            storage_state=data.get("storage_state"),
            user_agent=data.get("user_agent")
        )
```

### Three-Stage Pipeline for E2E Test Reverse Engineering

```
┌─────────────────────────────────────────────────────────────────┐
│ Stage 1: E2E Test Parser (Framework-Specific)                  │
│ ┌──────────────┐                                                │
│ │ Playwright   │──→ PlaywrightParser ──→ ParsedE2ETest         │
│ │ Cypress      │──→ CypressParser ──→ ParsedE2ETest            │
│ │ Selenium     │──→ SeleniumParser ──→ ParsedE2ETest (future)  │
│ └──────────────┘                                                │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ Stage 2: Test to E2ETestSpec Mapper (Universal)                │
│ ParsedE2ETest ──→ E2ETestSpec                                   │
│   - Extract page definitions and selectors                     │
│   - Map navigation steps                                       │
│   - Identify actions and assertions                            │
│   - Extract network mocks                                      │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ Stage 3: E2E Flow Pattern Detection & Enhancement              │
│ - Detect flow patterns (authentication, checkout, wizard)      │
│ - Extract page object models                                   │
│ - Identify critical user paths                                 │
│ - Suggest missing scenarios                                    │
└─────────────────────────────────────────────────────────────────┘
                           ↓
                    E2ETestSpec YAML Output
```

---

## 📅 Week 56: Day-by-Day Implementation

### Day 1: E2ETestSpec AST & Page Object Model

**Objective**: Define universal E2E test specification and page object system

**Morning: E2ETestSpec Models (3h)**

File created: `src/testing/e2e_spec/models.py` (shown above in Architecture Design)

**Afternoon: Page Object Extractor (3h)**

```python
# src/testing/e2e_spec/page_object_extractor.py

from typing import Dict, List, Set
from dataclasses import dataclass
from collections import defaultdict

from .models import PageDefinition, E2ETestSpec

@dataclass
class PageObjectModel:
    """
    Extracted page object model with selectors and actions

    Example:
        PageObjectModel(
            name="SignupPage",
            url="/signup",
            selectors={
                "email_input": {"type": "label", "value": "Email Address"},
                "password_input": {"type": "label", "value": "Password"},
                "submit_button": {"type": "role", "value": "button", "options": {"name": "Create Account"}}
            },
            actions={
                "fill_email": ["fill", "email_input", "{value}"],
                "fill_password": ["fill", "password_input", "{value}"],
                "submit": ["click", "submit_button"]
            }
        )
    """
    name: str
    url: str
    selectors: Dict[str, Dict]
    actions: Dict[str, List]
    metadata: Dict = None

class PageObjectExtractor:
    """
    Extract page object models from E2E tests

    Analyzes test scenarios to:
    - Identify unique pages
    - Extract selectors used on each page
    - Infer common actions
    - Generate reusable page objects
    """

    def extract_from_spec(self, spec: E2ETestSpec) -> List[PageObjectModel]:
        """Extract page objects from E2ETestSpec"""
        page_usage = self._analyze_page_usage(spec)
        page_objects = []

        for page_def in spec.pages:
            # Get all selectors used on this page
            selectors = page_def.selectors.copy()

            # Get all actions performed on this page
            actions = self._extract_page_actions(spec, page_def.name)

            page_objects.append(PageObjectModel(
                name=page_def.name,
                url=page_def.url,
                selectors=selectors,
                actions=actions,
                metadata={"usage_count": page_usage[page_def.name]}
            ))

        return page_objects

    def _analyze_page_usage(self, spec: E2ETestSpec) -> Dict[str, int]:
        """Count how many times each page is used"""
        usage = defaultdict(int)

        for scenario in spec.scenarios:
            for page in scenario.pages:
                usage[page.name] += 1

        return dict(usage)

    def _extract_page_actions(self, spec: E2ETestSpec, page_name: str) -> Dict[str, List]:
        """Extract common actions for a page"""
        actions = {}

        for scenario in spec.scenarios:
            for step in scenario.steps:
                if hasattr(step, 'page') and step.page == page_name:
                    # Extract action patterns
                    for action in step.actions:
                        action_type = action.get('type')
                        selector_name = action.get('selector_name')

                        if action_type and selector_name:
                            action_name = f"{action_type}_{selector_name}"
                            actions[action_name] = [action_type, selector_name, action.get('value', '{value}')]

        return actions

    def generate_typescript_page_object(self, page_obj: PageObjectModel) -> str:
        """Generate TypeScript page object class"""
        template = f'''
export class {page_obj.name} {{
  constructor(private page: Page) {{}}

  // Selectors
{self._generate_selector_getters(page_obj.selectors)}

  // Actions
{self._generate_action_methods(page_obj.actions)}

  // Navigation
  async goto() {{
    await this.page.goto('{page_obj.url}');
  }}

  async waitForLoad() {{
    await this.page.waitForLoadState('networkidle');
  }}
}}
'''
        return template

    def _generate_selector_getters(self, selectors: Dict[str, Dict]) -> str:
        """Generate selector getter methods"""
        lines = []

        for name, selector in selectors.items():
            selector_code = self._selector_to_playwright_code(selector)
            lines.append(f"  get {name}() {{ return this.page.{selector_code}; }}")

        return "\n".join(lines)

    def _generate_action_methods(self, actions: Dict[str, List]) -> str:
        """Generate action methods"""
        lines = []

        for action_name, [action_type, selector_name, value_template] in actions.items():
            if action_type == "fill":
                lines.append(f'''  async {action_name}(value: string) {{
    await this.{selector_name}.fill(value);
  }}''')
            elif action_type == "click":
                lines.append(f'''  async {action_name}() {{
    await this.{selector_name}.click();
  }}''')

        return "\n".join(lines)

    def _selector_to_playwright_code(self, selector: Dict) -> str:
        """Convert selector dict to Playwright code"""
        sel_type = selector.get('type')
        value = selector.get('value')
        options = selector.get('options', {})

        if sel_type == 'test_id':
            return f"getByTestId('{value}')"
        elif sel_type == 'role':
            if options:
                opts = ", ".join(f"{k}: '{v}'" for k, v in options.items())
                return f"getByRole('{value}', {{ {opts} }})"
            return f"getByRole('{value}')"
        elif sel_type == 'label':
            return f"getByLabel('{value}')"
        elif sel_type == 'text':
            return f"getByText('{value}')"
        else:
            return f"locator('{value}')"
```

**Tests** (`tests/unit/testing/e2e_spec/test_page_object_extractor.py`):

```python
import pytest
from src.testing.e2e_spec.models import (
    E2ETestSpec,
    E2ETestScenario,
    PageDefinition,
    PageAction,
    E2EFlowType
)
from src.testing.e2e_spec.page_object_extractor import PageObjectExtractor

class TestPageObjectExtractor:
    """Test page object extraction"""

    def setup_method(self):
        self.extractor = PageObjectExtractor()

    def test_extract_page_objects_from_spec(self):
        """Test extracting page objects from E2ETestSpec"""
        spec = E2ETestSpec(
            test_name="SignupFlow",
            flow_type=E2EFlowType.AUTHENTICATION,
            base_url="http://localhost:3000",
            pages=[
                PageDefinition(
                    name="HomePage",
                    url="/",
                    selectors={
                        "nav_signup": {"type": "role", "value": "link", "options": {"name": "Sign Up"}}
                    }
                ),
                PageDefinition(
                    name="SignupPage",
                    url="/signup",
                    selectors={
                        "email_input": {"type": "label", "value": "Email Address"},
                        "password_input": {"type": "label", "value": "Password"},
                        "submit_button": {"type": "role", "value": "button", "options": {"name": "Create Account"}}
                    }
                )
            ],
            scenarios=[
                E2ETestScenario(
                    name="complete_signup",
                    description="User signs up",
                    flow_type=E2EFlowType.AUTHENTICATION,
                    pages=[],
                    steps=[
                        PageAction(
                            page="SignupPage",
                            actions=[
                                {"type": "fill", "selector_name": "email_input", "value": "user@example.com"},
                                {"type": "fill", "selector_name": "password_input", "value": "pass123"},
                                {"type": "click", "selector_name": "submit_button"}
                            ]
                        )
                    ]
                )
            ]
        )

        page_objects = self.extractor.extract_from_spec(spec)

        assert len(page_objects) == 2

        signup_page = next(po for po in page_objects if po.name == "SignupPage")
        assert signup_page.url == "/signup"
        assert "email_input" in signup_page.selectors
        assert "password_input" in signup_page.selectors
        assert "fill_email_input" in signup_page.actions
        assert "click_submit_button" in signup_page.actions

    def test_generate_typescript_page_object(self):
        """Test generating TypeScript page object"""
        page_obj = self.extractor.extract_from_spec(
            # ... (use spec from previous test)
        )[1]  # SignupPage

        ts_code = self.extractor.generate_typescript_page_object(page_obj)

        assert "export class SignupPage" in ts_code
        assert "get email_input()" in ts_code
        assert "async fill_email_input(value: string)" in ts_code
        assert "await this.page.goto('/signup')" in ts_code
```

**Success Criteria**:
- ✅ E2ETestSpec AST models defined
- ✅ Page object extractor implemented
- ✅ TypeScript page object code generation
- ✅ YAML serialization/deserialization
- ✅ 10+ tests passing

---

### Day 2: Playwright Test Parser

**Objective**: Parse Playwright tests → E2ETestSpec

**Morning: Playwright Parser Implementation (3h)**

```python
# src/reverse_engineering/e2e_tests/playwright_parser.py

import re
from typing import List, Dict, Any
from pathlib import Path

from src.testing.e2e_spec.models import (
    E2ETestSpec,
    E2ETestScenario,
    PageDefinition,
    NavigationStep,
    PageAction,
    PageAssertion,
    NetworkMock,
    NavigationType,
    E2EFlowType
)

class PlaywrightParser:
    """
    Parse Playwright E2E tests to E2ETestSpec

    Example input:
    ```typescript
    test('user registration flow', async ({ page }) => {
      await page.goto('/');

      await page.getByRole('link', { name: 'Sign Up' }).click();
      await expect(page).toHaveURL(/.*signup/);

      await page.getByLabel('Email Address').fill('user@example.com');
      await page.getByLabel('Password').fill('SecurePass123');
      await page.getByRole('button', { name: 'Create Account' }).click();

      await expect(page).toHaveURL(/.*dashboard/);
      await expect(page.getByRole('heading', { name: 'Welcome' })).toBeVisible();
    });
    ```
    """

    def parse_file(self, file_path: Path) -> E2ETestSpec:
        """Parse Playwright test file to E2ETestSpec"""
        content = file_path.read_text()

        test_name = self._extract_test_name(content)
        base_url = self._extract_base_url(content)
        pages = self._extract_pages(content)
        scenarios = self._extract_scenarios(content, pages)
        network_mocks = self._extract_network_mocks(content)

        return E2ETestSpec(
            test_name=test_name,
            flow_type=self._infer_flow_type(scenarios),
            base_url=base_url or "http://localhost:3000",
            pages=pages,
            scenarios=scenarios,
            global_network_mocks=network_mocks,
            metadata={"parser": "playwright", "version": "1.0"}
        )

    def _extract_test_name(self, content: str) -> str:
        """Extract test name from test() or describe()"""
        # Try test block first
        match = re.search(r"test\(['\"](.+?)['\"]\s*,", content)
        if match:
            return match.group(1).replace(' ', '_')

        # Try describe block
        match = re.search(r"describe\(['\"](.+?)['\"]\s*,", content)
        if match:
            return match.group(1).replace(' ', '_')

        return "unnamed_e2e_test"

    def _extract_base_url(self, content: str) -> str:
        """Extract base URL from playwright.config or goto calls"""
        # Try config
        match = re.search(r"baseURL:\s*['\"](.+?)['\"]", content)
        if match:
            return match.group(1)

        # Try first goto
        match = re.search(r"page\.goto\(['\"](.+?)['\"]\)", content)
        if match:
            url = match.group(1)
            if url.startswith('http'):
                return '/'.join(url.split('/')[:3])
            return "http://localhost:3000"

        return "http://localhost:3000"

    def _extract_pages(self, content: str) -> List[PageDefinition]:
        """Extract page definitions from test"""
        pages_dict = {}

        # Find all goto calls to identify pages
        goto_pattern = r"page\.goto\(['\"](.+?)['\"]\)"
        for match in re.finditer(goto_pattern, content):
            url = match.group(1)
            page_name = self._url_to_page_name(url)

            if page_name not in pages_dict:
                pages_dict[page_name] = PageDefinition(
                    name=page_name,
                    url=url,
                    selectors={}
                )

        # Extract selectors for each page
        # This is simplified - real implementation would track context
        selector_pattern = r"page\.(getBy\w+)\((.+?)\)"
        for match in re.finditer(selector_pattern, content):
            method = match.group(1)
            args = match.group(2)

            selector_name, selector_dict = self._parse_playwright_selector(method, args)

            # Add to first page as fallback (real impl would track page context)
            if pages_dict:
                first_page = list(pages_dict.values())[0]
                first_page.selectors[selector_name] = selector_dict

        return list(pages_dict.values())

    def _extract_scenarios(self, content: str, pages: List[PageDefinition]) -> List[E2ETestScenario]:
        """Extract test scenarios"""
        scenarios = []

        # Find test blocks
        test_pattern = r"test\(['\"](.+?)['\"]\s*,\s*async\s*\(\{\s*page\s*\}\)\s*=>\s*\{([\s\S]+?)\n\}\)"

        for match in re.finditer(test_pattern, content):
            test_name = match.group(1)
            test_body = match.group(2)

            scenario = self._parse_scenario(test_name, test_body, pages)
            scenarios.append(scenario)

        return scenarios

    def _parse_scenario(self, name: str, body: str, pages: List[PageDefinition]) -> E2ETestScenario:
        """Parse single scenario"""
        steps = []

        # Parse each line as a step
        lines = [line.strip() for line in body.split('\n') if line.strip()]

        for line in lines:
            # Navigation: page.goto()
            if 'page.goto' in line:
                match = re.search(r"page\.goto\(['\"](.+?)['\"]\)", line)
                if match:
                    url = match.group(1)
                    page_name = self._url_to_page_name(url)

                    steps.append(NavigationStep(
                        type=NavigationType.DIRECT_URL,
                        target_page=page_name,
                        target_url=url
                    ))

            # Click action
            elif '.click()' in line:
                match = re.search(r"page\.(getBy\w+)\((.+?)\)\.click\(\)", line)
                if match:
                    method = match.group(1)
                    args = match.group(2)

                    selector_name, selector_dict = self._parse_playwright_selector(method, args)

                    # Determine if this is navigation or action
                    if 'link' in line.lower() or 'button' in line.lower():
                        steps.append(NavigationStep(
                            type=NavigationType.CLICK_LINK,
                            selector=selector_dict,
                            target_page=""  # Unknown without running
                        ))
                    else:
                        # Treat as action on current page
                        current_page = pages[0].name if pages else "UnknownPage"
                        steps.append(PageAction(
                            page=current_page,
                            actions=[{"type": "click", "selector": selector_dict}]
                        ))

            # Fill action
            elif '.fill(' in line:
                match = re.search(r"page\.(getBy\w+)\((.+?)\)\.fill\(['\"](.+?)['\"]\)", line)
                if match:
                    method = match.group(1)
                    args = match.group(2)
                    value = match.group(3)

                    selector_name, selector_dict = self._parse_playwright_selector(method, args)

                    current_page = pages[0].name if pages else "UnknownPage"
                    steps.append(PageAction(
                        page=current_page,
                        actions=[{"type": "fill", "selector": selector_dict, "value": value}]
                    ))

            # Assertion: expect(page).toHaveURL()
            elif 'expect(page).toHaveURL' in line:
                match = re.search(r"expect\(page\)\.toHaveURL\(/(.+?)/\)", line)
                if match:
                    url_pattern = match.group(1)

                    current_page = self._url_to_page_name(url_pattern)
                    steps.append(PageAssertion(
                        page=current_page,
                        assertions=[{"type": "url_matches", "pattern": url_pattern}]
                    ))

            # Assertion: expect(element).toBeVisible()
            elif 'toBeVisible()' in line:
                match = re.search(r"expect\(page\.(getBy\w+)\((.+?)\)\)\.toBeVisible\(\)", line)
                if match:
                    method = match.group(1)
                    args = match.group(2)

                    selector_name, selector_dict = self._parse_playwright_selector(method, args)

                    current_page = pages[-1].name if pages else "UnknownPage"
                    steps.append(PageAssertion(
                        page=current_page,
                        assertions=[{"type": "visible", "selector": selector_dict}]
                    ))

        return E2ETestScenario(
            name=name.replace(' ', '_').lower(),
            description=name,
            flow_type=E2EFlowType.MULTI_PAGE,
            pages=pages,
            steps=steps
        )

    def _extract_network_mocks(self, content: str) -> List[NetworkMock]:
        """Extract page.route() network mocks"""
        mocks = []

        # Pattern: page.route('/api/...', route => route.fulfill({...}))
        route_pattern = r"page\.route\(['\"](.+?)['\"]\s*,\s*(?:async\s*)?\(?route\)?\s*=>\s*route\.fulfill\(\{([\s\S]+?)\}\)"

        for match in re.finditer(route_pattern, content):
            url_pattern = match.group(1)
            fulfill_body = match.group(2)

            # Extract status
            status_match = re.search(r"status:\s*(\d+)", fulfill_body)
            status = int(status_match.group(1)) if status_match else 200

            # Extract body
            body_match = re.search(r"body:\s*JSON\.stringify\((\{[\s\S]+?\})\)", fulfill_body)
            body = body_match.group(1) if body_match else "{}"

            mocks.append(NetworkMock(
                method="GET",  # Default, could be enhanced
                url_pattern=url_pattern,
                response={"status": status, "body": body}
            ))

        return mocks

    def _parse_playwright_selector(self, method: str, args: str) -> tuple:
        """
        Parse Playwright selector to universal format

        Examples:
            getByTestId('submit-btn') → ('submit_btn', {type: 'test_id', value: 'submit-btn'})
            getByRole('button', { name: 'Submit' }) → ('submit_button', {type: 'role', value: 'button', options: {name: 'Submit'}})
        """
        if method == 'getByTestId':
            value = args.strip('\'"')
            return (value.replace('-', '_'), {"type": "test_id", "value": value})

        elif method == 'getByRole':
            # Parse role and options
            parts = args.split(',', 1)
            role = parts[0].strip('\'"')

            options = {}
            if len(parts) > 1:
                # Extract name from options object
                name_match = re.search(r"name:\s*['\"](.+?)['\"]", parts[1])
                if name_match:
                    options["name"] = name_match.group(1)

            selector_name = role.replace(' ', '_').lower()
            if options.get('name'):
                selector_name += '_' + options['name'].replace(' ', '_').lower()

            return (selector_name, {"type": "role", "value": role, "options": options})

        elif method == 'getByLabel':
            value = args.strip('\'"')
            return (value.replace(' ', '_').lower(), {"type": "label", "value": value})

        elif method == 'getByText':
            value = args.strip('\'"')
            return (value.replace(' ', '_').lower(), {"type": "text", "value": value})

        elif method == 'getByPlaceholder':
            value = args.strip('\'"')
            return (value.replace(' ', '_').lower(), {"type": "placeholder", "value": value})

        else:
            return ("unknown_selector", {"type": "css", "value": args})

    def _url_to_page_name(self, url: str) -> str:
        """Convert URL to page name"""
        # Remove leading slash and query params
        url = url.lstrip('/').split('?')[0].split('#')[0]

        if not url or url == '/':
            return "HomePage"

        # Convert /signup → SignupPage
        parts = url.split('/')
        name = ''.join(p.capitalize() for p in parts if p)
        return f"{name}Page"

    def _infer_flow_type(self, scenarios: List[E2ETestScenario]) -> E2EFlowType:
        """Infer flow type from scenario content"""
        # Simple heuristic based on scenario names
        for scenario in scenarios:
            name_lower = scenario.name.lower()

            if 'auth' in name_lower or 'login' in name_lower or 'signup' in name_lower:
                return E2EFlowType.AUTHENTICATION
            elif 'checkout' in name_lower or 'cart' in name_lower:
                return E2EFlowType.CHECKOUT
            elif 'wizard' in name_lower or 'multi' in name_lower:
                return E2EFlowType.FORM_WIZARD

        return E2EFlowType.MULTI_PAGE
```

**Afternoon: Playwright Parser Tests (3h)**

```python
# tests/unit/reverse_engineering/e2e_tests/test_playwright_parser.py

import pytest
from pathlib import Path
from src.reverse_engineering.e2e_tests.playwright_parser import PlaywrightParser
from src.testing.e2e_spec.models import NavigationType, E2EFlowType

class TestPlaywrightParser:
    """Test Playwright E2E test parser"""

    def setup_method(self):
        self.parser = PlaywrightParser()

    def test_parse_simple_navigation_test(self, tmp_path):
        """Test parsing simple navigation test"""
        test_file = tmp_path / "signup.spec.ts"
        test_file.write_text("""
import { test, expect } from '@playwright/test';

test('user registration flow', async ({ page }) => {
  await page.goto('/');

  await page.getByRole('link', { name: 'Sign Up' }).click();
  await expect(page).toHaveURL(/.*signup/);

  await page.getByLabel('Email Address').fill('user@example.com');
  await page.getByLabel('Password').fill('SecurePass123');
  await page.getByRole('button', { name: 'Create Account' }).click();

  await expect(page).toHaveURL(/.*dashboard/);
  await expect(page.getByRole('heading', { name: 'Welcome' })).toBeVisible();
});
        """)

        spec = self.parser.parse_file(test_file)

        assert spec.test_name == "user_registration_flow"
        assert spec.flow_type == E2EFlowType.AUTHENTICATION
        assert len(spec.scenarios) == 1

        scenario = spec.scenarios[0]
        assert scenario.name == "user_registration_flow"
        assert len(scenario.steps) > 0

        # Check navigation steps
        nav_steps = [s for s in scenario.steps if hasattr(s, 'type') and isinstance(s.type, NavigationType)]
        assert len(nav_steps) > 0

        # Check page actions
        action_steps = [s for s in scenario.steps if hasattr(s, 'actions')]
        assert len(action_steps) > 0

    def test_extract_pages_from_test(self, tmp_path):
        """Test extracting page definitions"""
        test_file = tmp_path / "test.spec.ts"
        test_file.write_text("""
test('navigate pages', async ({ page }) => {
  await page.goto('/');
  await page.goto('/about');
  await page.goto('/contact');
});
        """)

        spec = self.parser.parse_file(test_file)

        assert len(spec.pages) == 3
        page_names = [p.name for p in spec.pages]
        assert "HomePage" in page_names
        assert "AboutPage" in page_names
        assert "ContactPage" in page_names

    def test_extract_network_mocks(self, tmp_path):
        """Test extracting page.route() mocks"""
        test_file = tmp_path / "test.spec.ts"
        test_file.write_text("""
test('with mock', async ({ page }) => {
  await page.route('/api/user', route => route.fulfill({
    status: 200,
    body: JSON.stringify({ id: 1, name: 'John' })
  }));

  await page.goto('/profile');
});
        """)

        spec = self.parser.parse_file(test_file)

        assert len(spec.global_network_mocks) == 1
        mock = spec.global_network_mocks[0]
        assert mock.url_pattern == "/api/user"
        assert mock.response["status"] == 200

    def test_parse_playwright_selector(self):
        """Test parsing Playwright selectors"""
        test_cases = [
            ("getByTestId", "'submit-btn'", "submit_btn", {"type": "test_id", "value": "submit-btn"}),
            ("getByRole", "'button', { name: 'Submit' }", "button_submit", {"type": "role", "value": "button", "options": {"name": "Submit"}}),
            ("getByLabel", "'Email Address'", "email_address", {"type": "label", "value": "Email Address"}),
        ]

        for method, args, expected_name, expected_dict in test_cases:
            name, selector_dict = self.parser._parse_playwright_selector(method, args)
            assert name == expected_name
            assert selector_dict == expected_dict
```

**Success Criteria**:
- ✅ Playwright parser implemented
- ✅ Parses test() blocks and scenarios
- ✅ Extracts page.goto() navigation
- ✅ Extracts page.getBy*() selectors
- ✅ Extracts expect() assertions
- ✅ Extracts page.route() network mocks
- ✅ Converts to E2ETestSpec
- ✅ 10+ tests passing

---

### Day 3: Playwright Test Generator

**Objective**: Generate Playwright tests from E2ETestSpec

**Morning: Playwright Generator Implementation (3h)**

```python
# src/generators/e2e_tests/playwright_generator.py

from typing import Dict, Any, List
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from src.testing.e2e_spec.models import (
    E2ETestSpec,
    E2ETestScenario,
    NavigationStep,
    PageAction,
    PageAssertion,
    NavigationType
)

class PlaywrightGenerator:
    """
    Generate Playwright E2E tests from E2ETestSpec

    Output example:
    ```typescript
    import { test, expect } from '@playwright/test';

    test.describe('User Registration Flow', () => {
      test('complete user registration', async ({ page }) => {
        // Navigate to home page
        await page.goto('/');

        // Click sign up link
        await page.getByRole('link', { name: 'Sign Up' }).click();
        await expect(page).toHaveURL(/.*signup/);

        // Fill signup form
        await page.getByLabel('Email Address').fill('user@example.com');
        await page.getByLabel('Password').fill('SecurePass123');
        await page.getByRole('button', { name: 'Create Account' }).click();

        // Verify dashboard
        await expect(page).toHaveURL(/.*dashboard/);
        await expect(page.getByRole('heading', { name: 'Welcome' })).toBeVisible();
      });
    });
    ```
    """

    def __init__(self, template_dir: Path):
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def generate(self, spec: E2ETestSpec, output_path: Path) -> None:
        """Generate Playwright test file from E2ETestSpec"""
        template = self.env.get_template('playwright_test.spec.ts.j2')

        rendered = template.render(
            test_name=spec.test_name,
            base_url=spec.base_url,
            scenarios=self._prepare_scenarios(spec.scenarios),
            network_mocks=spec.global_network_mocks,
            has_mocks=len(spec.global_network_mocks) > 0
        )

        output_path.write_text(rendered)

    def _prepare_scenarios(self, scenarios: List[E2ETestScenario]) -> List[Dict[str, Any]]:
        """Prepare scenarios for template rendering"""
        prepared = []

        for scenario in scenarios:
            prepared.append({
                "name": scenario.description,
                "steps": self._render_steps(scenario.steps),
                "timeout": scenario.timeout
            })

        return prepared

    def _render_steps(self, steps: List[Any]) -> List[Dict[str, str]]:
        """Render scenario steps to Playwright code"""
        rendered_steps = []

        for step in steps:
            if isinstance(step, NavigationStep):
                rendered_steps.extend(self._render_navigation(step))
            elif isinstance(step, PageAction):
                rendered_steps.extend(self._render_action(step))
            elif isinstance(step, PageAssertion):
                rendered_steps.extend(self._render_assertion(step))

        return rendered_steps

    def _render_navigation(self, nav: NavigationStep) -> List[Dict[str, str]]:
        """Render navigation step"""
        steps = []

        if nav.type == NavigationType.DIRECT_URL:
            steps.append({
                "comment": f"Navigate to {nav.target_page}",
                "code": f"await page.goto('{nav.target_url}');"
            })

        elif nav.type == NavigationType.CLICK_LINK or nav.type == NavigationType.CLICK_BUTTON:
            selector_code = self._selector_to_playwright(nav.selector)
            steps.append({
                "comment": f"Click to navigate to {nav.target_page}",
                "code": f"await page.{selector_code}.click();"
            })

        # Add wait conditions
        for wait in nav.wait_for:
            wait_code = self._render_wait_condition(wait)
            if wait_code:
                steps.append({"comment": "", "code": wait_code})

        return steps

    def _render_action(self, action: PageAction) -> List[Dict[str, str]]:
        """Render page action"""
        steps = []

        if action.wait_before:
            steps.append({
                "comment": "",
                "code": f"await page.waitForTimeout({action.wait_before});"
            })

        steps.append({
            "comment": f"Actions on {action.page}",
            "code": ""
        })

        for act in action.actions:
            act_type = act.get('type')
            selector = act.get('selector')
            value = act.get('value')

            selector_code = self._selector_to_playwright(selector)

            if act_type == 'fill':
                steps.append({
                    "comment": "",
                    "code": f"await page.{selector_code}.fill('{value}');"
                })
            elif act_type == 'click':
                steps.append({
                    "comment": "",
                    "code": f"await page.{selector_code}.click();"
                })
            elif act_type == 'select':
                steps.append({
                    "comment": "",
                    "code": f"await page.{selector_code}.selectOption('{value}');"
                })

        if action.wait_after:
            steps.append({
                "comment": "",
                "code": f"await page.waitForTimeout({action.wait_after});"
            })

        return steps

    def _render_assertion(self, assertion: PageAssertion) -> List[Dict[str, str]]:
        """Render page assertion"""
        steps = []

        steps.append({
            "comment": f"Verify {assertion.page}",
            "code": ""
        })

        for asrt in assertion.assertions:
            asrt_type = asrt.get('type')

            if asrt_type == 'url_matches':
                pattern = asrt.get('pattern')
                steps.append({
                    "comment": "",
                    "code": f"await expect(page).toHaveURL(/{pattern}/);"
                })

            elif asrt_type == 'visible':
                selector = asrt.get('selector')
                selector_code = self._selector_to_playwright(selector)
                steps.append({
                    "comment": "",
                    "code": f"await expect(page.{selector_code}).toBeVisible();"
                })

            elif asrt_type == 'has_text':
                selector = asrt.get('selector')
                expected = asrt.get('expected')
                selector_code = self._selector_to_playwright(selector)
                steps.append({
                    "comment": "",
                    "code": f"await expect(page.{selector_code}).toHaveText('{expected}');"
                })

        return steps

    def _selector_to_playwright(self, selector: Dict[str, Any]) -> str:
        """Convert universal selector to Playwright code"""
        if not selector:
            return "locator('body')"

        sel_type = selector.get('type')
        value = selector.get('value')
        options = selector.get('options', {})

        if sel_type == 'test_id':
            return f"getByTestId('{value}')"

        elif sel_type == 'role':
            if options:
                opts = ", ".join(f"{k}: '{v}'" for k, v in options.items())
                return f"getByRole('{value}', {{ {opts} }})"
            return f"getByRole('{value}')"

        elif sel_type == 'label':
            return f"getByLabel('{value}')"

        elif sel_type == 'text':
            return f"getByText('{value}')"

        elif sel_type == 'placeholder':
            return f"getByPlaceholder('{value}')"

        elif sel_type == 'css':
            return f"locator('{value}')"

        else:
            return f"locator('{value}')"

    def _render_wait_condition(self, wait: Dict[str, Any]) -> str:
        """Render wait condition"""
        condition = wait.get('condition')

        if condition == 'url_matches':
            pattern = wait.get('pattern')
            return f"await expect(page).toHaveURL(/{pattern}/);"

        elif condition == 'element_visible':
            selector = wait.get('selector')
            selector_code = self._selector_to_playwright(selector)
            return f"await expect(page.{selector_code}).toBeVisible();"

        elif condition == 'network_idle':
            return "await page.waitForLoadState('networkidle');"

        return ""
```

**Jinja2 Template** (`templates/e2e_tests/playwright_test.spec.ts.j2`):

```typescript
import { test, expect } from '@playwright/test';

{% if has_mocks %}
test.beforeEach(async ({ page }) => {
  // Setup network mocks
  {% for mock in network_mocks %}
  await page.route('{{ mock.url_pattern }}', route => route.fulfill({
    status: {{ mock.response.status }},
    body: JSON.stringify({{ mock.response.body }})
  }));
  {% endfor %}
});
{% endif %}

test.describe('{{ test_name | title }}', () => {
  {% for scenario in scenarios %}
  test('{{ scenario.name }}'{% if scenario.timeout %}, { timeout: {{ scenario.timeout }} }{% endif %}, async ({ page }) => {
    {% for step in scenario.steps %}
    {% if step.comment %}
    // {{ step.comment }}
    {% endif %}
    {{ step.code }}
    {% endfor %}
  });

  {% endfor %}
});
```

**Afternoon: Playwright Generator Tests (3h)**

```python
# tests/unit/generators/e2e_tests/test_playwright_generator.py

import pytest
from pathlib import Path
from src.generators.e2e_tests.playwright_generator import PlaywrightGenerator
from src.testing.e2e_spec.models import (
    E2ETestSpec,
    E2ETestScenario,
    PageDefinition,
    NavigationStep,
    PageAction,
    PageAssertion,
    NavigationType,
    E2EFlowType
)

class TestPlaywrightGenerator:
    """Test Playwright E2E test generator"""

    def setup_method(self):
        template_dir = Path(__file__).parent.parent.parent.parent / "src" / "generators" / "e2e_tests" / "templates"
        self.generator = PlaywrightGenerator(template_dir)

    def test_generate_simple_e2e_test(self, tmp_path):
        """Test generating simple E2E test"""
        spec = E2ETestSpec(
            test_name="user_signup",
            flow_type=E2EFlowType.AUTHENTICATION,
            base_url="http://localhost:3000",
            pages=[
                PageDefinition(
                    name="HomePage",
                    url="/",
                    selectors={"nav_signup": {"type": "role", "value": "link", "options": {"name": "Sign Up"}}}
                ),
                PageDefinition(
                    name="SignupPage",
                    url="/signup",
                    selectors={
                        "email_input": {"type": "label", "value": "Email Address"},
                        "password_input": {"type": "label", "value": "Password"},
                        "submit_button": {"type": "role", "value": "button", "options": {"name": "Create Account"}}
                    }
                ),
                PageDefinition(
                    name="DashboardPage",
                    url="/dashboard",
                    selectors={"welcome_message": {"type": "role", "value": "heading", "options": {"name": "Welcome"}}}
                )
            ],
            scenarios=[
                E2ETestScenario(
                    name="complete_signup",
                    description="User completes signup flow",
                    flow_type=E2EFlowType.AUTHENTICATION,
                    pages=[],
                    steps=[
                        NavigationStep(
                            type=NavigationType.DIRECT_URL,
                            target_page="HomePage",
                            target_url="/"
                        ),
                        NavigationStep(
                            type=NavigationType.CLICK_LINK,
                            selector={"type": "role", "value": "link", "options": {"name": "Sign Up"}},
                            target_page="SignupPage",
                            wait_for=[{"condition": "url_matches", "pattern": ".*signup"}]
                        ),
                        PageAction(
                            page="SignupPage",
                            actions=[
                                {"type": "fill", "selector": {"type": "label", "value": "Email Address"}, "value": "user@example.com"},
                                {"type": "fill", "selector": {"type": "label", "value": "Password"}, "value": "SecurePass123"},
                                {"type": "click", "selector": {"type": "role", "value": "button", "options": {"name": "Create Account"}}}
                            ]
                        ),
                        PageAssertion(
                            page="DashboardPage",
                            assertions=[
                                {"type": "url_matches", "pattern": ".*dashboard"},
                                {"type": "visible", "selector": {"type": "role", "value": "heading", "options": {"name": "Welcome"}}}
                            ]
                        )
                    ]
                )
            ]
        )

        output_file = tmp_path / "signup.spec.ts"
        self.generator.generate(spec, output_file)

        content = output_file.read_text()

        # Check imports
        assert "import { test, expect } from '@playwright/test';" in content

        # Check test structure
        assert "test.describe('User Signup', () => {" in content
        assert "test('User completes signup flow'," in content

        # Check navigation
        assert "await page.goto('/');" in content
        assert "await page.getByRole('link', { name: 'Sign Up' }).click();" in content

        # Check actions
        assert "await page.getByLabel('Email Address').fill('user@example.com');" in content
        assert "await page.getByLabel('Password').fill('SecurePass123');" in content

        # Check assertions
        assert "await expect(page).toHaveURL(/.*dashboard/);" in content
        assert "await expect(page.getByRole('heading', { name: 'Welcome' })).toBeVisible();" in content
```

**Success Criteria**:
- ✅ Playwright generator implemented
- ✅ Generates complete test files
- ✅ Renders navigation steps
- ✅ Renders page actions
- ✅ Renders assertions
- ✅ Proper TypeScript syntax
- ✅ 8+ tests passing

---

### Day 4: Cypress Support

**Objective**: Add Cypress parser and generator

**Morning: Cypress Parser (2h)**

```python
# src/reverse_engineering/e2e_tests/cypress_parser.py

import re
from typing import List, Dict, Any
from pathlib import Path

from src.testing.e2e_spec.models import (
    E2ETestSpec,
    E2ETestScenario,
    PageDefinition,
    NavigationStep,
    PageAction,
    PageAssertion,
    NavigationType,
    E2EFlowType
)

class CypressParser:
    """
    Parse Cypress E2E tests to E2ETestSpec

    Example input:
    ```javascript
    describe('User Registration', () => {
      it('should complete signup flow', () => {
        cy.visit('/');

        cy.get('[data-cy="nav-signup"]').click();
        cy.url().should('include', '/signup');

        cy.get('[data-cy="email-input"]').type('user@example.com');
        cy.get('[data-cy="password-input"]').type('SecurePass123');
        cy.get('[data-cy="submit-btn"]').click();

        cy.url().should('include', '/dashboard');
        cy.get('[data-cy="welcome-msg"]').should('be.visible');
      });
    });
    ```
    """

    def parse_file(self, file_path: Path) -> E2ETestSpec:
        """Parse Cypress test file"""
        content = file_path.read_text()

        test_name = self._extract_test_name(content)
        base_url = "http://localhost:3000"  # From cypress.config or env
        pages = self._extract_pages(content)
        scenarios = self._extract_scenarios(content, pages)

        return E2ETestSpec(
            test_name=test_name,
            flow_type=E2EFlowType.MULTI_PAGE,
            base_url=base_url,
            pages=pages,
            scenarios=scenarios,
            metadata={"parser": "cypress", "version": "1.0"}
        )

    def _extract_test_name(self, content: str) -> str:
        """Extract test name from describe()"""
        match = re.search(r"describe\(['\"](.+?)['\"]\s*,", content)
        if match:
            return match.group(1).replace(' ', '_')
        return "cypress_test"

    def _extract_pages(self, content: str) -> List[PageDefinition]:
        """Extract pages from cy.visit() calls"""
        pages_dict = {}

        visit_pattern = r"cy\.visit\(['\"](.+?)['\"]\)"
        for match in re.finditer(visit_pattern, content):
            url = match.group(1)
            page_name = self._url_to_page_name(url)

            if page_name not in pages_dict:
                pages_dict[page_name] = PageDefinition(
                    name=page_name,
                    url=url,
                    selectors={}
                )

        return list(pages_dict.values())

    def _extract_scenarios(self, content: str, pages: List[PageDefinition]) -> List[E2ETestScenario]:
        """Extract it() test blocks"""
        scenarios = []

        it_pattern = r"it\(['\"](.+?)['\"]\s*,\s*\(\)\s*=>\s*\{([\s\S]+?)\n\s*\}\)"

        for match in re.finditer(it_pattern, content):
            test_name = match.group(1)
            test_body = match.group(2)

            scenario = self._parse_scenario(test_name, test_body, pages)
            scenarios.append(scenario)

        return scenarios

    def _parse_scenario(self, name: str, body: str, pages: List[PageDefinition]) -> E2ETestScenario:
        """Parse scenario"""
        steps = []
        lines = [line.strip() for line in body.split('\n') if line.strip() and not line.strip().startswith('//')]

        for line in lines:
            # Visit
            if 'cy.visit' in line:
                match = re.search(r"cy\.visit\(['\"](.+?)['\"]\)", line)
                if match:
                    url = match.group(1)
                    steps.append(NavigationStep(
                        type=NavigationType.DIRECT_URL,
                        target_page=self._url_to_page_name(url),
                        target_url=url
                    ))

            # Click
            elif '.click()' in line:
                match = re.search(r"cy\.get\(['\"](.+?)['\"]\)\.click\(\)", line)
                if match:
                    selector = match.group(1)
                    steps.append(PageAction(
                        page="UnknownPage",
                        actions=[{"type": "click", "selector": self._parse_cypress_selector(selector)}]
                    ))

            # Type
            elif '.type(' in line:
                match = re.search(r"cy\.get\(['\"](.+?)['\"]\)\.type\(['\"](.+?)['\"]\)", line)
                if match:
                    selector = match.group(1)
                    value = match.group(2)
                    steps.append(PageAction(
                        page="UnknownPage",
                        actions=[{"type": "fill", "selector": self._parse_cypress_selector(selector), "value": value}]
                    ))

            # URL assertion
            elif "cy.url().should('include'," in line:
                match = re.search(r"cy\.url\(\)\.should\('include',\s*['\"](.+?)['\"]\)", line)
                if match:
                    url_part = match.group(1)
                    steps.append(PageAssertion(
                        page="UnknownPage",
                        assertions=[{"type": "url_matches", "pattern": url_part}]
                    ))

            # Visibility assertion
            elif ".should('be.visible')" in line:
                match = re.search(r"cy\.get\(['\"](.+?)['\"]\)\.should\('be\.visible'\)", line)
                if match:
                    selector = match.group(1)
                    steps.append(PageAssertion(
                        page="UnknownPage",
                        assertions=[{"type": "visible", "selector": self._parse_cypress_selector(selector)}]
                    ))

        return E2ETestScenario(
            name=name.replace(' ', '_').lower(),
            description=name,
            flow_type=E2EFlowType.MULTI_PAGE,
            pages=pages,
            steps=steps
        )

    def _parse_cypress_selector(self, selector: str) -> Dict[str, Any]:
        """Parse Cypress selector to universal format"""
        # data-cy attribute
        if selector.startswith('[data-cy='):
            value = selector.split('"')[1] if '"' in selector else selector.split("'")[1]
            return {"type": "test_id", "value": value}

        # CSS selector
        return {"type": "css", "value": selector}

    def _url_to_page_name(self, url: str) -> str:
        """Convert URL to page name"""
        url = url.lstrip('/').split('?')[0]
        if not url:
            return "HomePage"
        return ''.join(p.capitalize() for p in url.split('/')) + "Page"
```

**Cypress Generator (2h)**:

```python
# src/generators/e2e_tests/cypress_generator.py

from typing import Dict, Any, List
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from src.testing.e2e_spec.models import (
    E2ETestSpec,
    E2ETestScenario,
    NavigationStep,
    PageAction,
    PageAssertion,
    NavigationType
)

class CypressGenerator:
    """Generate Cypress E2E tests from E2ETestSpec"""

    def __init__(self, template_dir: Path):
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def generate(self, spec: E2ETestSpec, output_path: Path) -> None:
        """Generate Cypress test file"""
        template = self.env.get_template('cypress_test.cy.js.j2')

        rendered = template.render(
            test_name=spec.test_name,
            scenarios=self._prepare_scenarios(spec.scenarios)
        )

        output_path.write_text(rendered)

    def _prepare_scenarios(self, scenarios: List[E2ETestScenario]) -> List[Dict[str, Any]]:
        """Prepare scenarios"""
        prepared = []

        for scenario in scenarios:
            prepared.append({
                "name": scenario.description,
                "steps": self._render_steps(scenario.steps)
            })

        return prepared

    def _render_steps(self, steps: List[Any]) -> List[str]:
        """Render steps to Cypress code"""
        rendered = []

        for step in steps:
            if isinstance(step, NavigationStep):
                if step.type == NavigationType.DIRECT_URL:
                    rendered.append(f"cy.visit('{step.target_url}');")

            elif isinstance(step, PageAction):
                for action in step.actions:
                    selector = self._selector_to_cypress(action['selector'])
                    if action['type'] == 'fill':
                        rendered.append(f"cy.get('{selector}').type('{action['value']}');")
                    elif action['type'] == 'click':
                        rendered.append(f"cy.get('{selector}').click();")

            elif isinstance(step, PageAssertion):
                for assertion in step.assertions:
                    if assertion['type'] == 'url_matches':
                        rendered.append(f"cy.url().should('include', '{assertion['pattern']}');")
                    elif assertion['type'] == 'visible':
                        selector = self._selector_to_cypress(assertion['selector'])
                        rendered.append(f"cy.get('{selector}').should('be.visible');")

        return rendered

    def _selector_to_cypress(self, selector: Dict[str, Any]) -> str:
        """Convert universal selector to Cypress selector"""
        if selector['type'] == 'test_id':
            return f"[data-cy=\"{selector['value']}\"]"
        elif selector['type'] == 'css':
            return selector['value']
        else:
            return selector['value']
```

**Cypress Template** (`templates/e2e_tests/cypress_test.cy.js.j2`):

```javascript
describe('{{ test_name | title }}', () => {
  {% for scenario in scenarios %}
  it('{{ scenario.name }}', () => {
    {% for step in scenario.steps %}
    {{ step }}
    {% endfor %}
  });

  {% endfor %}
});
```

**Success Criteria**:
- ✅ Cypress parser implemented
- ✅ Cypress generator implemented
- ✅ Parses cy.visit/get/type/click
- ✅ Extracts cy.url().should() assertions
- ✅ 8+ tests passing

---

### Day 5: CLI Integration & Cross-Browser Validation

**Objective**: CLI commands and browser compatibility

**Morning: E2E CLI Commands (2h)**

```python
# src/cli/e2e_test_commands.py

import click
from pathlib import Path

from src.reverse_engineering.e2e_tests.playwright_parser import PlaywrightParser
from src.reverse_engineering.e2e_tests.cypress_parser import CypressParser

from src.generators.e2e_tests.playwright_generator import PlaywrightGenerator
from src.generators.e2e_tests.cypress_generator import CypressGenerator

@click.group()
def e2e_tests():
    """E2E test specification commands"""
    pass

@e2e_tests.command()
@click.argument('test_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), required=True)
@click.option('--framework', type=click.Choice(['playwright', 'cypress']), required=True)
def reverse(test_file: str, output: str, framework: str):
    """
    Reverse engineer E2E tests to E2ETestSpec

    Examples:
        specql e2e-tests reverse signup.spec.ts -o specs/e2e/signup.yaml --framework playwright
        specql e2e-tests reverse checkout.cy.js -o specs/e2e/checkout.yaml --framework cypress
    """
    test_path = Path(test_file)
    output_path = Path(output)

    if framework == 'playwright':
        parser = PlaywrightParser()
    elif framework == 'cypress':
        parser = CypressParser()
    else:
        raise ValueError(f"Unsupported framework: {framework}")

    click.echo(f"Parsing {test_path} with {framework} parser...")
    spec = parser.parse_file(test_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(spec.to_yaml())

    click.echo(f"✅ Generated E2ETestSpec: {output_path}")
    click.echo(f"   Test: {spec.test_name}")
    click.echo(f"   Flow: {spec.flow_type.value}")
    click.echo(f"   Pages: {len(spec.pages)}")
    click.echo(f"   Scenarios: {len(spec.scenarios)}")

@e2e_tests.command()
@click.argument('spec_files', nargs=-1, type=click.Path(exists=True))
@click.option('--framework', type=click.Choice(['playwright', 'cypress']), required=True)
@click.option('--output-dir', '-o', type=click.Path(), required=True)
def generate(spec_files: tuple, framework: str, output_dir: str):
    """
    Generate E2E tests from E2ETestSpec

    Examples:
        specql e2e-tests generate specs/e2e/*.yaml --framework playwright -o tests/e2e/
        specql e2e-tests generate specs/e2e/*.yaml --framework cypress -o cypress/e2e/
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    template_dir = Path(__file__).parent.parent / "generators" / "e2e_tests" / "templates"

    if framework == 'playwright':
        generator = PlaywrightGenerator(template_dir)
        ext = ".spec.ts"
    elif framework == 'cypress':
        generator = CypressGenerator(template_dir)
        ext = ".cy.js"
    else:
        raise ValueError(f"Unsupported framework: {framework}")

    for spec_file in spec_files:
        spec_path = Path(spec_file)
        click.echo(f"Generating from {spec_path}...")

        from src.testing.e2e_spec.models import E2ETestSpec
        spec = E2ETestSpec.from_yaml(spec_path.read_text())

        output_file = output_path / f"{spec.test_name}{ext}"
        generator.generate(spec, output_file)

        click.echo(f"✅ Generated: {output_file}")

    click.echo(f"\n✅ Generated {len(spec_files)} E2E test files in {output_path}")
```

**Afternoon: Cross-Browser Validation (3h)**

```python
# src/testing/e2e_spec/browser_validator.py

from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum

class BrowserType(Enum):
    """Supported browsers"""
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"  # Safari
    EDGE = "edge"

@dataclass
class BrowserCompatibility:
    """Browser compatibility info"""
    browser: BrowserType
    supported: bool
    notes: str = ""
    known_issues: List[str] = None

class BrowserValidator:
    """
    Validate E2E tests across browsers

    Checks:
    - Selector compatibility
    - Feature support
    - Known browser issues
    """

    def validate_spec(self, spec: Any, browsers: List[BrowserType]) -> Dict[BrowserType, BrowserCompatibility]:
        """Validate spec compatibility across browsers"""
        results = {}

        for browser in browsers:
            results[browser] = self._validate_browser(spec, browser)

        return results

    def _validate_browser(self, spec: Any, browser: BrowserType) -> BrowserCompatibility:
        """Validate for specific browser"""
        issues = []

        # Check selector compatibility
        for page in spec.pages:
            for selector_name, selector in page.selectors.items():
                if not self._is_selector_compatible(selector, browser):
                    issues.append(f"Selector '{selector_name}' may not work in {browser.value}")

        # Check feature compatibility
        if browser == BrowserType.WEBKIT:
            # Safari has known issues with certain features
            if any('geolocation' in str(s) for s in spec.scenarios):
                issues.append("Geolocation requires user permission in Safari")

        supported = len(issues) == 0

        return BrowserCompatibility(
            browser=browser,
            supported=supported,
            notes=f"Validated {len(spec.scenarios)} scenarios",
            known_issues=issues
        )

    def _is_selector_compatible(self, selector: Dict[str, Any], browser: BrowserType) -> bool:
        """Check if selector is compatible with browser"""
        # Most selectors are cross-browser compatible
        # Special cases could be added here
        return True
```

**Success Criteria**:
- ✅ E2E CLI commands implemented
- ✅ Reverse engineering command working
- ✅ Generation command working
- ✅ Browser compatibility validator
- ✅ 5+ integration tests passing

---

## 📊 Week 56 Summary

### Deliverables

| Component | Status | Tests | Lines of Code |
|-----------|--------|-------|---------------|
| E2ETestSpec AST | ✅ Complete | 10+ | ~1,200 |
| Page Object Extractor | ✅ Complete | 8+ | ~600 |
| Playwright Parser | ✅ Complete | 10+ | ~800 |
| Playwright Generator | ✅ Complete | 8+ | ~600 |
| Cypress Parser | ✅ Complete | 8+ | ~600 |
| Cypress Generator | ✅ Complete | 6+ | ~400 |
| E2E CLI Integration | ✅ Complete | 5+ | ~300 |
| Browser Validator | ✅ Complete | 4+ | ~300 |
| **Total** | **✅ 100%** | **59+** | **~4,800** |

### Platform Coverage Matrix

| Framework | Parser | Generator | Features | Status |
|-----------|--------|-----------|----------|--------|
| Playwright | ✅ | ✅ | Navigation, actions, assertions, network mocks | ✅ Complete |
| Cypress | ✅ | ✅ | Visit, get, type, click, URL assertions | ✅ Complete |
| Selenium | ⚠️ | ⚠️ | Basic support | Future |

### Cross-Browser Support

| Browser | Playwright | Cypress | Status |
|---------|------------|---------|--------|
| Chromium | ✅ | ✅ | Full support |
| Firefox | ✅ | ✅ | Full support |
| WebKit (Safari) | ✅ | ⚠️ | Playwright only |
| Edge | ✅ | ✅ | Full support |

### Key Features

1. **Universal E2ETestSpec AST**
   - Multi-page flows and navigation
   - Page object model definitions
   - Network request/response mocking
   - Browser context management

2. **Bi-Directional Transformation**
   - Parse: Playwright/Cypress → E2ETestSpec
   - Generate: E2ETestSpec → Playwright/Cypress
   - Enables framework migration

3. **Page Object Extraction**
   - Automatic page object model generation
   - TypeScript class generation
   - Reusable selectors and actions

4. **Network Mocking**
   - API response mocking
   - Request matching
   - Response delays

### Example Usage

```bash
# Reverse engineer Playwright tests
specql e2e-tests reverse tests/e2e/signup.spec.ts \
  --output specs/e2e/signup.yaml \
  --framework playwright

# Generate Cypress tests from spec
specql e2e-tests generate specs/e2e/signup.yaml \
  --framework cypress \
  --output-dir cypress/e2e/

# Validate cross-browser compatibility
specql e2e-tests validate specs/e2e/signup.yaml \
  --browsers chromium,firefox,webkit
```

### Next Steps (Week 57)

- Visual regression testing
- Accessibility testing (WCAG validation)
- Mobile-specific testing (gestures, orientations)
- Performance testing integration

---

**Week 56 Status**: ✅ **COMPLETE** - Universal E2E test specification implemented with Playwright and Cypress support, page object extraction, and cross-browser validation.
