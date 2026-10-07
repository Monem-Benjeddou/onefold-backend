from pathlib import Path

import pytest
from django.conf import settings

from apps.learning.content import ContentError, load_path


def write(root, relative, text):
    file = root / relative
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(text)


def step(title="Do it", type_="build", extra=""):
    return f"---\ntitle: {title}\ntype: {type_}\nest_minutes: 10\n{extra}---\nBody.\n"


@pytest.fixture
def path_dir(tmp_path):
    root = tmp_path / "my-path"
    write(root, "path.yml", "title: My path\noutcome: Ship\nversion: 1.0.0\n")
    write(root, "01-idea/station.yml", "title: Idea\nrole: Founder\n")
    write(root, "01-idea/01-problem.md", step())
    return root


def problems(root):
    with pytest.raises(ContentError) as exc:
        load_path(root)
    return "\n".join(exc.value.errors)


def test_loads_a_valid_path(path_dir):
    write(path_dir, "02-ship/station.yml", "title: Ship\nrole: DevOps\n")
    write(
        path_dir,
        "02-ship/01-go-live.md",
        step(type_="ship", extra='check:\n  kind: http.get\n  url: "{project.live_url}/health"\n'),
    )

    spec = load_path(path_dir)

    assert (spec.slug, spec.version) == ("my-path", "1.0.0")
    assert [s.slug for s in spec.stations] == ["idea", "ship"]
    go_live = spec.stations[1].steps[0]
    assert (go_live.slug, go_live.type, go_live.check_spec["kind"]) == ("go-live", "ship", "http.get")
    assert go_live.body_md == "Body.\n"
    assert len(spec.content_hash) == 64


def test_content_hash_changes_with_content(path_dir):
    before = load_path(path_dir).content_hash
    write(path_dir, "01-idea/01-problem.md", step(title="Changed"))
    assert load_path(path_dir).content_hash != before


def test_reports_every_problem_at_once(path_dir):
    write(path_dir, "path.yml", "title: My path\nversion: one\n")
    write(path_dir, "01-idea/02-no-front-matter.md", "Just text\n")
    write(path_dir, "01-idea/03-problem.md", step())  # duplicate slug
    write(path_dir, "01-idea/04-bad-type.md", step(type_="watch"))

    found = problems(path_dir)

    assert "version must be semver" in found
    assert "missing YAML front matter" in found
    assert "slug 'problem' is already used" in found
    assert "type must be one of" in found


def test_check_and_ship_steps_need_a_check(path_dir):
    write(path_dir, "01-idea/02-gate.md", step(type_="check"))
    assert "'check' steps need a 'check'" in problems(path_dir)


def test_invalid_check_specs_are_rejected(path_dir):
    write(
        path_dir,
        "01-idea/02-gate.md",
        step(type_="check", extra="check:\n  kind: http.get\n  url: '{project.user.password}'\n"),
    )
    found = problems(path_dir)
    assert "unknown placeholder {project.user.password}" in found


def test_unknown_check_kind_is_rejected(path_dir):
    write(path_dir, "01-idea/02-gate.md", step(type_="check", extra="check:\n  kind: magic\n"))
    assert "unknown kind 'magic'" in problems(path_dir)


def test_badly_named_station_dir(path_dir):
    write(path_dir, "Idea Two/station.yml", "title: X\nrole: Y\n")
    assert "name must look like '01-station-slug'" in problems(path_dir)


def test_the_bundled_draft_path_is_valid():
    root = Path(settings.LEARNING_CONTENT_DIR) / "paths" / "ship-your-first-product"
    spec = load_path(root)
    assert len(spec.stations) == 9
