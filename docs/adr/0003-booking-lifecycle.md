# ADR-0003: Booking lifecycle

**Status:** Accepted, 9 Nov 2026

## Context

The brief requires a booking lifecycle (e.g. Requested → Confirmed → Cancelled/Completed) that the system enforces. Some resources, such as the boardroom or expensive equipment, need a Manager's approval. Most don't.

## Decision

### States

`requested`, `confirmed`, `rejected`, `cancelled`, `completed`

```
            ┌─ confirm (Mgr, before start) ─▶ confirmed ─ done (booker/Mgr, after end) ─▶ completed
requested ──┤                                     │
            ├─ reject (Mgr) ─▶ rejected           └─ cancel ─▶ cancelled
            └─ cancel ─▶ cancelled
```

- **Rejected and Cancelled are separate states**, so the record shows who ended the booking without needing a reason field.
- **Rejected, Cancelled and Completed are final.** Nothing can be reopened; the user makes a new booking.
- Only `requested` and `confirmed` block slots (see ADR-0002).

### Enforcement

- One dictionary defines every allowed transition:
  ```python
  _TRANSITIONS = {
      'requested': {'confirmed', 'rejected', 'cancelled'},
      'confirmed': {'completed', 'cancelled'},
  }
  ```
- All buttons and the Tier 2 cron call one `_set_state(target)` method. It checks the transition, then the role and time rules below.
- `state` is read-only in views. `write()` is **not** overridden, so the ORM and tests aren't obstructed.

### Approval

- Each resource has `requires_approval` (Boolean, off by default).
  - **Off:** a booking that passes the conflict and availability checks is created as **Confirmed**.
  - **On:** it is created as **Requested** and waits for a Manager.
- **Managers' bookings are always confirmed immediately**, including ones they make for other users.
- **Changing `requires_approval` affects only new bookings.**

### Who can do what, and when

| Action | Who | Allowed from | Time rule |
|---|---|---|---|
| Confirm | Manager | Requested | Before start |
| Reject | Manager | Requested | — |
| Cancel | Booker | Requested, Confirmed | Before start |
| Cancel | Manager | Requested, Confirmed | Before end |
| Mark as done | Booker or Manager | Confirmed | After end |

### Editing active bookings

- The time or resource can only be changed while the booking is **active and before its start**. The conflict and availability checks run again.
- If the (new) resource requires approval and the editor isn't a Manager, a Confirmed booking **goes back to Requested**. This stops a user from getting a slot approved and then moving it.
- Editing only the name or description never changes the state.

### Tier 2 (designed in Session 6)

- A cron auto-completes Confirmed bookings after they end.
- A cron auto-cancels Requested bookings whose start has passed without a decision.

## Alternatives considered

| Option | Why rejected |
|---|---|
| 4 states, with rejection folded into Cancelled | Loses who ended the booking unless a reason field is added |
| Approval for every booking | Managers become a bottleneck for routine rooms |
| No approval at all | Requested would be a state that never does anything |
| Override `write()` to block every direct state change | Gets in the way of the ORM, data imports and tests; the read-only field plus one method is enough |
| Allow resetting final states to Requested | Would need another conflict check and muddy the history; a new booking is cheap |
| Re-apply an approval-flag change to existing bookings | Same reasoning as ADR-0001: check when saved, not retroactively |

## Consequences

- Tests must cover:
  - Every disallowed transition raises an error
  - The role and time rules in the table above
  - Auto-confirm when approval is off, and Manager auto-confirm when it's on
  - Moving a Confirmed booking on an approval resource sends it back to Requested
  - Confirming after the start time is rejected
- Until the Tier 2 cron exists, undecided requests whose start has passed stay in Requested. They hold a slot that's already in the past, which is harmless.
