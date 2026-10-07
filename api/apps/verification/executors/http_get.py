from .. import net
from .base import Executor, Outcome, render, unknown_placeholders

BODY_EXCERPT_CHARS = 300


class HttpGetExecutor(Executor):
    """GET a URL on the builder's live app and compare status and body."""

    kind = "http.get"
    allowed_keys = {"kind", "url", "expect", "timeout_ms"}
    expect_keys = {"status", "body_contains"}

    def validate(self, spec):
        problems = super().validate(spec)
        url = spec.get("url")
        if not isinstance(url, str) or not url:
            problems.append("'url' is required")
        else:
            if not url.startswith(("https://", "http://", "{project.live_url}")):
                problems.append("'url' must start with https://, http:// or {project.live_url}")
            problems += [f"unknown placeholder {{{p}}}" for p in unknown_placeholders(url)]

        expect = spec.get("expect", {})
        if not isinstance(expect, dict):
            problems.append("'expect' must be a mapping")
            expect = {}
        extra = sorted(set(expect) - self.expect_keys)
        if extra:
            problems.append(f"unexpected expect key(s): {', '.join(extra)}")
        status = expect.get("status", 200)
        if not isinstance(status, int) or not 100 <= status <= 599:
            problems.append("'expect.status' must be an HTTP status code")
        contains = expect.get("body_contains")
        if contains is not None:
            if not isinstance(contains, str) or not contains:
                problems.append("'expect.body_contains' must be a non-empty string")
            else:
                problems += [f"unknown placeholder {{{p}}}" for p in unknown_placeholders(contains)]

        timeout = spec.get("timeout_ms", 5000)
        if not isinstance(timeout, int) or not 500 <= timeout <= 10_000:
            problems.append("'timeout_ms' must be between 500 and 10000")
        return problems

    def preflight(self, spec, project):
        if "{project.live_url}" in spec["url"] and not project.live_url:
            return ["Add your live URL to the project first."]
        return []

    def run(self, spec, project):
        url = render(spec["url"], project)
        expect = spec.get("expect", {})
        want_status = expect.get("status", 200)
        want_text = render(expect["body_contains"], project) if expect.get("body_contains") else None

        checked = f"GET {url} returns {want_status}"
        if want_text:
            checked += f" and the response contains “{want_text}”"

        try:
            response = net.fetch(url, timeout_s=spec.get("timeout_ms", 5000) / 1000)
        except net.BlockedURL as exc:
            return Outcome(
                passed=False,
                checked=checked,
                reasons=[str(exc)],
                hints=["Checks only call public internet addresses. Use your deployed URL."],
            )
        except net.FetchError as exc:
            return Outcome(
                passed=False,
                checked=checked,
                reasons=[str(exc)],
                hints=_connection_hints(str(exc)),
            )

        text = response.body.decode("utf-8", errors="replace")
        got = {
            "status": response.status,
            "reason": response.reason,
            "elapsed_ms": response.elapsed_ms,
            "content_type": response.headers.get("content-type", ""),
            "body_excerpt": text[:BODY_EXCERPT_CHARS],
        }
        reasons, hints = [], []
        if response.status != want_status:
            reasons.append(f"Expected status {want_status}, got {response.status}.")
            hints += _status_hints(response.status, response.headers.get("location"))
        if want_text and want_text not in text:
            reasons.append(f"The response doesn't contain “{want_text}”.")
            if response.truncated:
                hints.append("Your response is over 1 MB; return the token near the top.")
            else:
                hints.append("Return the token exactly as shown, from the path above.")
        return Outcome(passed=not reasons, checked=checked, got=got, reasons=reasons, hints=hints)


def _status_hints(status, location):
    if 300 <= status < 400:
        target = f" to {location}" if location else ""
        return [f"Your app redirects{target}. Checks don't follow redirects; use the final URL."]
    if status == 404:
        return ["The route doesn't exist on your deployed app. Is the latest commit deployed?"]
    if status in (401, 403):
        return ["The route needs auth. Keep the health route public."]
    if status >= 500:
        return ["Your app is erroring. Check your hosting provider's logs for the stack trace."]
    return []


def _connection_hints(message):
    if message.startswith("Couldn't resolve"):
        return ["Check the domain spelling, and that DNS has propagated."]
    if message.startswith("TLS"):
        return ["Your HTTPS certificate isn't valid for this domain yet."]
    if message.startswith("No response"):
        return ["Your app may be asleep or overloaded. Open it in a browser, then retry."]
    return ["Make sure the app is deployed and running, then retry."]
