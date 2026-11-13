from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class BookingResource(models.Model):
    """A bookable thing: one record per physical room or item (ADR-0001)."""

    _name = "booking.resource"
    _description = "Bookable Resource"
    _order = "resource_type, name"

    name = fields.Char(required=True)
    resource_type = fields.Selection(
        [("room", "Room"), ("equipment", "Equipment"), ("other", "Other")],
        string="Type",
        required=True,
        default="room",
    )
    # Display-only: no attendee count to check it against (ADR-0006).
    capacity = fields.Integer(help="Number of people the room seats.")
    # Availability windows come from Odoo's working-hours calendars, evaluated
    # in the calendar's own time zone.
    calendar_id = fields.Many2one(
        "resource.calendar",
        string="Working Hours",
        required=True,
        default=lambda self: self.env.company.resource_calendar_id,
    )
    requires_approval = fields.Boolean(
        help="If set, bookings by non-managers stay Requested until a Manager confirms them.",
    )
    description = fields.Text()
    active = fields.Boolean(default=True)

    @api.constrains("capacity")
    def _check_capacity(self):
        for resource in self:
            if resource.capacity < 0:
                raise ValidationError(_("Capacity cannot be negative."))
