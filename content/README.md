# Learning content

Paths are authored as files and synced into the database. Builders are pinned to the
version they enrolled in, so a published version is immutable: to change content,
bump `version` in `path.yml`.

```
content/paths/<path-slug>/
  path.yml                 # title, outcome, version (semver)
  01-idea/
    station.yml            # title, role
    01-problem-statement.md
```

Step files are Markdown with YAML front matter:

```yaml
---
title: Put it on the internet
type: ship            # learn | build | check | ship
est_minutes: 90
requires_laptop: true
check:                # required for check and ship steps
  kind: http.get      # attest | http.get
  url: "{project.live_url}/health"
  expect: {status: 200, body_contains: "{project.ownership_token}"}
---
```

Validate, then sync:

```
python manage.py sync_content --check
python manage.py sync_content --publish
```

The `ship-your-first-product` path is a **draft skeleton** (one or two steps per station)
for development and tests. The full ~45-step path is the content author's work (MVP plan, section 3.2).
