---
id: approvals-br-v2
title: Travel approvals · BR · H2 2026
version: v2
published_on: '2026-06-15'
topic: approvals
clauses:
- id: approvals-br-v2.main
  document_id: approvals-br-v2
  rule_key: approvals.main
  topic: approvals
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
    kind: requirement
    value: Written manager and finance approval
  relationships:
  - kind: supersedes
    target_id: approvals-br-v1.main
- id: approvals-br-v2.documentation
  document_id: approvals-br-v2
  rule_key: approvals.documentation
  topic: approvals
  period: *id001
  scope: *id002
  value:
    kind: requirement
    value: Travel approval must be recorded before booking. A policy limit alone does
      not constitute approval for a purchase.
  relationships:
  - kind: supersedes
    target_id: approvals-br-v1.documentation
---

# Travel approvals · BR · H2 2026

Synthetic Northstar Works policy. For demonstration only; this is not a real employer's policy.

## approvals-br-v2.main

Travel requires written manager and finance approval before booking.

## approvals-br-v2.documentation

Travel approval must be recorded before booking. A policy limit alone does not constitute approval for a purchase.
