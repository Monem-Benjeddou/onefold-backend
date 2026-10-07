---
title: Put it on the internet
type: ship
est_minutes: 90
requires_laptop: true
check:
  kind: http.get
  url: "{project.live_url}/health"
  expect:
    status: 200
    body_contains: "{project.ownership_token}"
  timeout_ms: 5000
---
Deploy your app, then prove it's yours: make `GET /health` return your project's verification token (shown in your project settings) anywhere in the response body.

We'll call `/health` on your live URL and check for a `200` and the token. We don't follow redirects, so use your final `https://` address.
