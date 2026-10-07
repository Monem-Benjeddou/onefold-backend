from .base import Executor, Outcome


class AttestExecutor(Executor):
    """The builder confirms it themselves. Used where automation can't judge yet."""

    kind = "attest"
    allowed_keys = {"kind", "statement"}

    def validate(self, spec):
        problems = super().validate(spec)
        if not isinstance(spec.get("statement"), str) or not spec["statement"].strip():
            problems.append("'statement' is required: what the builder confirms")
        return problems

    def run(self, spec, project):
        return Outcome(passed=True, checked=f"You confirmed: {spec['statement']}")
