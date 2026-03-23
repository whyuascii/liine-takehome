import os
import tempfile
from datetime import time

import pytest
from django.core.management import call_command
from restaurants.models import Restaurant, OpeningHours


@pytest.mark.django_db
class TestRestaurantModel:
    def test_create_restaurant(self):
        # Act
        restaurant = Restaurant.objects.create(name="Elzar's Fine Cuisine")

        # Assert
        assert restaurant.name == "Elzar's Fine Cuisine"
        assert str(restaurant) == "Elzar's Fine Cuisine"

    def test_restaurant_name_is_unique(self):
        # Arrange
        Restaurant.objects.create(name="Fishy Joe's")

        # Act & Assert
        with pytest.raises(Exception):
            Restaurant.objects.create(name="Fishy Joe's")


@pytest.mark.django_db
class TestOpeningHoursModel:
    def test_create_opening_hours(self):
        # Arrange
        restaurant = Restaurant.objects.create(name="Planet Express Canteen")

        # Act
        hours = OpeningHours.objects.create(
            restaurant=restaurant,
            day_of_week=0,
            open_time=time(11, 0),
            close_time=time(22, 0),
        )

        # Assert
        assert hours.restaurant == restaurant
        assert hours.day_of_week == 0
        assert hours.open_time == time(11, 0)
        assert hours.close_time == time(22, 0)

    def test_opening_hours_str(self):
        # Arrange
        restaurant = Restaurant.objects.create(name="Bender's Bistro")
        hours = OpeningHours.objects.create(
            restaurant=restaurant,
            day_of_week=0,
            open_time=time(11, 0),
            close_time=time(22, 0),
        )

        # Act
        result = str(hours)

        # Assert
        assert "Bender's Bistro" in result
        assert "Monday" in result

    def test_opening_hours_index_exists(self):
        # Act
        index_fields = [
            idx.fields for idx in OpeningHours._meta.indexes
        ]

        # Assert
        assert ["day_of_week", "open_time", "close_time"] in index_fields


@pytest.mark.django_db
class TestLoadRestaurantsCommand:
    def _create_csv(self, content):
        """Write CSV content to a temp file and return its path."""
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
        f.write(content)
        f.close()
        return f.name

    def test_loads_restaurants_from_csv(self):
        # Arrange
        csv = self._create_csv(
            '"Restaurant Name","Hours"\n'
            '"Elzar\'s Fine Cuisine","Mon-Sun 11 am - 10 pm"\n'
        )

        # Act
        call_command("load_restaurants", csv)
        os.unlink(csv)

        # Assert
        assert Restaurant.objects.count() == 1
        assert Restaurant.objects.first().name == "Elzar's Fine Cuisine"

    def test_creates_opening_hours(self):
        # Arrange
        csv = self._create_csv(
            '"Restaurant Name","Hours"\n'
            '"Leela\'s Lounge","Mon-Fri 11 am - 10 pm"\n'
        )

        # Act
        call_command("load_restaurants", csv)
        os.unlink(csv)

        # Assert
        assert OpeningHours.objects.count() == 5

    def test_handles_overnight_hours(self):
        # Arrange
        csv = self._create_csv(
            '"Restaurant Name","Hours"\n'
            '"Robot Arms Apartments Bar","Mon 5 pm - 1:30 am"\n'
        )

        # Act
        call_command("load_restaurants", csv)
        os.unlink(csv)

        # Assert
        hours = list(
            OpeningHours.objects.order_by("day_of_week", "open_time").values_list(
                "day_of_week", "open_time", "close_time"
            )
        )
        assert (0, time(17, 0), time.max) in hours  # Mon until end of day
        assert (1, time.min, time(1, 30)) in hours  # Tue early morning

    def test_idempotent_reload(self):
        # Arrange
        csv = self._create_csv(
            '"Restaurant Name","Hours"\n'
            '"Fishy Joe\'s","Mon-Sun 11 am - 10 pm"\n'
        )

        # Act
        call_command("load_restaurants", csv)
        call_command("load_restaurants", csv)
        os.unlink(csv)

        # Assert
        assert Restaurant.objects.count() == 1

    def test_multiple_restaurants(self):
        # Arrange
        csv = self._create_csv(
            '"Restaurant Name","Hours"\n'
            '"Hermes\' Jerk Hut","Mon-Fri 11 am - 10 pm"\n'
            '"Zoidberg\'s Dumpster","Sat-Sun 9 am - 5 pm"\n'
        )

        # Act
        call_command("load_restaurants", csv)
        os.unlink(csv)

        # Assert
        assert Restaurant.objects.count() == 2

    def test_strips_whitespace_from_names(self):
        # Arrange
        csv = self._create_csv(
            '"Restaurant Name","Hours"\n'
            '"  Kif\'s Kitchen  ","Mon 11 am - 10 pm"\n'
        )

        # Act
        call_command("load_restaurants", csv)
        os.unlink(csv)

        # Assert
        assert Restaurant.objects.first().name == "Kif's Kitchen"
