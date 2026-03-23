from datetime import datetime
from django.http import JsonResponse
from restaurants.models import OpeningHours


def open_restaurants(request):
    """Return alphabetically sorted list of restaurants open at the given datetime.

    GET /api/restaurants/open/?datetime=<ISO-8601>

    Returns JSON: {"datetime": "...", "restaurants": ["..."]}
    Returns 400 if the datetime parameter is missing or invalid.
    """
    datetime_str = request.GET.get("datetime")
    if not datetime_str:
        return JsonResponse(
            {"error": "Missing required parameter: datetime"}, status=400
        )

    try:
        dt = datetime.fromisoformat(datetime_str)
    except (ValueError, TypeError):
        return JsonResponse(
            {"error": f"Invalid datetime format: {datetime_str!r}. Use ISO 8601 format, e.g. 2024-01-15T14:30:00"},
            status=400,
        )

    day_of_week = dt.weekday()  # 0=Monday
    query_time = dt.time()

    names = (
        OpeningHours.objects.filter(
            day_of_week=day_of_week,
            open_time__lte=query_time,
            close_time__gt=query_time,
        )
        .values_list("restaurant__name", flat=True)
        .distinct()
        .order_by("restaurant__name")
    )

    return JsonResponse(
        {
            "datetime": datetime_str,
            "restaurants": list(names),
        }
    )
