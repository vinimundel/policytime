---
id: meals-us-v1
title: Meals · US · H1 2026
version: v1
published_on: '2025-12-15'
topic: meals
clauses:
- id: meals-us-v1.main
  document_id: meals-us-v1
  rule_key: meals.main
  topic: meals
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
    amount: 50
    currency: USD
    unit: per_day
  relationships: []
- id: meals-us-v1.documentation
  document_id: meals-us-v1
  rule_key: meals.documentation
  topic: meals
  period: *id001
  scope: *id002
  value:
    kind: requirement
    value: Meals require an itemized receipt with the business purpose. Alcohol and
      meals already provided by the host are excluded.
  relationships: []
---

# Meals · US · H1 2026

Synthetic Northstar Works policy. For demonstration only; this is not a real employer's policy.

## meals-us-v1.main

Meals reimbursement is limited to USD 50 per day.

## meals-us-v1.documentation

Meals require an itemized receipt with the business purpose. Alcohol and meals already provided by the host are excluded.
