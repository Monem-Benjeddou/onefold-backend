import shutil
from io import StringIO
from pathlib import Path

import pytest
from django.conf import settings
from django.core.management import CommandError, call_command

from apps.learning.models import PathVersion

pytestmark = pytest.mark.django_db


@pytest.fixture
def content(tmp_path):
    shutil.copytree(Path(settings.LEARNING_CONTENT_DIR) / "paths", tmp_path / "paths")
    return tmp_path


def run(*args):
    out = StringIO()
    call_command("sync_content", *args, stdout=out, stderr=out)
    return out.getvalue()


def test_check_only_writes_nothing(content):
    assert "is valid" in run("--dir", str(content), "--check")
    assert PathVersion.objects.count() == 0


def test_publish_then_rerun(content):
    assert "created, published" in run("--dir", str(content), "--publish")
    assert "unchanged, published" in run("--dir", str(content), "--publish")


def test_editing_without_a_version_bump_fails(content):
    run("--dir", str(content))
    step = next((content / "paths").rglob("01-problem-statement.md"))
    step.write_text(step.read_text() + "\nMore.\n")

    with pytest.raises(CommandError, match="Bump the version"):
        run("--dir", str(content))


def test_invalid_content_syncs_nothing(content):
    (content / "paths" / "ship-your-first-product" / "path.yml").write_text("title: x\n")
    with pytest.raises(CommandError, match="content problem"):
        run("--dir", str(content), "--publish")
    assert PathVersion.objects.count() == 0
