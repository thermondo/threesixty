import csv
import urllib.request

from django.core.management import BaseCommand, CommandError

from threesixty.models import Question


class Command(BaseCommand):
    """
    Import set of questions as a CSV.

    The CSV must have the following headers "statement",
    "attribute" and "connotation".
    """

    help = __doc__.strip()

    def add_arguments(self, parser):
        parser.add_argument(
            "CSV", help="URI to CSV file." " I can be both a file:// or http:// URI."
        )

    def handle(self, *args, **options):
        csv_uri = options.get("CSV")

        response = urllib.request.urlopen(csv_uri)  # nosec

        csv_reader = csv.DictReader(chunk.decode() for chunk in response)
        questions = (
            Question(
                text=row["statement"],
                attribute=row["attribute"],
                connotation=row["connotation"] in ["1", "true", "positive"],
            )
            for row in csv_reader
        )
        try:
            Question.objects.bulk_create(questions)
        except KeyError as e:
            raise CommandError("CSV header do not match.") from e
