import pytest
from datetime import time
from django.test import Client
from restaurants.models import Restaurant, OpeningHours


@pytest.fixture
def client():
    return Client()


def _create_restaurant(name, hours_list):
    """Helper: create a restaurant with opening hours.

    hours_list: list of (day_of_week, open_time, close_time)
    """
    r = Restaurant.objects.create(name=name)
    for day, open_time, close_time in hours_list:
        OpeningHours.objects.create(
            restaurant=r,
            day_of_week=day,
            open_time=open_time,
            close_time=close_time,
        )
    return r


@pytest.mark.django_db
class TestOpenRestaurantsView:
    def test_returns_open_restaurants(self, client):
        # Arrange
        _create_restaurant("Elzar's Fine Cuisine", [(0, time(11, 0), time(22, 0))])
        _create_restaurant("Fishy Joe's", [(1, time(11, 0), time(22, 0))])

        # Act
        response = client.get("/api/restaurants/open/", {"datetime": "2024-01-15T14:00:00"})

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["restaurants"] == ["Elzar's Fine Cuisine"]

    def test_returns_multiple_restaurants(self, client):
        # Arrange
        _create_restaurant("Elzar's Fine Cuisine", [(0, time(11, 0), time(22, 0))])
        _create_restaurant("Fishy Joe's", [(0, time(10, 0), time(23, 0))])

        # Act
        response = client.get("/api/restaurants/open/", {"datetime": "2024-01-15T12:00:00"})

        # Assert
        data = response.json()
        assert data["restaurants"] == ["Elzar's Fine Cuisine", "Fishy Joe's"]

    def test_returns_alphabetically_sorted(self, client):
        # Arrange
        _create_restaurant("Zoidberg's Dumpster", [(0, time(11, 0), time(22, 0))])
        _create_restaurant("Bender's Bistro", [(0, time(11, 0), time(22, 0))])
        _create_restaurant("Leela's Lounge", [(0, time(11, 0), time(22, 0))])

        # Act
        response = client.get("/api/restaurants/open/", {"datetime": "2024-01-15T12:00:00"})

        # Assert
        data = response.json()
        assert data["restaurants"] == ["Bender's Bistro", "Leela's Lounge", "Zoidberg's Dumpster"]

    def test_empty_list_when_none_open(self, client):
        # Arrange
        _create_restaurant("Elzar's Fine Cuisine", [(0, time(11, 0), time(22, 0))])

        # Act
        response = client.get("/api/restaurants/open/", {"datetime": "2024-01-15T05:00:00"})

        # Assert
        data = response.json()
        assert data["restaurants"] == []

    def test_includes_at_opening_time(self, client):
        # Arrange
        _create_restaurant("Planet Express Canteen", [(0, time(11, 0), time(22, 0))])

        # Act
        response = client.get("/api/restaurants/open/", {"datetime": "2024-01-15T11:00:00"})

        # Assert
        assert "Planet Express Canteen" in response.json()["restaurants"]

    def test_excludes_at_closing_time(self, client):
        # Arrange
        _create_restaurant("Planet Express Canteen", [(0, time(11, 0), time(22, 0))])

        # Act
        response = client.get("/api/restaurants/open/", {"datetime": "2024-01-15T22:00:00"})

        # Assert
        assert "Planet Express Canteen" not in response.json()["restaurants"]

    def test_overnight_hours_early_morning(self, client):
        # Arrange
        _create_restaurant("Robot Arms Apartments Bar", [
            (0, time(17, 0), time.max),
            (1, time.min, time(1, 30)),
        ])

        # Act
        response = client.get("/api/restaurants/open/", {"datetime": "2024-01-16T01:00:00"})

        # Assert
        assert "Robot Arms Apartments Bar" in response.json()["restaurants"]

    def test_overnight_not_returned_after_close(self, client):
        # Arrange
        _create_restaurant("Robot Arms Apartments Bar", [
            (0, time(17, 0), time.max),
            (1, time.min, time(1, 30)),
        ])

        # Act
        response = client.get("/api/restaurants/open/", {"datetime": "2024-01-16T02:00:00"})

        # Assert
        assert "Robot Arms Apartments Bar" not in response.json()["restaurants"]

    def test_closed_on_unlisted_day(self, client):
        # Arrange
        _create_restaurant("Kif's Kitchen", [(0, time(11, 0), time(22, 0))])

        # Act
        response = client.get("/api/restaurants/open/", {"datetime": "2024-01-17T12:00:00"})

        # Assert
        assert response.json()["restaurants"] == []

    def test_midnight_query(self, client):
        # Arrange
        _create_restaurant("Hermes' Jerk Hut", [(0, time(11, 0), time.max)])

        # Act
        response = client.get("/api/restaurants/open/", {"datetime": "2024-01-15T00:00:00"})

        # Assert
        assert "Hermes' Jerk Hut" not in response.json()["restaurants"]

    def test_returns_datetime_in_response(self, client):
        # Act
        response = client.get("/api/restaurants/open/", {"datetime": "2024-01-15T14:00:00"})

        # Assert
        data = response.json()
        assert data["datetime"] == "2024-01-15T14:00:00"

    def test_missing_datetime_returns_400(self, client):
        # Act
        response = client.get("/api/restaurants/open/")

        # Assert
        assert response.status_code == 400
        assert "error" in response.json()

    def test_invalid_datetime_returns_400(self, client):
        # Act
        response = client.get("/api/restaurants/open/", {"datetime": "not-a-date"})

        # Assert
        assert response.status_code == 400
        assert "error" in response.json()

    def test_no_duplicate_restaurants(self, client):
        """A restaurant with multiple matching hours should appear only once."""
        # Arrange
        _create_restaurant("Fry's Pizzeria", [
            (0, time(10, 0), time(20, 0)),
            (0, time(15, 0), time(23, 20)),
        ])

        # Act
        response = client.get("/api/restaurants/open/", {"datetime": "2024-01-15T11:00:00"})

        # Assert
        data = response.json()
        assert data["restaurants"].count("Fry's Pizzeria") == 1
