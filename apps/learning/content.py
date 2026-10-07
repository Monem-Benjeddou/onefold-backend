"""
Load learning paths from content-as-code files.

Layout (one directory per path)::

    <content_dir>/paths/<path-slug>/
        path.yml                     # title, outcome, version
        01-idea/
            station.yml              # title, role
            01-problem-statement.md  # YAML front matter + Markdown body
            02-scope-cut.md

Numeric prefixes give the order; the rest of the name is the slug. Step slugs
must be unique within a path because they address steps in the API.
"""

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path as FsPath

import yaml

from .models import Step

ORDERED_NAME = re.compile(r"^(?P<order>\d{2})-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)$")
FRONT_MATTER = re.compile(r"\A---\n(?P<meta>.*?)\n---\n?(?P<body>.*)\Z", re.DOTALL)
VERSION = re.compile(r"^\d+\.\d+\.\d+$")


class ContentError(Exception):
    def __init__(self, errors):
        self.errors = list(errors)
        super().__init__("\n".join(self.errors))


@dataclass
class StepSpec:
    order: int
    slug: str
    title: str
    type: str
    est_minutes: int
    requires_laptop: bool
    body_md: str
    check_spec: dict | None


@dataclass
class StationSpec:
    order: int
    slug: str
    title: str
    role: str
    steps: list[StepSpec] = field(default_factory=list)


@dataclass
class PathSpec:
    slug: str
    title: str
    outcome: str
    version: str
    content_hash: str
    stations: list[StationSpec] = field(default_factory=list)

    def iter_steps(self):
        for station in self.stations:
            yield from station.steps


def _read_yaml(file, errors):
    try:
        data = yaml.safe_load(file.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        errors.append(f"{file}: invalid YAML ({exc})")
        return {}
    if not isinstance(data, dict):
        errors.append(f"{file}: expected a mapping at the top level")
        return {}
    return data


def _require(data, key, file, errors, kind=str):
    value = data.get(key)
    if value is None or value == "" or not isinstance(value, kind):
        errors.append(f"{file}: '{key}' is required and must be {kind.__name__}")
        return None
    return value


def _content_hash(root):
    digest = hashlib.sha256()
    for file in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(file.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(file.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _load_step(file, errors):
    match = ORDERED_NAME.match(file.stem)
    if not match:
        errors.append(f"{file}: name must look like '01-step-slug.md'")
        return None
    parsed = FRONT_MATTER.match(file.read_text(encoding="utf-8"))
    if not parsed:
        errors.append(f"{file}: missing YAML front matter ('---' block at the top)")
        return None
    try:
        meta = yaml.safe_load(parsed["meta"]) or {}
    except yaml.YAMLError as exc:
        errors.append(f"{file}: invalid front matter ({exc})")
        return None
    if not isinstance(meta, dict):
        errors.append(f"{file}: front matter must be a mapping")
        return None

    title = _require(meta, "title", file, errors)
    step_type = _require(meta, "type", file, errors)
    est_minutes = _require(meta, "est_minutes", file, errors, int)
    if step_type and step_type not in Step.Type.values:
        errors.append(f"{file}: type must be one of {', '.join(Step.Type.values)}")
    if est_minutes is not None and not 1 <= est_minutes <= 600:
        errors.append(f"{file}: est_minutes must be between 1 and 600")

    check_spec = meta.get("check")
    if check_spec is not None:
        from apps.verification.executors import validate_spec

        for problem in validate_spec(check_spec):
            errors.append(f"{file}: check: {problem}")
    elif step_type in (Step.Type.CHECK, Step.Type.SHIP):
        errors.append(f"{file}: '{step_type}' steps need a 'check'")

    return StepSpec(
        order=int(match["order"]),
        slug=match["slug"],
        title=title or "",
        type=step_type or "",
        est_minutes=est_minutes or 0,
        requires_laptop=bool(meta.get("requires_laptop", False)),
        body_md=parsed["body"].strip() + "\n",
        check_spec=check_spec,
    )


def load_path(root):
    """Parse and validate one path directory. Raises ContentError."""
    root = FsPath(root)
    errors = []
    if not (root / "path.yml").is_file():
        raise ContentError([f"{root}: missing path.yml"])

    meta = _read_yaml(root / "path.yml", errors)
    title = _require(meta, "title", root / "path.yml", errors)
    version = _require(meta, "version", root / "path.yml", errors)
    if version and not VERSION.match(version):
        errors.append(f"{root / 'path.yml'}: version must be semver, e.g. 1.0.0")

    spec = PathSpec(
        slug=root.name,
        title=title or "",
        outcome=meta.get("outcome", "") or "",
        version=version or "",
        content_hash=_content_hash(root),
    )

    seen_station_orders, seen_step_slugs = set(), set()
    for station_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        match = ORDERED_NAME.match(station_dir.name)
        if not match:
            errors.append(f"{station_dir}: name must look like '01-station-slug'")
            continue
        order = int(match["order"])
        if order in seen_station_orders:
            errors.append(f"{station_dir}: duplicate station number {order:02d}")
        seen_station_orders.add(order)

        station_file = station_dir / "station.yml"
        if not station_file.is_file():
            errors.append(f"{station_dir}: missing station.yml")
            continue
        station_meta = _read_yaml(station_file, errors)
        station = StationSpec(
            order=order,
            slug=match["slug"],
            title=_require(station_meta, "title", station_file, errors) or "",
            role=_require(station_meta, "role", station_file, errors) or "",
        )

        seen_step_orders = set()
        for step_file in sorted(station_dir.glob("*.md")):
            step = _load_step(step_file, errors)
            if step is None:
                continue
            if step.order in seen_step_orders:
                errors.append(f"{step_file}: duplicate step number {step.order:02d}")
            if step.slug in seen_step_slugs:
                errors.append(f"{step_file}: step slug '{step.slug}' is already used in this path")
            seen_step_orders.add(step.order)
            seen_step_slugs.add(step.slug)
            station.steps.append(step)

        if not station.steps:
            errors.append(f"{station_dir}: a station needs at least one step")
        spec.stations.append(station)

    if not spec.stations:
        errors.append(f"{root}: a path needs at least one station")
    if errors:
        raise ContentError(errors)
    return spec
