import logging

from django.core.management import BaseCommand

import rooms.services
import bussen.services


class Command(BaseCommand):
    """Data minimisation command to execute data minimization according to privacy policy."""

    def add_arguments(self, parser):
        """Arguments for the command."""
        parser.add_argument(
            "--dry-run", action="store_true", dest="dry-run", default=False, help="Dry run instead of saving data",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        deleted_objects = rooms.services.execute_data_minimisation(options["dry-run"])
        for d in deleted_objects:
            logging.info("Removed {}".format(d))

        deleted_objects = bussen.services.execute_data_minimisation(options["dry-run"])
        for d in deleted_objects:
            logging.info("Removed {}".format(d))
