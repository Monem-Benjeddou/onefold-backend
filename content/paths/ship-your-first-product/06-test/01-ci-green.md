---
title: Get CI green
type: check
est_minutes: 60
requires_laptop: true
check:
  kind: attest
  statement: A CI workflow runs my tests on every push, and the latest run on my default branch passed.
---
Add one unit test and one end-to-end test, then a CI workflow that runs both on every push.

<!-- Becomes an automatic github.workflow_status check when the GitHub App lands (M3). -->
