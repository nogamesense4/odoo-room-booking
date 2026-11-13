# 03: Book a resource (happy path)

**What to build:** A User books a resource for themselves; with no approval required the booking is Confirmed straight away and appears in the default bookings list (Upcoming filter, sorted by start, state badges). Booking fields per ADR-0002 (state field carries all five states from ADR-0003, even if only some are reachable yet). Security per ADR-0004: Users read all bookings, write only their own, cannot delete; only Managers book for someone else.

**Blocked by:** 02

**Status:** ready-for-agent

- [ ] User creates a booking → Confirmed; it shows in the Upcoming list
- [ ] End must be after start; start in the past is rejected (create and move)
- [ ] User cannot edit someone else's booking, cannot delete, cannot set "booked for" to another user
- [ ] Manager can book for another user
- [ ] Tests cover all of the above with `with_user()`
