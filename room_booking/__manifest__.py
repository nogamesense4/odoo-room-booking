{
    "name": "Room Booking",
    "summary": "Book rooms and equipment for a time slot, with conflict prevention",
    "version": "18.0.1.0.0",
    "category": "Productivity",
    "license": "LGPL-3",
    "depends": ["base", "resource"],
    "data": [
        "security/room_booking_groups.xml",
        "security/ir.model.access.csv",
        "security/booking_rules.xml",
        "views/booking_resource_views.xml",
        "views/booking_booking_views.xml",
        "views/menus.xml",
    ],
    "demo": [
        "demo/booking_demo.xml",
    ],
    "application": True,
    "installable": True,
}
