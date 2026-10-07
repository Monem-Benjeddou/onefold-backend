"""
Check executors, keyed by the `kind` in a step's `check` spec.

Each executor validates its spec (at content-sync time) and runs it against a
project, returning an Outcome that says what we checked and what we got.
"""

from .base import Outcome, render
from .attest import AttestExecutor
from .http_get import HttpGetExecutor

EXECUTORS = {executor.kind: executor for executor in (AttestExecutor(), HttpGetExecutor())}


def get_executor(kind):
    return EXECUTORS.get(kind)


def validate_spec(spec):
    """Return a list of problems with a check spec (empty when valid)."""
    if not isinstance(spec, dict):
        return ["must be a mapping with a 'kind'"]
    kind = spec.get("kind")
    executor = get_executor(kind)
    if executor is None:
        return [f"unknown kind '{kind}' (known: {', '.join(sorted(EXECUTORS))})"]
    return executor.validate(spec)


__all__ = ["EXECUTORS", "Outcome", "get_executor", "render", "validate_spec"]
