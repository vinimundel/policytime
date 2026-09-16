---
id: airfare-br-v2
title: Airfare · BR · H2 2026
version: v2
published_on: '2026-06-15'
topic: airfare
clauses:
- id: airfare-br-v2.main
  document_id: airfare-br-v2
  rule_key: airfare.main
  topic: airfare
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
    value: Economy or premium economy with approval
  relationships:
  - kind: supersedes
    target_id: airfare-br-v1.main
- id: airfare-br-v2.documentation
  document_id: airfare-br-v2
  rule_key: airfare.documentation
  topic: airfare
  period: *id001
  scope: *id002
  value:
    kind: requirement
    value: Airfare reimbursement requires the airline invoice and boarding confirmation.
      Personal upgrades are excluded.
  relationships:
  - kind: supersedes
    target_id: airfare-br-v1.documentation
---

# Airfare · BR · H2 2026

Synthetic Northstar Works policy. For demonstration only; this is not a real employer's policy.

## airfare-br-v2.main

Airfare eligibility: economy or premium economy with approval.

## airfare-br-v2.documentation

Airfare reimbursement requires the airline invoice and boarding confirmation. Personal upgrades are excluded.
