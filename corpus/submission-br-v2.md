---
id: submission-br-v2
title: Expense submission · BR · H2 2026
version: v2
published_on: '2026-06-15'
topic: submission
clauses:
- id: submission-br-v2.main
  document_id: submission-br-v2
  rule_key: submission.main
  topic: submission
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
    kind: days
    days: 45
  relationships:
  - kind: supersedes
    target_id: submission-br-v1.main
- id: submission-br-v2.documentation
  document_id: submission-br-v2
  rule_key: submission.documentation
  topic: submission
  period: *id001
  scope: *id002
  value:
    kind: requirement
    value: Submit expenses with receipts, the business purpose, and the expense date.
      The submission date never changes which policy applied when the expense occurred.
  relationships:
  - kind: supersedes
    target_id: submission-br-v1.documentation
---

# Expense submission · BR · H2 2026

Synthetic Northstar Works policy. For demonstration only; this is not a real employer's policy.

## submission-br-v2.main

Submit an expense claim within 45 calendar days after the expense date.

## submission-br-v2.documentation

Submit expenses with receipts, the business purpose, and the expense date. The submission date never changes which policy applied when the expense occurred.
