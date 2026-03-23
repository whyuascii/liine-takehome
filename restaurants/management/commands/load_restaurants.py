import csv
from django.core.management.base import BaseCommand
from django.db import transaction
from restaurants.models import Restaurant, OpeningHours
from restaurants.parsing import parse_hours_string


class Command(BaseCommand):
    help = "Load CSV"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Path to the CSV")

    def handle(self, *args, **options):
        csv_path = options["csv_path"]

        with transaction.atomic():
            # Clear existing data for reload
            OpeningHours.objects.all().delete()
            Restaurant.objects.all().delete()

            restaurant_count = 0
            hours_count = 0

            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row["Restaurant Name"].strip()
                    hours_str = row["Hours"].strip()

                    restaurant = Restaurant.objects.create(name=name)
                    entries = parse_hours_string(hours_str)

                    for day, open_time, close_time in entries:
                        OpeningHours.objects.create(
                            restaurant=restaurant,
                            day_of_week=day,
                            open_time=open_time,
                            close_time=close_time,
                        )
                        hours_count += 1

                    restaurant_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Loaded {restaurant_count} restaurants with {hours_count} opening hour records"
            )
        )
