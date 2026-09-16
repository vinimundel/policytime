---
id: meals-br-v2
title: Meals · BR · H2 2026
version: v2
published_on: '2026-06-15'
topic: meals
clauses:
- id: meals-br-v2.main
  document_id: meals-br-v2
  rule_key: meals.main
  topic: meals
  period: &id001
    start: '2026-07-01'
    end: null
  scope: &id002
    countries:
    - BR
    employment_types:
    - employee
    - contractor
  value:
    kind: money
    amount: 100
    currency: BRL
    unit: per_day
  relationships:
  - kind: supersedes
    target_id: meals-br-v1.main
- id: meals-br-v2.documentation
  document_id: meals-br-v2
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
    target_id: meals-br-v1.documentation
- id: meals-br-v2.contractor
  document_id: meals-br-v2
  rule_key: meals.main
  topic: meals
  period: *id001
  scope:
    countries:
    - BR
    employment_types:
    - contractor
  value:
    kind: money
    amount: 60
    currency: BRL
    unit: per_day
  relationships:
  - kind: overrides
    target_id: meals-br-v2.main
---

# Meals · BR · H2 2026

Synthetic Northstar Works policy. For demonstration only; this is not a real employer's policy.

## meals-br-v2.main

Meals reimbursement is limited to BRL 100 per day.

## meals-br-v2.documentation

Meals require an itemized receipt with the business purpose. Alcohol and meals already provided by the host are excluded.

## meals-br-v2.contractor

For contractors, meals reimbursement is limited to BRL 60 per day. This exception replaces the general limit only; documentation requirements still apply.
