from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError

# States that hold a slot (ADR-0002); the others are final (ADR-0003).
ACTIVE_STATES = ("requested", "confirmed")


class BookingBooking(models.Model):
    """A reservation of one resource for a [start, end) time range (ADR-0002)."""

    _name = "booking.booking"
    _description = "Booking"
    _order = "start_datetime, id"

    name = fields.Char(string="Purpose", required=True)
    resource_id = fields.Many2one("booking.resource", required=True, index=True)
    user_id = fields.Many2one(
        "res.users",
        string="Booked For",
        required=True,
        index=True,
        default=lambda self: self.env.user,
    )
    start_datetime = fields.Datetime(string="Start", required=True)
    end_datetime = fields.Datetime(string="End", required=True)
    duration = fields.Float(string="Duration (h)", compute="_compute_duration")
    state = fields.Selection(
        [
            ("requested", "Requested"),
            ("confirmed", "Confirmed"),
            ("rejected", "Rejected"),
            ("cancelled", "Cancelled"),
            ("completed", "Completed"),
        ],
        required=True,
        default="requested",
        readonly=True,
        copy=False,
    )
    description = fields.Text()
    # UI helper only: lets views lock fields for non-managers.
    is_booking_manager = fields.Boolean(compute="_compute_is_booking_manager")

    @api.depends("start_datetime", "end_datetime")
    def _compute_duration(self):
        for booking in self:
            if booking.start_datetime and booking.end_datetime:
                delta = booking.end_datetime - booking.start_datetime
                booking.duration = delta.total_seconds() / 3600
            else:
                booking.duration = 0.0

    @api.depends_context("uid")
    def _compute_is_booking_manager(self):
        is_manager = self.env.user.has_group("room_booking.group_booking_manager")
        for booking in self:
            booking.is_booking_manager = is_manager

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @api.constrains("start_datetime", "end_datetime")
    def _check_times(self):
        now = fields.Datetime.now()
        for booking in self:
            if booking.end_datetime <= booking.start_datetime:
                raise ValidationError(_("The end time must be after the start time."))
            # The system (data loading, crons) may record past bookings;
            # people may not (ADR-0002, ADR-0006).
            if not self.env.su and booking.start_datetime < now:
                raise ValidationError(_("A booking cannot start in the past."))

    def _check_booked_for(self, vals):
        """Only Managers may book for, or hand a booking to, another user (ADR-0004)."""
        if self.env.su or "user_id" not in vals:
            return
        if vals["user_id"] != self.env.uid and not self.env.user.has_group(
            "room_booking.group_booking_manager"
        ):
            raise AccessError(_("Only a Booking Manager can book for someone else."))

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._check_booked_for(vals)
            if "state" not in vals:
                resource = self.env["booking.resource"].browse(vals.get("resource_id"))
                vals["state"] = "requested" if resource.requires_approval else "confirmed"
        return super().create(vals_list)

    def write(self, vals):
        self._check_booked_for(vals)
        return super().write(vals)
