---
id: meals-us-v2
title: Meals · US · H2 2026
version: v2
published_on: '2026-06-15'
topic: meals
clauses:
- id: meals-us-v2.main
  document_id: meals-us-v2
  rule_key: meals.main
  topic: meals
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
    amount: 65
    currency: USD
    unit: per_day
  relationships:
  - kind: supersedes
    target_id: meals-us-v1.main
- id: meals-us-v2.documentation
  document_id: meals-us-v2
  rule_key: meals.documentation
  topic: meals
  period: *id001
  scope: *id002
  value:
    kind: requirement
    value: Meals require an itemized receipt with the business purpose. Alcohol and
      meals already provided by the host are excluded.
  relationships:
  - kind: supersedes
    target_id: meals-us-v1.documentation
- id: meals-us-v2.contractor
  document_id: meals-us-v2
  rule_key: meals.main
  topic: meals
  period: *id001
  scope:
    countries:
    - US
    employment_types:
    - contractor
  value:
    kind: money
    amount: 45
    currency: USD
    unit: per_day
  relationships:
  - kind: overrides
    target_id: meals-us-v2.main
- id: meals-us-v2.unresolved-bulletin
  document_id: meals-us-v2
  rule_key: meals.main
  topic: meals
  period:
    start: '2026-09-01'
    end: null
  scope:
    countries:
    - US
    employment_types:
    - employee
  value:
    kind: money
    amount: 90
    currency: USD
    unit: per_day
  relationships: []
---

# Meals · US · H2 2026

Synthetic Northstar Works policy. For demonstration only; this is not a real employer's policy.

## meals-us-v2.main

Meals reimbursement is limited to USD 65 per day.

## meals-us-v2.documentation

Meals require an itemized receipt with the business purpose. Alcohol and meals already provided by the host are excluded.

## meals-us-v2.contractor

For contractors, meals reimbursement is limited to USD 45 per day. This exception replaces the general limit only; documentation requirements still apply.

## meals-us-v2.unresolved-bulletin

A September operations bulletin lists the employee meals limit as USD 90 per day. It provides no authority to replace the existing meals limit. The policy owner has not resolved the discrepancy.
