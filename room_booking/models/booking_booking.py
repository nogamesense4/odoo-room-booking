from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError

# States that hold a slot (ADR-0002); the others are final (ADR-0003).
ACTIVE_STATES = ("requested", "confirmed")


class BookingBooking(models.Model):
    """A reservation of one resource for a [start, end) time range (ADR-0002)."""

    _name = "booking.booking"
    _description = "Booking"
    _order = "start_datetime, id"

    # Source of truth for "no overlapping active bookings on one resource"
    # (ADR-0002). Half-open ranges, so back-to-back bookings don't collide.
    # DEFERRED: checked at commit, so the Python check below runs first and
    # gives the readable message; the database catches the race where two
    # users save at the same moment and neither can see the other's row.
    _sql_constraints = [
        (
            "no_overlap",
            "EXCLUDE USING gist ("
            " resource_id WITH =,"
            " tsrange(start_datetime, end_datetime, '[)') WITH &&"
            ") WHERE (state IN ('requested', 'confirmed'))"
            " DEFERRABLE INITIALLY DEFERRED",
            "This resource is already booked for an overlapping time.",
        ),
    ]

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

    def _auto_init(self):
        # The exclusion constraint compares resource_id (a plain integer) with
        # a GiST index, which needs btree_gist. It must exist before Odoo
        # creates the constraint at the end of _auto_init.
        self.env.cr.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
        return super()._auto_init()

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

    @api.constrains("resource_id", "start_datetime", "end_datetime", "state")
    def _check_no_overlap(self):
        """Readable version of the exclusion constraint (ADR-0002)."""
        for booking in self.filtered(lambda b: b.state in ACTIVE_STATES):
            clash = self.search([
                ("id", "!=", booking.id),
                ("resource_id", "=", booking.resource_id.id),
                ("state", "in", ACTIVE_STATES),
                ("start_datetime", "<", booking.end_datetime),
                ("end_datetime", ">", booking.start_datetime),
            ], limit=1)
            if clash:
                raise ValidationError(_(
                    "%(resource)s is already booked %(start)s–%(end)s by %(user)s (%(state)s).",
                    resource=clash.resource_id.display_name,
                    start=clash._format_local(clash.start_datetime, "%a %d %b %H:%M"),
                    end=clash._format_local(clash.end_datetime, "%H:%M"),
                    user=clash.user_id.display_name,
                    state=dict(clash._fields["state"].selection)[clash.state],
                ))

    def _format_local(self, value, fmt):
        """Show a UTC datetime in the current user's time zone."""
        return fields.Datetime.context_timestamp(self, value).strftime(fmt)

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
