from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestInstall(TransactionCase):
    """Smoke test: the module installs and the security groups are wired (ADR-0004)."""

    def test_internal_users_get_booking_user_group(self):
        user = self.env["res.users"].create({"name": "New Employee", "login": "new_employee"})
        self.assertTrue(user.has_group("room_booking.group_booking_user"))
        self.assertFalse(user.has_group("room_booking.group_booking_manager"))

    def test_admin_is_booking_manager(self):
        admin = self.env.ref("base.user_admin")
        self.assertTrue(admin.has_group("room_booking.group_booking_manager"))
