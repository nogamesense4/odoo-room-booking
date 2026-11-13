from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged

from .common import BookingCase


@tagged("post_install", "-at_install")
class TestBookingHappyPath(BookingCase):
    """Ticket 03: book a resource; basic validation and access rules (ADR-0002, ADR-0004)."""

    def test_user_books_for_themselves_and_it_is_confirmed(self):
        booking = self.book(self.alice)
        self.assertEqual(booking.user_id, self.alice)
        self.assertEqual(booking.state, "confirmed")
        self.assertEqual(booking.duration, 1.0)

    def test_booking_on_approval_resource_starts_requested(self):
        booking = self.book(self.alice, resource=self.approval_room)
        self.assertEqual(booking.state, "requested")

    def test_end_must_be_after_start(self):
        start, _end = self.slot()
        with self.assertRaises(ValidationError):
            self.env["booking.booking"].with_user(self.alice).create({
                "name": "Backwards", "resource_id": self.room.id,
                "start_datetime": start, "end_datetime": start,
            })

    def test_cannot_create_booking_in_the_past(self):
        start = fields.Datetime.now() - timedelta(hours=2)
        with self.assertRaises(ValidationError):
            self.env["booking.booking"].with_user(self.alice).create({
                "name": "Too late", "resource_id": self.room.id,
                "start_datetime": start, "end_datetime": start + timedelta(hours=1),
            })

    def test_cannot_move_booking_into_the_past(self):
        booking = self.book(self.alice)
        start = fields.Datetime.now() - timedelta(hours=2)
        with self.assertRaises(ValidationError):
            booking.write({"start_datetime": start, "end_datetime": start + timedelta(hours=1)})

    def test_user_can_read_other_users_bookings(self):
        booking = self.book(self.bob)
        self.assertEqual(booking.with_user(self.alice).user_id, self.bob)

    def test_user_cannot_edit_other_users_booking(self):
        booking = self.book(self.bob)
        with self.assertRaises(AccessError):
            booking.with_user(self.alice).write({"name": "Mine now"})

    def test_user_can_edit_own_booking(self):
        booking = self.book(self.alice)
        booking.write({"name": "Renamed"})
        self.assertEqual(booking.name, "Renamed")

    def test_user_cannot_delete_bookings(self):
        booking = self.book(self.alice)
        with self.assertRaises(AccessError):
            booking.unlink()

    def test_user_cannot_book_for_someone_else(self):
        with self.assertRaises(AccessError):
            self.book(self.alice, user_id=self.bob.id)

    def test_user_cannot_reassign_own_booking(self):
        booking = self.book(self.alice)
        with self.assertRaises(AccessError):
            booking.write({"user_id": self.bob.id})

    def test_manager_books_for_someone_else_who_can_then_edit_it(self):
        booking = self.book(self.manager, user_id=self.alice.id)
        self.assertEqual(booking.user_id, self.alice)
        booking.with_user(self.alice).write({"description": "Agenda attached"})
        self.assertEqual(booking.description, "Agenda attached")
