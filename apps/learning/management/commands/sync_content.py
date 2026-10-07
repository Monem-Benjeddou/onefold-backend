from pathlib import Path as FsPath

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.learning.content import ContentError, load_path
from apps.learning.services import ImmutableVersionError, sync_path


class Command(BaseCommand):
    help = "Validate learning content files and sync them into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dir",
            default=str(settings.LEARNING_CONTENT_DIR),
            help="Content root (contains a 'paths' directory).",
        )
        parser.add_argument(
            "--publish", action="store_true", help="Publish synced versions to builders."
        )
        parser.add_argument(
            "--check", action="store_true", help="Validate only; don't write to the database."
        )

    def handle(self, *args, **options):
        paths_dir = FsPath(options["dir"]) / "paths"
        if not paths_dir.is_dir():
            raise CommandError(f"No 'paths' directory in {options['dir']}")

        specs, errors = [], []
        for path_dir in sorted(p for p in paths_dir.iterdir() if p.is_dir()):
            try:
                specs.append(load_path(path_dir))
            except ContentError as exc:
                errors.extend(exc.errors)
        if errors:
            for error in errors:
                self.stderr.write(f"  ✕ {error}")
            raise CommandError(f"{len(errors)} content problem(s). Nothing was synced.")

        for spec in specs:
            steps = sum(len(s.steps) for s in spec.stations)
            label = f"{spec.slug}@{spec.version} ({len(spec.stations)} stations, {steps} steps)"
            if options["check"]:
                self.stdout.write(f"  ✓ {label} is valid")
                continue
            try:
                version, created = sync_path(spec, publish=options["publish"])
            except ImmutableVersionError as exc:
                raise CommandError(str(exc)) from exc
            state = "published" if version.is_published else "draft"
            action = "created" if created else "unchanged"
            self.stdout.write(self.style.SUCCESS(f"  ✓ {label}: {action}, {state}"))
