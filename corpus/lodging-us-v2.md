---
id: lodging-us-v2
title: Hotel and lodging · US · H2 2026
version: v2
published_on: '2026-06-15'
topic: lodging
clauses:
- id: lodging-us-v2.main
  document_id: lodging-us-v2
  rule_key: lodging.main
  topic: lodging
  period: &id001
    start: '2026-07-01'
    end: null
  scope: &id002
    countries:
    - US
    employment_types:
    - employee
    - contractor
  value:
    kind: money
    amount: 180
    currency: USD
    unit: per_night
  relationships:
  - kind: supersedes
    target_id: lodging-us-v1.main
- id: lodging-us-v2.documentation
  document_id: lodging-us-v2
  rule_key: lodging.documentation
  topic: lodging
  period: *id001
  scope: *id002
  value:
    kind: requirement
    value: Hotel reimbursement covers the room charge and mandatory taxes. An itemized
      hotel receipt is required; minibar and personal entertainment are excluded.
  relationships:
  - kind: supersedes
    target_id: lodging-us-v1.documentation
- id: lodging-us-v2.contractor
  document_id: lodging-us-v2
  rule_key: lodging.main
  topic: lodging
  period: *id001
  scope:
    countries:
    - US
    employment_types:
    - contractor
  value:
    kind: money
    amount: 160
    currency: USD
    unit: per_night
  relationships:
  - kind: overrides
    target_id: lodging-us-v2.main
---

# Hotel and lodging · US · H2 2026

Synthetic Northstar Works policy. For demonstration only; this is not a real employer's policy.

## lodging-us-v2.main

Hotel and lodging reimbursement is limited to USD 180 per night.

## lodging-us-v2.documentation

Hotel reimbursement covers the room charge and mandatory taxes. An itemized hotel receipt is required; minibar and personal entertainment are excluded.

## lodging-us-v2.contractor

For contractors, lodging reimbursement is limited to USD 160 per night. This exception replaces the general limit only; documentation requirements still apply.
