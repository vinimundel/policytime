---
id: approvals-us-v1
title: Travel approvals · US · H1 2026
version: v1
published_on: '2025-12-15'
topic: approvals
clauses:
- id: approvals-us-v1.main
  document_id: approvals-us-v1
  rule_key: approvals.main
  topic: approvals
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
    kind: requirement
    value: Written manager approval
  relationships: []
- id: approvals-us-v1.documentation
  document_id: approvals-us-v1
  rule_key: approvals.documentation
  topic: approvals
  period: *id001
  scope: *id002
  value:
    kind: requirement
    value: Travel approval must be recorded before booking. A policy limit alone does
      not constitute approval for a purchase.
  relationships: []
---

# Travel approvals · US · H1 2026

Synthetic Northstar Works policy. For demonstration only; this is not a real employer's policy.

## approvals-us-v1.main

Travel requires written manager approval before booking.

## approvals-us-v1.documentation

Travel approval must be recorded before booking. A policy limit alone does not constitute approval for a purchase.
