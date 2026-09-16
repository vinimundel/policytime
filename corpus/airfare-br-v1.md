---
id: airfare-br-v1
title: Airfare · BR · H1 2026
version: v1
published_on: '2025-12-15'
topic: airfare
clauses:
- id: airfare-br-v1.main
  document_id: airfare-br-v1
  rule_key: airfare.main
  topic: airfare
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
    kind: requirement
    value: Economy class only
  relationships: []
- id: airfare-br-v1.documentation
  document_id: airfare-br-v1
  rule_key: airfare.documentation
  topic: airfare
  period: *id001
  scope: *id002
  value:
    kind: requirement
    value: Airfare reimbursement requires the airline invoice and boarding confirmation.
      Personal upgrades are excluded.
  relationships: []
---

# Airfare · BR · H1 2026

Synthetic Northstar Works policy. For demonstration only; this is not a real employer's policy.

## airfare-br-v1.main

Airfare eligibility: economy class only.

## airfare-br-v1.documentation

Airfare reimbursement requires the airline invoice and boarding confirmation. Personal upgrades are excluded.
