# ADR-0001: Resource and availability model

**Status:** Accepted, 9 Nov 2026

## Context

Users book rooms and equipment. Each resource has limited availability (e.g. business hours), and both creating a booking and detecting conflicts must respect it. Odoo already ships `resource.calendar`, which handles working hours, breaks, time zones and leaves.

## Decision

1. **One model, `booking.resource`**, with fields `name`, `resource_type` (selection: room / equipment / other), `capacity` (optional, shown for rooms only), `description` and `active`.
2. **One record per physical item.** Five projectors are five resources. There is no quantity or pool booking.
3. **Availability comes from `resource.calendar`.** `calendar_id` is a required Many2one that defaults to the company's working hours. The calendar's time zone is the one used for all availability checks.
4. **Plain Many2one, not `_inherits = {'resource.resource': ...}`.**
5. **Leaves that apply to the whole calendar block bookings** (e.g. public holidays). This comes free from `_work_intervals_batch`. To close a single resource, a Manager creates a Confirmed booking named "Maintenance".
6. **A booking must fit inside one continuous work interval.** Its `[start, end)` has to be contained in a single interval returned by the calendar. That rejects bookings across lunch breaks, overnight and over several days.
7. **Free start and end times**, validated so that `end > start`. There is no slot grid and no minimum or maximum duration.
8. **Availability is checked only when a booking is saved**, i.e. on create or when its time or resource changes. Changing a calendar later does not re-check existing bookings.
9. **No manager override** of availability windows.
10. **A resource can't be archived while it has future bookings that are Requested or Confirmed.**

## Alternatives considered

| Option | Why rejected |
|---|---|
| Separate room and equipment models | Duplicates the conflict logic, and booking behaviour doesn't differ between them |
| Quantity / pooled equipment | The conflict check would become counting booked units, and users couldn't tell which item they have |
| Custom `booking.availability` table (weekday, from, to) | Rebuilds what `resource.calendar` already does, without holidays, breaks or time zones |
| `_inherits resource.resource` | The idiomatic way (as `hr.employee` does it) and it gives per-resource leaves, but it adds hidden delegation and a second record per resource. **This is the next step** if per-resource closures are needed. |
| Re-check existing bookings when a calendar changes | Needs a write hook on the calendar plus a policy for bookings that are no longer valid; not worth it at this scope |
| Manager override flag | Adds a way to skip the rule; changing the calendar covers real exceptions |
| Auto-cancel bookings when a resource is archived | Needs notifications (chatter/mail); deferred to Tier 2 |

## Consequences

- Depends on Odoo's `resource` module.
- The availability check reuses `calendar_id._work_intervals_batch(start, end)`, so I have to understand how it behaves at interval edges and with time zones. Tests must cover booking exactly at the start or end of a window, across lunch, on a holiday, and overnight.
- Multi-day bookings (e.g. lending equipment out) and pooled equipment are out of scope.
