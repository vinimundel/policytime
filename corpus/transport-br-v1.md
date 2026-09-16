---
id: transport-br-v1
title: Ground transport · BR · H1 2026
version: v1
published_on: '2025-12-15'
topic: transport
clauses:
- id: transport-br-v1.main
  document_id: transport-br-v1
  rule_key: transport.main
  topic: transport
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
    amount: 120
    currency: BRL
    unit: per_trip
  relationships: []
- id: transport-br-v1.documentation
  document_id: transport-br-v1
  rule_key: transport.documentation
  topic: transport
  period: *id001
  scope: *id002
  value:
    kind: requirement
    value: Ground transport requires a dated taxi or rideshare receipt and the business
      route. Personal detours are excluded.
  relationships: []
---

# Ground transport · BR · H1 2026

Synthetic Northstar Works policy. For demonstration only; this is not a real employer's policy.

## transport-br-v1.main

Ground transport reimbursement is limited to BRL 120 per trip.

## transport-br-v1.documentation

Ground transport requires a dated taxi or rideshare receipt and the business route. Personal detours are excluded.
