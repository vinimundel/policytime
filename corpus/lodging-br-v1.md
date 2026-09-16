---
id: lodging-br-v1
title: Hotel and lodging · BR · H1 2026
version: v1
published_on: '2025-12-15'
topic: lodging
clauses:
- id: lodging-br-v1.main
  document_id: lodging-br-v1
  rule_key: lodging.main
  topic: lodging
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
    amount: 180
    currency: BRL
    unit: per_night
  relationships: []
- id: lodging-br-v1.documentation
  document_id: lodging-br-v1
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

# Hotel and lodging · BR · H1 2026

Synthetic Northstar Works policy. For demonstration only; this is not a real employer's policy.

## lodging-br-v1.main

Hotel and lodging reimbursement is limited to BRL 180 per night.

## lodging-br-v1.documentation

Hotel reimbursement covers the room charge and mandatory taxes. An itemized hotel receipt is required; minibar and personal entertainment are excluded.
