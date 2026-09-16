---
id: submission-br-v1
title: Expense submission · BR · H1 2026
version: v1
published_on: '2025-12-15'
topic: submission
clauses:
- id: submission-br-v1.main
  document_id: submission-br-v1
  rule_key: submission.main
  topic: submission
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
    kind: days
    days: 30
  relationships: []
- id: submission-br-v1.documentation
  document_id: submission-br-v1
  rule_key: submission.documentation
  topic: submission
  period: *id001
  scope: *id002
  value:
    kind: requirement
    value: Submit expenses with receipts, the business purpose, and the expense date.
      The submission date never changes which policy applied when the expense occurred.
  relationships: []
---

# Expense submission · BR · H1 2026

Synthetic Northstar Works policy. For demonstration only; this is not a real employer's policy.

## submission-br-v1.main

Submit an expense claim within 30 calendar days after the expense date.

## submission-br-v1.documentation

Submit expenses with receipts, the business purpose, and the expense date. The submission date never changes which policy applied when the expense occurred.
