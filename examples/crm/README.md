# CRM Example

**Customer relationship management built with SpecQL** 👥

Contacts, organizations, and opportunities.

## Overview

Simple CRM with:
- **Contacts** with rich contact information
- **Organizations** (companies)
- **Opportunities** (sales leads)

## Entities

### Contact (`contact.yaml`)

```yaml
entity: Contact
schema: crm
description: "CRM contact"

fields:
  email: email!
  first_name: text!
  last_name: text!
  phone: phone
  organization: ref(Organization)

actions:
  - name: create_contact
  - name: update_contact
```

### Organization (`organization.yaml`)

```yaml
entity: Organization
schema: crm
description: "CRM organization/company"

fields:
  name: text!
  domain: domainName
  website: url
  industry: text

actions:
  - name: create_organization
  - name: update_organization
```

### Opportunity (`opportunity.yaml`)

```yaml
entity: Opportunity
schema: crm
description: "Sales opportunity"

fields:
  title: text!
  amount: money
  stage: enum(prospect, qualified, proposal, negotiation, closed_won, closed_lost)
  contact: ref(Contact)
  organization: ref(Organization)

actions:
  - name: create_opportunity
  - name: update_stage
```

## Quick Start

```bash
cd examples/crm
specql generate entities/*.yaml
createdb crm_example
cd db/schema
confiture migrate up
```

## File Structure

```
examples/crm/
├── README.md
└── entities/
    ├── contact.yaml
    ├── organization.yaml
    └── opportunity.yaml
```