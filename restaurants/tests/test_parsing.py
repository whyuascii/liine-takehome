import pytest
from datetime import time
from restaurants.parsing import parse_day_specifiers, parse_hours_string, parse_time


class TestParseTime:
    def test_simple_am(self):
        # Act
        result = parse_time("11 am")

        # Assert
        assert result == time(11, 0)

    def test_simple_pm(self):
        # Act
        result = parse_time("5 pm")

        # Assert
        assert result == time(17, 0)

    def test_with_minutes_am(self):
        # Act
        result = parse_time("11:30 am")

        # Assert
        assert result == time(11, 30)

    def test_with_minutes_pm(self):
        # Act
        result = parse_time("5:30 pm")

        # Assert
        assert result == time(17, 30)

    def test_12_am_is_midnight(self):
        # Act
        result = parse_time("12 am")

        # Assert
        assert result == time(0, 0)

    def test_12_pm_is_noon(self):
        # Act
        result = parse_time("12 pm")

        # Assert
        assert result == time(12, 0)

    def test_12_30_am(self):
        # Act
        result = parse_time("12:30 am")

        # Assert
        assert result == time(0, 30)

    def test_12_30_pm(self):
        # Act
        result = parse_time("12:30 pm")

        # Assert
        assert result == time(12, 30)

    def test_with_extra_whitespace(self):
        # Act
        result = parse_time("  11:30  am  ")

        # Assert
        assert result == time(11, 30)

    def test_with_colon_zero_minutes(self):
        # Act
        result = parse_time("11:00 am")

        # Assert
        assert result == time(11, 0)


class TestParseDaySpecifiers:
    def test_single_day(self):
        # Act
        result = parse_day_specifiers("Mon")

        # Assert
        assert result == [0]

    def test_single_day_sunday(self):
        # Act
        result = parse_day_specifiers("Sun")

        # Assert
        assert result == [6]

    def test_day_range(self):
        # Act
        result = parse_day_specifiers("Mon-Fri")

        # Assert
        assert result == [0, 1, 2, 3, 4]

    def test_day_range_tues_spelling(self):
        # Act
        result = parse_day_specifiers("Tues-Fri")

        # Assert
        assert result == [1, 2, 3, 4]

    def test_full_week(self):
        # Act
        result = parse_day_specifiers("Mon-Sun")

        # Assert
        assert result == [0, 1, 2, 3, 4, 5, 6]

    def test_comma_separated_range_and_day(self):
        # Act
        result = parse_day_specifiers("Mon-Thu, Sun")

        # Assert
        assert result == [0, 1, 2, 3, 6]

    def test_comma_separated_day_and_range(self):
        # Act
        result = parse_day_specifiers("Mon, Wed-Sun")

        # Assert
        assert result == [0, 2, 3, 4, 5, 6]

    def test_comma_separated_ranges(self):
        # Act
        result = parse_day_specifiers("Mon-Wed, Fri-Sun")

        # Assert
        assert result == [0, 1, 2, 4, 5, 6]

    def test_single_day_comma_separated(self):
        # Act
        result = parse_day_specifiers("Mon, Wed, Fri")

        # Assert
        assert result == [0, 2, 4]

    def test_weekend(self):
        # Act
        result = parse_day_specifiers("Sat-Sun")

        # Assert
        assert result == [5, 6]

    def test_with_extra_whitespace(self):
        # Act
        result = parse_day_specifiers("  Mon-Fri , Sat  ")

        # Assert
        assert result == [0, 1, 2, 3, 4, 5]


class TestParseHoursString:
    def test_simple_all_week(self):
        # Act
        result = parse_hours_string("Mon-Sun 11 am - 10 pm")

        # Assert
        assert len(result) == 7
        for day in range(7):
            assert (day, time(11, 0), time(22, 0)) in result

    def test_comma_day_groups_single_time(self):
        # Act
        result = parse_hours_string("Mon-Thu, Sun 9 am - 10 pm")

        # Assert
        assert len(result) == 5
        for day in [0, 1, 2, 3, 6]:
            assert (day, time(9, 0), time(22, 0)) in result

    def test_multiple_blocks(self):
        # Act
        result = parse_hours_string("Mon-Fri 11 am - 10 pm / Sat-Sun 10 am - 9:30 pm")

        # Assert
        assert len(result) == 7
        for day in range(5):
            assert (day, time(11, 0), time(22, 0)) in result
        for day in [5, 6]:
            assert (day, time(10, 0), time(21, 30)) in result

    def test_overnight_hours_split(self):
        # Act
        result = parse_hours_string("Mon 5 pm - 12:30 am")

        # Assert
        assert (0, time(17, 0), time.max) in result  # Mon until end of day
        assert (1, time.min, time(0, 30)) in result  # Tue early morning

    def test_overnight_sunday_wraps_to_monday(self):
        # Act
        result = parse_hours_string("Sun 5 pm - 1:30 am")

        # Assert
        assert (6, time(17, 0), time.max) in result  # Sun until end of day
        assert (0, time.min, time(1, 30)) in result  # Mon early morning

    def test_closing_at_midnight_no_split(self):
        # Act
        result = parse_hours_string("Mon 11 am - 12 am")

        # Assert
        assert result == [(0, time(11, 0), time.max)]

    def test_overnight_range_multiple_days(self):
        # Act
        result = parse_hours_string("Mon-Wed 5 pm - 12:30 am")

        # Assert
        assert (0, time(17, 0), time.max) in result  # Mon until end of day
        assert (1, time.min, time(0, 30)) in result  # Tue early morning
        assert (1, time(17, 0), time.max) in result  # Tue until end of day
        assert (2, time.min, time(0, 30)) in result  # Wed early morning
        assert (2, time(17, 0), time.max) in result  # Wed until end of day
        assert (3, time.min, time(0, 30)) in result  # Thu early morning
        assert len(result) == 6

    def test_bonchon_full(self):
        # Arrange
        hours = "Mon-Wed 5 pm - 12:30 am  / Thu-Fri 5 pm - 1:30 am  / Sat 3 pm - 1:30 am  / Sun 3 pm - 11:30 pm"

        # Act
        result = parse_hours_string(hours)

        # Assert
        assert (6, time(15, 0), time(23, 30)) in result  # Sun 3pm-11:30pm
        assert (5, time(15, 0), time.max) in result  # Sat 3pm-end of day
        assert (6, time.min, time(1, 30)) in result  # Sun 0-1:30am (Sat overnight)

    def test_centro_individual_day_with_range(self):
        # Act
        result = parse_hours_string("Mon, Wed-Sun 11 am - 10 pm")

        # Assert
        assert len(result) == 6
        assert (0, time(11, 0), time(22, 0)) in result  # Mon
        assert all(entry[0] != 1 for entry in result)  # Tue excluded
        for day in [2, 3, 4, 5, 6]:
            assert (day, time(11, 0), time(22, 0)) in result

    def test_extra_whitespace_in_separator(self):
        # Act
        result = parse_hours_string("Mon 11 am - 10 pm  / Tue 9 am - 5 pm")

        # Assert
        assert (0, time(11, 0), time(22, 0)) in result
        assert (1, time(9, 0), time(17, 0)) in result
