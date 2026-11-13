# ADR-0006: Additional features

**Status:** Accepted, 12 Nov 2026

## Context

The brief asks for features that give real value to users and cover at least one of three rules: (1) integration with an Odoo core module, (2) an AI feature, (3) automation or scheduled logic. Covering more rules earns extra credit. Time is limited (see PLAN.md), so this covers **rules 1 and 3**. Rule 2 is optional (Tier 3).

## Decision

### Rule 1: integration with `mail` (chatter, followers, activities)

- `booking.booking` inherits `mail.thread` and `mail.activity.mixin`.
- `tracking=True` on `state`, `resource_id`, `user_id`, `start_datetime` and `end_datetime`, so every change is logged with who made it and when. This backs up "cancel instead of delete" (ADR-0004).
- The booker's partner (from `user_id`) is added as a follower automatically.
- Confirm, reject and cancel each post a message to the booker through `message_post`, which shows up in their inbox (and is emailed if outgoing mail is configured).
- Together with `user_id` → `res.users`, this links bookings to Users and Discuss.

### Rule 3: scheduled jobs (`ir.cron`)

| Cron | Interval | What it does |
|---|---|---|
| **Housekeeping** | 15 min | (a) Confirmed with `end ≤ now` → **Completed**. (b) Requested with `start ≤ now` → **Cancelled**, with a chatter note "cancelled automatically: no decision before start" |
| **Reminders** | 15 min | Confirmed bookings starting within `room_booking.reminder_minutes` (system parameter, default 60) and with `reminder_sent = False` → post a reminder to the booker and set `reminder_sent = True` |

- `reminder_sent` resets whenever `start_datetime` changes, so a moved booking gets a fresh reminder.
- Requested bookings are never reminded, since they may not happen.
- Because the cron runs every 15 minutes, a reminder may arrive up to 15 minutes late. A booking made inside the reminder window is reminded on the next run.

### What the system is allowed to do

Crons run as the superuser. When `self.env.su` is true, `_set_state()` **skips the role and time checks** but **always applies the transition table** (ADR-0003). The system is a separate actor with its own limits: it can complete or cancel bookings, but it can't make a transition the table doesn't allow. Users can't reach `env.su` through the UI.

## Alternatives considered

| Option | Why rejected |
|---|---|
| Create a `calendar.event` from each booking | Syncing one way raises a two-way question (what if someone moves the event?). The module's own calendar view covers the visual need. **Next step.** |
| Attendees + checking room capacity | One more field and constraint plus more tests, and it doesn't help with any rule. `capacity` stays display-only |
| No-show auto-cancel | There's no check-in data, so the system can't tell who didn't turn up; guessing would cancel real meetings |
| One combined cron | Two crons can each be tested and switched off on their own |
| Hard-coded reminder lead time | A system parameter lets offices change it without editing code |
| Remind Requested bookings too | Misleading, since they may be rejected |
| An AI feature now (rule 2) | Only if Tier 2 is tested and committed by Sat 14 Nov. Otherwise it's a next step: "suggest the nearest free slot or a similar free resource when a booking conflicts" |

## Consequences

- New dependency: `mail`.
- New fields: `reminder_sent` (Boolean); a system parameter in `data/`.
- Tests call `_cron_housekeeping()` and `_cron_send_reminders()` directly, with relative dates or frozen time:
  - Ended Confirmed bookings → Completed
  - Leftover Requested bookings → Cancelled, with a chatter note
  - A reminder is sent once, and again after the booking is moved
  - Requested bookings get no reminder
  - Followers and messages: the booker follows and receives decision messages
