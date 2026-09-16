---
id: meals-br-v1
title: Meals · BR · H1 2026
version: v1
published_on: '2025-12-15'
topic: meals
clauses:
- id: meals-br-v1.main
  document_id: meals-br-v1
  rule_key: meals.main
  topic: meals
  period: &id001
    start: '2026-01-01'
    end: '2026-07-01'
  scope: &id002
    countries:
    - BR
    employment_types:
    - employee
    - contractor
  value:
    kind: money
    amount: 80
    currency: BRL
    unit: per_day
  relationships: []
- id: meals-br-v1.documentation
  document_id: meals-br-v1
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

# Meals · BR · H1 2026

Synthetic Northstar Works policy. For demonstration only; this is not a real employer's policy.

## meals-br-v1.main

Meals reimbursement is limited to BRL 80 per day.

## meals-br-v1.documentation

Meals require an itemized receipt with the business purpose. Alcohol and meals already provided by the host are excluded.
