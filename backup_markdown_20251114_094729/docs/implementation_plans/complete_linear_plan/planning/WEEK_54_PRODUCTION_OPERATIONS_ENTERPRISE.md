# Week 54: Production Operations & Enterprise Features

**Date**: 2025-11-13
**Duration**: 5 days
**Status**: ✅ Completed
**Objective**: Production-ready operations, monitoring, enterprise security, and deployment automation

---

## 🎯 Overview

Make SpecQL enterprise-ready with CI/CD, monitoring, security, compliance, and operational excellence.

```
┌────────────────────────────────────────────────────────┐
│         PRODUCTION OPERATIONS                           │
├──────────────┬──────────────┬──────────────────────────┤
│   CI/CD      │  Monitoring  │   Enterprise             │
│   Pipeline   │  & Observ.   │   Features               │
│              │              │                          │
│ • GitHub     │ • Error      │ • SSO/SAML               │
│   Actions    │   tracking   │ • Audit logs             │
│ • Testing    │ • Analytics  │ • Multi-tenancy          │
│ • Deploy     │ • A/B test   │ • White-labeling         │
└──────────────┴──────────────┴──────────────────────────┘
```

---

## Day 1: CI/CD Pipeline Templates

### GitHub Actions Workflow

**File**: `.github/workflows/specql-frontend.yml`

```yaml
name: SpecQL Frontend CI/CD

on:
  push:
    branches: [main, develop]
    paths:
      - 'frontend/**'
      - '.github/workflows/specql-frontend.yml'
  pull_request:
    branches: [main]

jobs:
  validate:
    name: Validate SpecQL
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install SpecQL CLI
        run: pip install specql-cli

      - name: Validate specifications
        run: specql frontend validate frontend/**/*.specql.yaml

      - name: Check breaking changes
        run: specql frontend diff --compare origin/main

  generate:
    name: Generate & Test
    needs: validate
    runs-on: ubuntu-latest
    strategy:
      matrix:
        framework: [react, vue, flutter]

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        if: matrix.framework != 'flutter'
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Setup Flutter
        if: matrix.framework == 'flutter'
        uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.13.0'

      - name: Generate code
        run: |
          specql generate ${{ matrix.framework }} \
            frontend/specs/*.yaml \
            --output generated/${{ matrix.framework }}

      - name: Install dependencies
        working-directory: generated/${{ matrix.framework }}
        run: |
          if [ "${{ matrix.framework }}" == "flutter" ]; then
            flutter pub get
          else
            npm install
          fi

      - name: Run tests
        working-directory: generated/${{ matrix.framework }}
        run: |
          if [ "${{ matrix.framework }}" == "flutter" ]; then
            flutter test
          else
            npm test
          fi

      - name: Build
        working-directory: generated/${{ matrix.framework }}
        run: |
          if [ "${{ matrix.framework }}" == "flutter" ]; then
            flutter build apk --debug
          else
            npm run build
          fi

      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: ${{ matrix.framework }}-build
          path: generated/${{ matrix.framework }}/build

  deploy:
    name: Deploy
    needs: generate
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v3

      - name: Download artifacts
        uses: actions/download-artifact@v3

      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID }}
          vercel-project-id: ${{ secrets.PROJECT_ID }}
          working-directory: ./react-build

  notify:
    name: Notify
    needs: [validate, generate, deploy]
    runs-on: ubuntu-latest
    if: always()

    steps:
      - name: Slack Notification
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'SpecQL Frontend deployment ${{ job.status }}'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### GitLab CI Pipeline

**File**: `.gitlab-ci.yml`

```yaml
stages:
  - validate
  - generate
  - test
  - build
  - deploy

variables:
  SPECQL_VERSION: "1.0.0"

validate_specs:
  stage: validate
  image: python:3.11
  script:
    - pip install specql-cli==$SPECQL_VERSION
    - specql frontend validate frontend/**/*.specql.yaml
  only:
    - merge_requests
    - main

generate_react:
  stage: generate
  image: node:18
  script:
    - specql generate react frontend/specs/*.yaml --output dist/react
  artifacts:
    paths:
      - dist/react/
    expire_in: 1 day

generate_flutter:
  stage: generate
  image: cirrusci/flutter:stable
  script:
    - specql generate flutter frontend/specs/*.yaml --output dist/flutter
  artifacts:
    paths:
      - dist/flutter/
    expire_in: 1 day

test_react:
  stage: test
  image: node:18
  dependencies:
    - generate_react
  script:
    - cd dist/react
    - npm install
    - npm test -- --coverage
  coverage: '/Statements\s*:\s*(\d+\.?\d*)%/'

build_production:
  stage: build
  image: node:18
  dependencies:
    - generate_react
  script:
    - cd dist/react
    - npm install
    - npm run build
  artifacts:
    paths:
      - dist/react/build/
  only:
    - main

deploy_production:
  stage: deploy
  image: alpine:latest
  dependencies:
    - build_production
  script:
    - apk add --no-cache rsync openssh
    - rsync -avz dist/react/build/ $DEPLOY_USER@$DEPLOY_HOST:/var/www/app/
  environment:
    name: production
    url: https://app.example.com
  only:
    - main
```

---

## Day 2: Monitoring & Observability

### Error Tracking Integration

**SpecQL Configuration**:

```yaml
frontend:
  monitoring:
    # Error tracking
    error_tracking:
      provider: sentry
      dsn: ${SENTRY_DSN}
      environment: production
      sample_rate: 1.0
      traces_sample_rate: 0.1

      # Auto-capture
      capture_console: true
      capture_unhandled_rejections: true

      # Context
      include_user_context: true
      include_component_hierarchy: true

    # Analytics
    analytics:
      provider: mixpanel  # or google_analytics, amplitude
      token: ${MIXPANEL_TOKEN}

      # Track events
      auto_track:
        - page_views
        - button_clicks
        - form_submissions
        - errors

      # Custom events from SpecQL actions
      track_actions: true
```

### Auto-Generated Monitoring

**File**: `templates/react/monitoring.tsx.j2`

```tsx
import * as Sentry from '@sentry/react';
import { BrowserTracing } from '@sentry/tracing';
import mixpanel from 'mixpanel-browser';

// Auto-initialize Sentry
Sentry.init({
  dsn: process.env.REACT_APP_SENTRY_DSN,
  environment: process.env.NODE_ENV,
  integrations: [
    new BrowserTracing(),
    new Sentry.Replay({
      maskAllText: false,
      blockAllMedia: false,
    }),
  ],
  tracesSampleRate: 0.1,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
});

// Auto-initialize Mixpanel
mixpanel.init(process.env.REACT_APP_MIXPANEL_TOKEN || '');

// Track page views
export function trackPageView(pageName: string) {
  mixpanel.track('Page View', {
    page: pageName,
    timestamp: new Date().toISOString()
  });

  Sentry.addBreadcrumb({
    category: 'navigation',
    message: `Navigated to ${pageName}`,
    level: 'info',
  });
}

// Track user actions
export function trackAction(action: string, data?: any) {
  mixpanel.track(action, {
    ...data,
    timestamp: new Date().toISOString()
  });

  Sentry.addBreadcrumb({
    category: 'user_action',
    message: action,
    data,
    level: 'info',
  });
}

// Error boundary
export class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean }
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    Sentry.captureException(error, {
      contexts: {
        react: {
          componentStack: errorInfo.componentStack,
        },
      },
    });

    mixpanel.track('Error', {
      error: error.message,
      stack: error.stack,
    });
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback />;
    }

    return this.props.children;
  }
}

// Performance monitoring
export function trackPerformance(metric: string, value: number) {
  Sentry.captureMessage(`Performance: ${metric}`, {
    level: 'info',
    extra: {
      metric,
      value,
      unit: 'ms',
    },
  });

  if (value > 1000) {  // Slow operation
    mixpanel.track('Performance Issue', {
      metric,
      value,
      threshold: 1000,
    });
  }
}
```

### A/B Testing Framework

```yaml
frontend:
  ab_testing:
    provider: optimizely  # or google_optimize, launchdarkly

    experiments:
      - id: button_color_test
        name: "Primary Button Color Test"
        variants:
          - id: control
            name: "Blue Button"
            config:
              button_color: "#3B82F6"

          - id: variant_a
            name: "Green Button"
            config:
              button_color: "#10B981"

        traffic_allocation: 50  # 50/50 split

      - id: checkout_flow_test
        name: "Checkout Flow Test"
        variants:
          - id: single_page
            name: "Single Page Checkout"
          - id: multi_step
            name: "Multi-Step Checkout"
```

---

## Day 3: Enterprise Authentication & Authorization

### SSO/SAML Integration

```yaml
frontend:
  authentication:
    # Auth provider
    provider: auth0  # or okta, azure_ad, custom

    # SSO configuration
    sso:
      enabled: true
      protocols: [saml, oidc]
      auto_redirect: true

      providers:
        - id: okta
          name: "Okta SSO"
          type: saml
          metadata_url: ${OKTA_METADATA_URL}

        - id: azure_ad
          name: "Azure AD"
          type: oidc
          client_id: ${AZURE_CLIENT_ID}
          tenant_id: ${AZURE_TENANT_ID}

    # Session management
    session:
      timeout: 3600  # 1 hour
      refresh_before_expiry: 300  # 5 minutes
      persist: true

    # MFA
    mfa:
      enabled: true
      required_for_roles: [admin, finance]
      methods: [totp, sms, email]
```

### Auto-Generated Auth Components

```tsx
// Auto-generated Auth0 integration
import { Auth0Provider, useAuth0 } from '@auth0/auth0-react';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  return (
    <Auth0Provider
      domain={process.env.REACT_APP_AUTH0_DOMAIN!}
      clientId={process.env.REACT_APP_AUTH0_CLIENT_ID!}
      authorizationParams={{
        redirect_uri: window.location.origin,
        audience: process.env.REACT_APP_AUTH0_AUDIENCE,
        scope: 'openid profile email',
      }}
    >
      {children}
    </Auth0Provider>
  );
}

// Protected route wrapper
export function ProtectedRoute({
  children,
  requiredRoles = [],
}: {
  children: React.ReactNode;
  requiredRoles?: string[];
}) {
  const { isAuthenticated, isLoading, user, loginWithRedirect } = useAuth0();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    loginWithRedirect();
    return null;
  }

  // Check roles
  if (requiredRoles.length > 0) {
    const userRoles = user?.['https://app.com/roles'] || [];
    const hasRequiredRole = requiredRoles.some(role => userRoles.includes(role));

    if (!hasRequiredRole) {
      return <UnauthorizedPage />;
    }
  }

  return <>{children}</>;
}
```

### Role-Based Access Control (RBAC)

```yaml
frontend:
  authorization:
    type: rbac

    roles:
      - id: admin
        name: "Administrator"
        permissions: ["*"]  # All permissions

      - id: editor
        name: "Editor"
        permissions:
          - users.read
          - users.create
          - users.update
          - posts.read
          - posts.create
          - posts.update
          - posts.delete

      - id: viewer
        name: "Viewer"
        permissions:
          - users.read
          - posts.read

  # Apply to pages
  pages:
    - name: UserManagement
      route: /users
      required_permissions: [users.read]

    - name: UserCreate
      route: /users/new
      required_permissions: [users.create]

  # Apply to actions
  actions:
    - name: delete_user
      required_permissions: [users.delete]
      required_roles: [admin]
```

---

## Day 4: Multi-Tenancy & White-Labeling

### Multi-Tenant Architecture

```yaml
frontend:
  multi_tenancy:
    enabled: true
    strategy: subdomain  # subdomain, path, or header

    # Tenant detection
    detection:
      subdomain: true  # tenant.app.com
      path: false      # app.com/tenant
      header: false    # X-Tenant-ID header

    # Tenant configuration
    tenants:
      - id: acme
        name: "Acme Corp"
        subdomain: acme
        theme: acme_theme
        features: [analytics, exports, api_access]

      - id: globex
        name: "Globex Corporation"
        subdomain: globex
        theme: globex_theme
        features: [analytics]

    # Tenant isolation
    isolation:
      data: strict       # Strict data isolation
      components: shared # Shared components
      assets: separate   # Separate assets per tenant
```

### White-Labeling System

```yaml
frontend:
  white_labeling:
    enabled: true

    customization:
      # Branding
      branding:
        logo: {customizable: true, max_size: "500KB"}
        favicon: {customizable: true}
        app_name: {customizable: true}

      # Theme
      theme:
        colors: {customizable: true}
        fonts: {customizable: true}
        spacing: {customizable: false}

      # Content
      content:
        welcome_message: {customizable: true}
        help_url: {customizable: true}
        support_email: {customizable: true}

      # Features
      features:
        analytics: {optional: true}
        exports: {optional: true}
        api_access: {optional: true, requires_plan: "enterprise"}

    # Per-tenant overrides
    tenant_overrides:
      acme:
        branding:
          logo: "https://cdn.acme.com/logo.png"
          app_name: "Acme Portal"
        theme:
          colors:
            primary: "#E31B23"
            secondary: "#000000"
```

---

## Day 5: Compliance & Security

### Audit Logging

```yaml
frontend:
  audit_logging:
    enabled: true
    provider: cloudwatch  # or elasticsearch, datadog

    # What to log
    events:
      - user_login
      - user_logout
      - data_access
      - data_modification
      - permission_change
      - export_data
      - api_call

    # Log format
    format: json
    include:
      - user_id
      - tenant_id
      - timestamp
      - action
      - resource
      - ip_address
      - user_agent
      - result  # success or failure

    # Retention
    retention_days: 90  # Keep logs for 90 days
    archive: true       # Archive to S3 after 90 days
```

### Auto-Generated Audit Trail

```typescript
// Audit logger middleware
export function auditMiddleware(action: string, resource: string) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const startTime = Date.now();

    // Log the attempt
    const auditLog = {
      user_id: req.user?.id,
      tenant_id: req.tenant?.id,
      action,
      resource,
      timestamp: new Date().toISOString(),
      ip_address: req.ip,
      user_agent: req.headers['user-agent'],
    };

    try {
      await next();

      // Log success
      await logAuditEvent({
        ...auditLog,
        result: 'success',
        duration_ms: Date.now() - startTime,
      });
    } catch (error) {
      // Log failure
      await logAuditEvent({
        ...auditLog,
        result: 'failure',
        error: error.message,
        duration_ms: Date.now() - startTime,
      });

      throw error;
    }
  };
}
```

### GDPR Compliance Features

```yaml
frontend:
  compliance:
    gdpr:
      enabled: true

      features:
        # Cookie consent
        cookie_consent:
          enabled: true
          categories: [essential, functional, analytics, marketing]
          require_explicit_consent: true

        # Data export
        data_export:
          enabled: true
          formats: [json, csv]
          include_all_user_data: true

        # Right to be forgotten
        data_deletion:
          enabled: true
          delete_immediately: false
          retention_period_days: 30  # Grace period

        # Privacy policy
        privacy_policy:
          url: "https://example.com/privacy"
          version: "1.0"
          require_acceptance: true

      # Tracking consent
      analytics_consent_required: true
      third_party_scripts_consent: true
```

---

## Week 54 Deliverables Summary

### CI/CD

- [x] GitHub Actions workflow
- [x] GitLab CI pipeline
- [x] Multi-framework builds
- [x] Automated testing
- [x] Deployment automation
- [x] Slack/Discord notifications

### Monitoring

- [x] Sentry integration
- [x] Mixpanel/Analytics integration
- [x] Performance monitoring
- [x] Error tracking
- [x] A/B testing framework
- [x] Session replay

### Enterprise Auth

- [x] SSO/SAML support
- [x] OAuth2/OIDC
- [x] Multi-factor authentication
- [x] Role-based access control (RBAC)
- [x] Permission system
- [x] Session management

### Multi-Tenancy

- [x] Subdomain/path routing
- [x] Tenant isolation
- [x] Per-tenant theming
- [x] Feature flags per tenant
- [x] White-labeling system
- [x] Tenant admin dashboard

### Compliance

- [x] Audit logging
- [x] GDPR compliance features
- [x] Cookie consent
- [x] Data export (GDPR)
- [x] Right to be forgotten
- [x] SOC 2 compliance helpers

**Status**: ✅ Week 54 Complete - Enterprise-ready production system
