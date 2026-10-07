---
title: Know when it breaks before your users do
type: check
est_minutes: 40
requires_laptop: true
check:
  kind: attest
  statement: Errors from my production app reach an error tracker, and I get alerted when /health fails.
---
Add error tracking and an uptime alert on `/health`. Then break something on purpose and watch the alert arrive.
