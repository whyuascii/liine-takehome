import os
import pytest
from django.core.management import call_command
from django.test import Client
from restaurants.models import Restaurant, OpeningHours


CSV_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "test_restaurants.csv")


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def loaded_db():
    """Load the test fixture CSV into the test database."""
    call_command("load_restaurants", CSV_PATH)


@pytest.mark.django_db
class TestIntegration:
    def test_csv_loads_all_restaurants(self, loaded_db):
        # Assert
        assert Restaurant.objects.count() == 10

    def test_csv_creates_opening_hours(self, loaded_db):
        # Assert
        for r in Restaurant.objects.all():
            assert r.opening_hours.count() > 0

    def test_monday_lunchtime(self, loaded_db, client):
        # Act
        response = client.get("/api/restaurants/open/", {"datetime": "2024-01-15T12:00:00"})

        # Assert
        restaurants = response.json()["restaurants"]
        assert "Daytime Grill" in restaurants
        assert "Morning Cafe" in restaurants
        assert "All Night Diner" in restaurants
        assert "Evening Only" not in restaurants  # opens at 5pm

    def test_tuesday_2am(self, loaded_db, client):
        # Act
        response = client.get("/api/restaurants/open/", {"datetime": "2024-01-16T02:00:00"})

        # Assert
        restaurants = response.json()["restaurants"]
        assert "Late Night Korean" in restaurants  # Mon-Sun 11am-4am overnight
        assert "Daytime Grill" not in restaurants  # closes at 10pm

    def test_wednesday_5pm(self, loaded_db, client):
        # Act
        response = client.get("/api/restaurants/open/", {"datetime": "2024-01-17T17:00:00"})

        # Assert
        restaurants = response.json()["restaurants"]
        assert "Evening Only" in restaurants
        assert "Weeknight Bites" in restaurants  # Mon-Wed 5pm-12:30am
        assert "Closed Tuesday" in restaurants  # Mon, Wed-Sun 11am-10pm

    def test_closed_tuesday(self, loaded_db, client):
        # Act
        response = client.get("/api/restaurants/open/", {"datetime": "2024-01-16T12:00:00"})

        # Assert
        assert "Closed Tuesday" not in response.json()["restaurants"]

    def test_saturday_night(self, loaded_db, client):
        # Act
        response = client.get("/api/restaurants/open/", {"datetime": "2024-01-20T23:00:00"})

        # Assert
        restaurants = response.json()["restaurants"]
        assert "Weekend Late" in restaurants  # Fri-Sat 11am-12:30am
        assert "Weekend Brunch" not in restaurants  # Sat-Sun 10am-9:30pm

    def test_sunday_morning_early(self, loaded_db, client):
        # Act
        response = client.get("/api/restaurants/open/", {"datetime": "2024-01-21T00:30:00"})

        # Assert
        restaurants = response.json()["restaurants"]
        assert "Weeknight Bites" in restaurants  # Sat 3pm-1:30am → Sun 0-1:30am
        assert "Oyster House" not in restaurants  # Sun starts at noon

    def test_response_format(self, loaded_db, client):
        # Act
        response = client.get("/api/restaurants/open/", {"datetime": "2024-01-15T12:00:00"})

        # Assert
        data = response.json()
        assert "datetime" in data
        assert "restaurants" in data
        assert isinstance(data["restaurants"], list)
        assert data["restaurants"] == sorted(data["restaurants"])
