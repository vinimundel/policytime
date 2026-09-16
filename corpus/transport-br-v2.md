---
id: transport-br-v2
title: Ground transport · BR · H2 2026
version: v2
published_on: '2026-06-15'
topic: transport
clauses:
- id: transport-br-v2.main
  document_id: transport-br-v2
  rule_key: transport.main
  topic: transport
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
    amount: 150
    currency: BRL
    unit: per_trip
  relationships:
  - kind: supersedes
    target_id: transport-br-v1.main
- id: transport-br-v2.documentation
  document_id: transport-br-v2
  rule_key: transport.documentation
  topic: transport
  period: *id001
  scope: *id002
  value:
    kind: requirement
    value: Ground transport requires a dated taxi or rideshare receipt and the business
      route. Personal detours are excluded.
  relationships:
  - kind: supersedes
    target_id: transport-br-v1.documentation
---

# Ground transport · BR · H2 2026

Synthetic Northstar Works policy. For demonstration only; this is not a real employer's policy.

## transport-br-v2.main

Ground transport reimbursement is limited to BRL 150 per trip.

## transport-br-v2.documentation

Ground transport requires a dated taxi or rideshare receipt and the business route. Personal detours are excluded.
