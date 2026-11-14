from datetime import timedelta

import psycopg2

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import BookingCase


@tagged("post_install", "-at_install")
class TestConflict(BookingCase):
    """Ticket 04: overlapping active bookings on one resource are rejected (ADR-0002).

    Existing booking in every test: Bob, Room A, 10:00-11:00 tomorrow.
    """

    def setUp(self):
        super().setUp()
        self.existing = self.book(self.bob, hour=10, hours=1)

    def test_back_to_back_bookings_are_allowed(self):
        before = self.book(self.alice, hour=9, hours=1)    # 09:00-10:00
        after = self.book(self.alice, hour=11, hours=1)    # 11:00-12:00
        self.assertEqual((before | after).mapped("state"), ["confirmed", "confirmed"])

    def test_partial_overlap_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.book(self.alice, hour=9, hours=2)         # 09:00-11:00

    def test_containment_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.book(self.alice, hour=8, hours=4)         # 08:00-12:00 contains it

    def test_exact_duplicate_is_rejected(self):
        with self.assertRaises(ValidationError):
            self.book(self.alice, hour=10, hours=1)

    def test_same_time_on_another_resource_is_allowed(self):
        other_room = self.env["booking.resource"].create({"name": "Room B"})
        booking = self.book(self.alice, resource=other_room, hour=10, hours=1)
        self.assertEqual(booking.state, "confirmed")

    def test_closed_bookings_do_not_block(self):
        for state in ("cancelled", "rejected", "completed"):
            with self.subTest(state=state):
                self.existing.sudo().write({"state": state})
                booking = self.book(self.alice, hour=10, hours=1)
                booking.sudo().write({"state": "cancelled"})  # free the slot for the next state

    def test_requested_bookings_hold_the_slot(self):
        self.existing.sudo().write({"state": "requested"})
        with self.assertRaises(ValidationError):
            self.book(self.alice, hour=10, hours=1)

    def test_moving_a_booking_ignores_itself(self):
        start = self.existing.start_datetime + timedelta(minutes=30)
        self.existing.write({"start_datetime": start, "end_datetime": start + timedelta(hours=1)})
        self.assertEqual(self.existing.start_datetime, start)

    def test_moving_onto_another_booking_is_rejected(self):
        mine = self.book(self.alice, hour=13, hours=1)
        with self.assertRaises(ValidationError):
            mine.write({
                "start_datetime": self.existing.start_datetime,
                "end_datetime": self.existing.end_datetime,
            })

    def test_error_message_names_the_conflict(self):
        with self.assertRaises(ValidationError) as caught:
            self.book(self.alice, hour=10, hours=1)
        message = str(caught.exception)
        self.assertIn("Room A", message)
        self.assertIn("Bob", message)
        self.assertIn("Confirmed", message)

    def test_database_rejects_overlap_that_bypasses_python(self):
        """The exclusion constraint holds even if the Python check never runs
        (e.g. two users saving at the same moment)."""
        self.env.flush_all()
        cr = self.env.cr
        with self.assertRaises(psycopg2.errors.ExclusionViolation), mute_logger("odoo.sql_db"):
            with cr.savepoint():
                # The constraint is deferred to commit; make it fire now.
                cr.execute("SET CONSTRAINTS booking_booking_no_overlap IMMEDIATE")
                cr.execute(
                    """INSERT INTO booking_booking
                       (name, resource_id, user_id, start_datetime, end_datetime, state)
                       VALUES ('Sneaky', %s, %s, %s, %s, 'confirmed')""",
                    (self.room.id, self.alice.id,
                     self.existing.start_datetime, self.existing.end_datetime),
                )
