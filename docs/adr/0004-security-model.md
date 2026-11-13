# ADR-0004: Security model

**Status:** Accepted, 9 Nov 2026

## Context

The brief requires CRUD on bookings "with proper read/write/create/delete access control". The roles were agreed in Session 1 (see the README, Users and roles). The role and time rules for state changes are defined in ADR-0003.

## Decision

### Groups

A module category, **Room Booking**, with two groups:

- `group_booking_user`: implied by `base.group_user`, so every internal user has it automatically.
- `group_booking_manager`: implies `group_booking_user`. The admin user is assigned to it in the data file.

Portal and public users have no access.

### Access rights (`ir.model.access.csv`)

| Model | User | Manager |
|---|---|---|
| `booking.resource` | read | read, write, create, delete |
| `booking.booking` | read, write, create | read, write, create, delete |

Users can't delete bookings. They **cancel** them, which keeps the history.

### Deleting

`@api.ondelete(at_uninstall=False)` allows deletion only of `rejected` or `cancelled` bookings, **for Managers too**. Active and Completed bookings can only end through the lifecycle.

### Record rules (`ir.rule`)

| Group | Read | Write |
|---|---|---|
| User | All bookings | Only where `user_id = user.id` |
| Manager | All bookings | All bookings |

- "Own booking" means `user_id`, not `create_uid`. Only Managers can book for others, so for normal users the two fields always match. If a Manager books for Alice, Alice can then manage that booking.
- Resources have no record rules; the access rights are enough.

### Where rules are enforced

- **Python** enforces every rule that depends on role and state, raising `AccessError` or `UserError`:
  - Confirm and reject are Manager-only
  - Time limits for cancelling and marking as done (ADR-0003)
  - Only Managers may set `user_id` to another user
  - Deleting only non-active bookings
- **`groups=` and `invisible` in views** only hide buttons. They are UX, not security, because any public method can be called over RPC.
- **No `sudo()` in user-facing code.** Users can already read all bookings, so the conflict check doesn't need elevated rights, and the exclusion constraint applies regardless. Only the Tier 2 cron runs with elevated rights.

## Alternatives considered

| Option | Why rejected |
|---|---|
| One role for everyone | Can't express approval or resource management; too thin for "proper access control" |
| A third, Approver role | More than this scope needs; Manager covers it |
| Let users delete their own bookings | Erases history; cancelling does the same job and leaves an audit trail |
| Hide other users' bookings | Users need to see who holds a slot to sort out conflicts themselves; this is an internal tool |
| Rely on hidden buttons | Can be bypassed over RPC |

## Consequences

- Tests use `with_user()` with one User and one Manager. They must cover:
  - A User can't write someone else's booking
  - A User can't delete any booking
  - A User can't set `user_id` to another user
  - A User can't confirm or reject
  - A Manager can't delete an active or completed booking
  - A User can't write to resources
