from datetime import timedelta

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import BookingCase


@tagged("post_install", "-at_install")
class TestAvailability(BookingCase):
    """A booking must fit inside one continuous working interval (ADR-0001)."""

    def test_exactly_window_start_and_end_allowed(self):
        morning = self.book(self.alice, hour=8, hours=4)     # 08:00-12:00
        afternoon = self.book(self.alice, hour=13, hours=4)  # 13:00-17:00
        self.assertTrue(morning and afternoon)

    def test_before_opening_rejected(self):
        with self.assertRaisesRegex(ValidationError, "working hours"):
            self.book(self.alice, hour=7, hours=2)

    def test_after_closing_rejected(self):
        with self.assertRaisesRegex(ValidationError, "working hours"):
            self.book(self.alice, hour=16, hours=2)

    def test_across_lunch_rejected(self):
        with self.assertRaisesRegex(ValidationError, "working hours"):
            self.book(self.alice, hour=11, hours=2)          # 11:00-13:00

    def test_inside_lunch_rejected(self):
        with self.assertRaisesRegex(ValidationError, "working hours"):
            self.book(self.alice, hour=12, hours=1)

    def test_overnight_rejected(self):
        with self.assertRaisesRegex(ValidationError, "working hours"):
            self.book(self.alice, hour=16, hours=17)         # 16:00 -> 09:00 next day

    def test_multi_day_rejected(self):
        with self.assertRaisesRegex(ValidationError, "working hours"):
            self.book(self.alice, hour=8, hours=57)          # 08:00 day 1 -> 17:00 day 3

    def test_holiday_rejected(self):
        start, _end = self.slot(days=2, hour=0, hours=0)
        self.env["resource.calendar.leaves"].create({
            "name": "Public holiday",
            "calendar_id": self.calendar.id,
            "date_from": start,
            "date_to": start + timedelta(days=1),
        })
        with self.assertRaisesRegex(ValidationError, "working hours"):
            self.book(self.alice, days=2, hour=10, hours=1)
        # The day before is unaffected.
        self.assertTrue(self.book(self.alice, days=1, hour=10, hours=1))

    def test_manager_also_blocked(self):
        with self.assertRaisesRegex(ValidationError, "working hours"):
            self.book(self.manager, hour=11, hours=2)

    def test_uses_calendar_time_zone(self):
        # 09:00-10:00 in Singapore is 01:00-02:00 UTC.
        sg = self.calendar.copy({"name": "SG hours", "tz": "Asia/Singapore"})
        room = self.env["booking.resource"].create({"name": "SG room", "calendar_id": sg.id})
        self.assertTrue(self.book(self.alice, resource=room, hour=1, hours=1))
        with self.assertRaisesRegex(ValidationError, "working hours"):
            self.book(self.alice, resource=room, hour=10, hours=1)  # 18:00 SGT

    def test_moving_outside_hours_rejected(self):
        booking = self.book(self.alice, hour=10, hours=1)
        start, end = self.slot(hour=12, hours=1)
        with self.assertRaisesRegex(ValidationError, "working hours"):
            booking.with_user(self.alice).write({"start_datetime": start, "end_datetime": end})

    def test_moving_to_closed_resource_rejected(self):
        night = self.calendar.copy({"name": "Night", "attendance_ids": [(5, 0, 0)] + [
            (0, 0, {"name": "night", "dayofweek": str(d), "hour_from": 20, "hour_to": 23})
            for d in range(7)
        ]})
        night_room = self.env["booking.resource"].create({"name": "Night room", "calendar_id": night.id})
        booking = self.book(self.alice, hour=10, hours=1)
        with self.assertRaisesRegex(ValidationError, "working hours"):
            booking.with_user(self.alice).write({"resource_id": night_room.id})

    def test_unrelated_edit_not_rechecked(self):
        booking = self.book(self.alice, hour=10, hours=1)
        # Calendar shrinks afterwards; the existing booking is not re-validated
        # unless its time or resource changes (ADR-0001 §8).
        self.calendar.attendance_ids.filtered(lambda a: a.hour_from == 8).hour_from = 11
        booking.with_user(self.alice).write({"name": "Renamed"})
        self.assertEqual(booking.name, "Renamed")
