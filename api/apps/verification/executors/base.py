import re
from dataclasses import asdict, dataclass, field

PLACEHOLDER = re.compile(r"\{([a-z_.]+)\}")


@dataclass
class Outcome:
    passed: bool
    checked: str
    got: dict = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    hints: list[str] = field(default_factory=list)

    def as_result(self):
        return asdict(self)


def template_values(project):
    # An explicit allow-list: specs can't reach arbitrary attributes
    # (str.format on the model would allow {project.user.password}).
    return {
        "project.live_url": project.live_url,
        "project.ownership_token": project.ownership_token,
        "project.repo_full_name": project.repo_full_name,
    }


def render(template, project):
    values = template_values(project)

    def replace(match):
        key = match.group(1)
        if key not in values:
            raise KeyError(key)
        return values[key]

    return PLACEHOLDER.sub(replace, template)


def unknown_placeholders(template):
    allowed = {"project.live_url", "project.ownership_token", "project.repo_full_name"}
    return sorted(set(PLACEHOLDER.findall(template)) - allowed)


class Executor:
    kind = ""
    allowed_keys = {"kind"}

    def validate(self, spec):
        extra = sorted(set(spec) - self.allowed_keys)
        return [f"unexpected key(s): {', '.join(extra)}"] if extra else []

    def preflight(self, spec, project):
        """Problems on the builder's side that stop the check from running."""
        return []

    def run(self, spec, project):
        raise NotImplementedError
