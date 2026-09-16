---
id: lodging-us-v1
title: Hotel and lodging · US · H1 2026
version: v1
published_on: '2025-12-15'
topic: lodging
clauses:
- id: lodging-us-v1.main
  document_id: lodging-us-v1
  rule_key: lodging.main
  topic: lodging
  period: &id001
    start: '2026-01-01'
    end: '2026-07-01'
  scope: &id002
    countries:
    - US
    employment_types:
    - employee
    - contractor
  value:
    kind: money
    amount: 140
    currency: USD
    unit: per_night
  relationships: []
- id: lodging-us-v1.documentation
  document_id: lodging-us-v1
  rule_key: lodging.documentation
  topic: lodging
  period: *id001
  scope: *id002
  value:
    kind: requirement
    value: Hotel reimbursement covers the room charge and mandatory taxes. An itemized
      hotel receipt is required; minibar and personal entertainment are excluded.
  relationships: []
---

# Hotel and lodging · US · H1 2026

Synthetic Northstar Works policy. For demonstration only; this is not a real employer's policy.

## lodging-us-v1.main

Hotel and lodging reimbursement is limited to USD 140 per night.

## lodging-us-v1.documentation

Hotel reimbursement covers the room charge and mandatory taxes. An itemized hotel receipt is required; minibar and personal entertainment are excluded.
