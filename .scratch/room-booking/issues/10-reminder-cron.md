# 10: Reminder cron

**What to build:** Bookers of Confirmed bookings get one reminder before the start; lead time is an admin-changeable system parameter (default 60 minutes). Moving the booking re-arms the reminder. Requested bookings are never reminded. See ADR-0006.

**Blocked by:** 08

**Status:** ready-for-agent

- [ ] Reminder sent once inside the window; not sent twice
- [ ] Changing the start time re-arms the reminder
- [ ] Requested bookings get no reminder
- [ ] Lead time read from the system parameter
- [ ] Tests call the cron method directly
