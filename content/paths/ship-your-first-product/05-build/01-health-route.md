---
title: Add a health route
type: check
est_minutes: 30
requires_laptop: true
check:
  kind: attest
  statement: My app answers GET /health with status 200.
---
Every production app needs one boring, public route that says "I'm alive". Add `GET /health` that returns `200`. You'll use it to prove your deploy works in station 7.
