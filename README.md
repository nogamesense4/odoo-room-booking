# Room & Equipment Booking (Odoo module)

A standalone Odoo module that lets internal users book a resource (room, equipment, etc.) for a time slot, with conflict prevention, availability windows and an enforced booking lifecycle.

> Status: in progress. Sections marked _TBD_ are filled in as each design decision is recorded in `docs/adr/`.

## How to run

Requires Docker. Runs Odoo 18.0 Community and PostgreSQL 16.

1. `docker compose up`. On first start this creates the `booking` database and installs the module with demo data.
2. Open http://localhost:8069
3. Log in as **Booking User** or **Booking Manager** (demo credentials: _TBD_) to see each role.

### Running the tests

```bash
docker compose run --rm odoo odoo -d booking -u room_booking --test-tags /room_booking --stop-after-init
```

Look for `0 failed, 0 error(s)` at the end of the output.

## Users and roles

| Role | Who | Can do |
|---|---|---|
| **Booking User** | Every internal user (default) | Create bookings for themselves; see all bookings, including who booked; edit or cancel only their own bookings |
| **Booking Manager** | Assigned explicitly | Manage resources and availability; confirm or reject requests; edit or cancel any booking; book on behalf of another user |

Each booking records **who it is for** (`user_id`, defaulting to the creator) separately from who created it. Only managers can set it to another user, for example an assistant booking a room for their manager.

## Using the module

**Menus** (app: **Room Booking**)
- **Bookings:** all bookings. This is the default.
- **To Approve:** Managers only. Lists Requested bookings waiting for a decision.
- **Configuration:** Managers only. Resources and Working Hours (`resource.calendar`).

**Bookings list (the default view)**
- Columns: name, resource, booked for, start, end, duration, and state as a coloured badge (Requested = amber, Confirmed = green, Rejected/Cancelled = grey, Completed = muted).
- Opens on the **Upcoming** filter, sorted by start time, so it answers "what's coming up?". Past and closed bookings are one filter away.
- Filters: My Bookings, Upcoming, Past, Requested, Confirmed. Group by: resource, state, booked for, start (day).

**Booking form**
- The status bar shows the lifecycle. Rejected and Cancelled only appear when the booking is in that state.
- Confirm / Reject / Cancel / Mark as done buttons appear only when your role and the booking's state allow them. They are for convenience only; every rule is enforced on the server.
- Chatter at the bottom records every change and notification.

**Calendar view**
- Coloured by resource. Dragging out a time slot opens the full booking form in a popup instead of quick-creating, so conflict and availability errors show up where you can fix them.
- No Gantt view: it's Enterprise-only.

**Resources**
- The form shows capacity for rooms only, plus the working-hours calendar, an approval checkbox and a description.
- An **Upcoming bookings (n)** smart button opens that resource's upcoming bookings.

## Assumptions

- **Internal users only.** The brief targets internal Odoo users, so portal and public users have no access.
- **Single company.** Multi-company record rules are not implemented.
- **Time zones.** Datetimes are stored in UTC and shown in each user's time zone (Odoo's default behaviour). Availability windows come from each resource's working-hours calendar (`resource.calendar`) and are evaluated in that calendar's time zone.
- **One resource per booking.** Booking a room plus a projector means making two bookings.
- Where the brief was unclear, I made my own decision and recorded the reasoning in an ADR under `docs/adr/`.

## Intentionally out of scope

| Left out | Why |
|---|---|
| Recurring bookings | Recurrence rules and exceptions add a lot of edge cases to conflict checking; making several one-off bookings covers the need for an MVP |
| Multi-resource bookings | Making two bookings is a workable alternative, and it keeps the conflict check to one resource per booking |
| Multi-day / overnight bookings | A booking must fit inside one continuous working interval, which keeps the availability rule simple to explain and test |
| Pooled equipment ("any of 5 projectors") | Each physical item is its own resource, so the conflict check stays a simple overlap check rather than a count |
| Per-resource closures (e.g. renovation) | Only calendar-wide leaves block bookings; a Manager blocks one resource with a "Maintenance" booking. Next step: `_inherits resource.resource` for per-resource leaves |
| Backfilling past usage | Bookings can't start in the past; there's no reporting need for historical entries |
| Sync to Odoo Calendar events | Syncing one way raises a two-way question (what if the event is moved?); the module's calendar view covers the visual need. Next step |
| Attendees + capacity check | Doesn't serve any of the brief's rules; `capacity` is display-only |
| No-show auto-cancel | There's no check-in data, so the system can't tell who didn't turn up; guessing would cancel real meetings |
| Multi-company | Not needed for a single internal team; it would add record rules without adding user value here |
| Payments / charging | Internal booking tool; no billing requirement |
| Portal / external users | The brief specifies internal users |
| Advanced time-zone handling | Odoo's UTC storage plus per-user display is enough for one office location |

## Design decisions

- [ADR-0001: Resource and availability model](docs/adr/0001-resource-and-availability-model.md)
- [ADR-0002: Booking storage and conflict prevention](docs/adr/0002-booking-storage-and-conflict-prevention.md)
- [ADR-0003: Booking lifecycle](docs/adr/0003-booking-lifecycle.md)
- [ADR-0004: Security model](docs/adr/0004-security-model.md)
- [ADR-0005: Tech stack and delivery](docs/adr/0005-tech-stack-and-delivery.md)
- [ADR-0006: Additional features](docs/adr/0006-additional-features.md)

## Trade-offs and simplifications

- **Availability is checked only when a booking is saved.** If a Manager later changes a calendar's hours, existing bookings are not re-checked. Doing that would need a calendar write hook and a policy for bookings that are no longer valid.
- **No manager override of availability.** Real exceptions are handled by editing the calendar.
- **Overlaps are rejected, not flagged.** A Requested booking holds its slot (first come, first served), so users get an answer immediately. The cost is that a manager can't choose between competing requests.
- **Conflicts are enforced twice.** A Python constraint gives a readable error, and a PostgreSQL exclusion constraint (`btree_gist`) closes the race between two users saving at the same moment.
- **Approval is set per resource.** Routine rooms confirm instantly; only resources flagged `requires_approval` wait for a Manager. Changing the flag affects only new bookings.
- **Final states can't be reopened.** A user who changes their mind makes a new booking, which keeps the history clean and avoids another conflict check.
- **Nobody deletes active history.** Users cancel instead of deleting; Managers can delete only rejected or cancelled bookings, as cleanup.
- **All bookings are visible to all internal users**, so people can see who holds a slot and sort out conflicts themselves. Privacy between users was traded for transparency.
- **Odoo 18, not 19.** 18 is well documented and supported, and AI tools are less likely to mix up APIs. On 19 the exclusion constraint would move to `models.Constraint`.
- **No CI pipeline.** Tests run with one documented command. Adding CI is a possible next step.
- **Rules 1 and 3 are covered; rule 2 (AI) is optional.** Chatter, follower notifications and two crons give users value right away. AI was deferred so the base features could be properly tested.
- **The system acts as its own actor.** Crons skip the role and time checks but still go through the transition table.
- _More TBD._

## How I used AI

_TBD. Will cover which tools I used, which parts I wrote by hand or heavily reworked (conflict logic, lifecycle), and how I verified AI output (tests and line-by-line review)._
