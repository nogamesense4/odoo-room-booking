# ADR-0002: Booking storage and conflict prevention

**Status:** Accepted, 9 Nov 2026

## Context

The core problem is preventing overlapping bookings of the same resource. The brief leaves the method open: "reject or flag … solved your way". A check written only in Python has a race. Two users who save at the same moment can both pass the check, because neither transaction can see the other's uncommitted row.

## Decision

1. **`booking.booking` stores a datetime range.** Fields:
   - `name`: the purpose
   - `resource_id`
   - `user_id`: who the booking is for (see the README, Users and roles)
   - `start_datetime`, `end_datetime`: Odoo `Datetime`, stored in UTC
   - `state`
   - `description`
   - `duration`: computed, in hours
2. **Intervals are half-open, `[start, end)`.** Back-to-back bookings (9–10 and 10–11) do not conflict.
3. **Overlaps are rejected, not flagged.** A booking is rejected if it overlaps any *active* booking (state `requested` or `confirmed`) on the same resource. Requested bookings hold the slot: first come, first served. `rejected`, `cancelled` and `completed` bookings never block (states are defined in ADR-0003).
4. **The error names the conflict**, e.g. "Room A is already booked 10:00–11:00 by Alice (Requested)." This is safe because all users can see all bookings.
5. **Enforcement has two layers:**
   - **Python** `@api.constrains('resource_id', 'start_datetime', 'end_datetime', 'state')`: gives the friendly message. Not race-safe.
   - **PostgreSQL exclusion constraint**, declared in `_sql_constraints`:
     ```sql
     EXCLUDE USING gist (
       resource_id WITH =,
       tsrange(start_datetime, end_datetime, '[)') WITH &&
     ) WHERE (state IN ('requested', 'confirmed'))
     DEFERRABLE INITIALLY DEFERRED
     ```
     `_auto_init()` runs `CREATE EXTENSION IF NOT EXISTS btree_gist` before calling `super()`. (Not `init()`: Odoo adds `_sql_constraints` inside `_auto_init`, which runs before `init()`, so the extension would arrive too late.)
     **Deferred to commit** so that the Python check always runs first and gives the readable message, whatever order the ORM flushes in. The database still rejects the overlap when two transactions race, because the check happens at commit. `tsrange` (not `tstzrange`) is used because Odoo stores `Datetime` as `timestamp without time zone`. **The database is the source of truth; Python is there to explain the error.**
6. **No bookings in the past.** Setting `start_datetime` to a time before now is rejected, on create or when a booking is moved, for every role. Editing other fields on past bookings stays allowed. The **system** (superuser: data loading and crons) is exempt, consistent with ADR-0006, so demo data can include past bookings; no user can reach the superuser environment from the UI.
7. **Deferred to later sessions:** attendees, the Calendar link, and checking room capacity against attendees (Session 6).

## Alternatives considered

| Option | Why rejected |
|---|---|
| One row per slot or day, with a unique constraint | Needs a slot grid (rejected in ADR-0001) and creates many rows per booking |
| "Flag" model: allow overlapping Requested bookings and let a Manager resolve them on confirm | Needs a conflict queue and a way to resolve it, and users see bookings that may never happen |
| **B.** Python check + `SELECT … FOR UPDATE` on the resource row | Works without an extension, and Odoo retries on serialization failure. But it is only safe if every path that writes a booking takes the lock; the database constraint can't be bypassed |
| **C.** Python check only | Leaves the race open. This is the fallback if `btree_gist` can't be installed |
| Constraint checked immediately (not deferred) | Depending on when the ORM flushes, the raw database error could fire before the Python check, so users would see a generic message |
| Constraint added by hand in `init()` | A violation would show a raw database error; `_sql_constraints` maps it to a readable message |

## Consequences

- Requires the `btree_gist` extension, which the Odoo database user in docker-compose can create.
- Tests must cover:
  - Back-to-back bookings are allowed
  - Partial overlap, containment and exact duplicate are rejected
  - A different resource with the same time is allowed
  - Cancelled and Completed bookings don't block
  - Moving a booking re-checks it against others, but not against itself
  - A start time in the past is rejected
  - **Database layer:** an overlapping row inserted with raw SQL (past the Python check) is rejected by Postgres
- If a later Odoo version replaces `_sql_constraints` with `models.Constraint`, the same SQL moves there.
