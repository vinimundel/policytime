---
id: lodging-br-v2
title: Hotel and lodging · BR · H2 2026
version: v2
published_on: '2026-06-15'
topic: lodging
clauses:
- id: lodging-br-v2.main
  document_id: lodging-br-v2
  rule_key: lodging.main
  topic: lodging
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
    amount: 220
    currency: BRL
    unit: per_night
  relationships:
  - kind: supersedes
    target_id: lodging-br-v1.main
- id: lodging-br-v2.documentation
  document_id: lodging-br-v2
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
    target_id: lodging-br-v1.documentation
- id: lodging-br-v2.contractor
  document_id: lodging-br-v2
  rule_key: lodging.main
  topic: lodging
  period: *id001
  scope:
    countries:
    - BR
    employment_types:
    - contractor
  value:
    kind: money
    amount: 180
    currency: BRL
    unit: per_night
  relationships:
  - kind: overrides
    target_id: lodging-br-v2.main
---

# Hotel and lodging · BR · H2 2026

Synthetic Northstar Works policy. For demonstration only; this is not a real employer's policy.

## lodging-br-v2.main

Hotel and lodging reimbursement is limited to BRL 220 per night.

## lodging-br-v2.documentation

Hotel reimbursement covers the room charge and mandatory taxes. An itemized hotel receipt is required; minibar and personal entertainment are excluded.

## lodging-br-v2.contractor

For contractors, lodging reimbursement is limited to BRL 180 per night. This exception replaces the general limit only; documentation requirements still apply.
