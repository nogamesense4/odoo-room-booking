from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase


class BookingCase(TransactionCase):
    """Shared fixtures: one plain User, one Manager, a room and an approval room."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env["res.users"].with_context(no_reset_password=True)
        internal = cls.env.ref("base.group_user")
        manager = cls.env.ref("room_booking.group_booking_manager")
        cls.alice = Users.create({
            "name": "Alice", "login": "test_alice", "groups_id": [(6, 0, [internal.id])],
        })
        cls.bob = Users.create({
            "name": "Bob", "login": "test_bob", "groups_id": [(6, 0, [internal.id])],
        })
        cls.manager = Users.create({
            "name": "Maria Manager", "login": "test_manager",
            "groups_id": [(6, 0, [internal.id, manager.id])],
        })
        Resource = cls.env["booking.resource"]
        cls.room = Resource.create({"name": "Room A", "resource_type": "room"})
        cls.approval_room = Resource.create({
            "name": "Boardroom", "resource_type": "room", "requires_approval": True,
        })

    @staticmethod
    def slot(days=1, hour=10, hours=1):
        """A future [start, end) pair, `days` from now, starting at `hour` UTC."""
        start = (fields.Datetime.now() + timedelta(days=days)).replace(
            hour=hour, minute=0, second=0, microsecond=0)
        return start, start + timedelta(hours=hours)

    def book(self, user, resource=None, days=1, hour=10, hours=1, **vals):
        start, end = self.slot(days, hour, hours)
        return self.env["booking.booking"].with_user(user).create({
            "name": "Meeting",
            "resource_id": (resource or self.room).id,
            "start_datetime": start,
            "end_datetime": end,
            **vals,
        })
