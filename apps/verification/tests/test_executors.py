from types import SimpleNamespace
from unittest import mock

import pytest

from apps.verification import net
from apps.verification.executors import get_executor, render, validate_spec

PROJECT = SimpleNamespace(
    live_url="https://habit-loop.example.com",
    ownership_token="onefold-verify-abc",
    repo_full_name="ada/habit-loop",
)
SPEC = {
    "kind": "http.get",
    "url": "{project.live_url}/health",
    "expect": {"status": 200, "body_contains": "{project.ownership_token}"},
}


def response(status=200, body=b"", **headers):
    return net.FetchResult(
        status=status,
        reason="",
        headers=headers,
        body=body,
        truncated=False,
        elapsed_ms=42,
        ip="1.2.3.4",
    )


class TestValidateSpec:
    def test_valid_specs(self):
        assert validate_spec(SPEC) == []
        assert validate_spec({"kind": "attest", "statement": "Done."}) == []

    @pytest.mark.parametrize(
        "spec, problem",
        [
            ("nope", "must be a mapping"),
            ({"kind": "ssh"}, "unknown kind"),
            ({"kind": "attest"}, "'statement' is required"),
            ({"kind": "http.get"}, "'url' is required"),
            ({"kind": "http.get", "url": "ftp://x"}, "must start with"),
            ({"kind": "http.get", "url": "{project.user.email}"}, "unknown placeholder"),
            ({**SPEC, "expect": {"status": 999}}, "HTTP status code"),
            ({**SPEC, "expect": {"headers": {}}}, "unexpected expect key"),
            ({**SPEC, "timeout_ms": 60_000}, "timeout_ms"),
            ({**SPEC, "follow": True}, "unexpected key"),
        ],
    )
    def test_problems(self, spec, problem):
        assert any(problem in p for p in validate_spec(spec)), validate_spec(spec)


def test_render_uses_an_allow_list():
    assert render("{project.live_url}/health", PROJECT) == "https://habit-loop.example.com/health"
    with pytest.raises(KeyError):
        render("{project.user.password}", PROJECT)


class TestHttpGet:
    executor = get_executor("http.get")

    def run(self, result=None, error=None):
        with mock.patch.object(net, "fetch", return_value=result, side_effect=error) as fetch:
            outcome = self.executor.run(SPEC, PROJECT)
        return outcome, fetch

    def test_pass(self):
        outcome, fetch = self.run(response(200, b'{"ok": true, "token": "onefold-verify-abc"}'))

        fetch.assert_called_once_with("https://habit-loop.example.com/health", timeout_s=5.0)
        assert outcome.passed
        assert outcome.reasons == []
        assert "returns 200" in outcome.checked and "onefold-verify-abc" in outcome.checked
        assert outcome.got["status"] == 200

    def test_missing_token(self):
        outcome, _ = self.run(response(200, b"ok"))
        assert not outcome.passed
        assert "doesn't contain" in outcome.reasons[0]

    def test_redirect_is_reported_not_followed(self):
        outcome, _ = self.run(
            response(301, b"", location="https://www.habit-loop.example.com/health")
        )
        assert not outcome.passed
        assert "Expected status 200, got 301." in outcome.reasons
        assert "www.habit-loop.example.com" in outcome.hints[0]

    def test_server_error_hint(self):
        outcome, _ = self.run(response(502, b"Bad gateway"))
        assert "logs" in outcome.hints[0]

    def test_blocked_and_unreachable(self):
        blocked, _ = self.run(
            error=net.BlockedURL("habit-loop.example.com resolves to a non-public address")
        )
        down, _ = self.run(error=net.FetchError("No response within 5s"))
        assert not blocked.passed and "public internet" in blocked.hints[0]
        assert not down.passed and "asleep" in down.hints[0]

    def test_preflight_needs_a_live_url(self):
        assert self.executor.preflight(SPEC, SimpleNamespace(live_url="")) == [
            "Add your live URL to the project first."
        ]
