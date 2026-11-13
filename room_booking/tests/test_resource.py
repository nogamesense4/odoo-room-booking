from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestResource(TransactionCase):
    """Ticket 02: Managers manage resources; Users can only read them (ADR-0001, ADR-0004)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env["res.users"].with_context(no_reset_password=True)
        cls.booking_user = Users.create({
            "name": "Test User",
            "login": "test_booking_user",
            "groups_id": [(6, 0, [cls.env.ref("base.group_user").id])],
        })
        cls.booking_manager = Users.create({
            "name": "Test Manager",
            "login": "test_booking_manager",
            "groups_id": [(6, 0, [
                cls.env.ref("base.group_user").id,
                cls.env.ref("room_booking.group_booking_manager").id,
            ])],
        })
        cls.room = cls.env["booking.resource"].with_user(cls.booking_manager).create({
            "name": "Test Room",
            "resource_type": "room",
            "capacity": 6,
        })

    def test_manager_can_create_edit_and_archive(self):
        room = self.room.with_user(self.booking_manager)
        room.write({"name": "Renamed Room", "requires_approval": True})
        self.assertEqual(room.name, "Renamed Room")
        room.action_archive()
        self.assertFalse(room.active)

    def test_calendar_defaults_to_company_working_hours(self):
        self.assertEqual(self.room.calendar_id, self.env.company.resource_calendar_id)

    def test_user_can_read_resources(self):
        room = self.room.with_user(self.booking_user)
        self.assertEqual(room.name, "Test Room")

    def test_user_cannot_create_resources(self):
        with self.assertRaises(AccessError):
            self.env["booking.resource"].with_user(self.booking_user).create({"name": "Sneaky Room"})

    def test_user_cannot_write_resources(self):
        with self.assertRaises(AccessError):
            self.room.with_user(self.booking_user).write({"name": "Hacked"})

    def test_user_cannot_delete_resources(self):
        with self.assertRaises(AccessError):
            self.room.with_user(self.booking_user).unlink()

    def test_capacity_cannot_be_negative(self):
        with self.assertRaises(ValidationError):
            self.room.write({"capacity": -1})
