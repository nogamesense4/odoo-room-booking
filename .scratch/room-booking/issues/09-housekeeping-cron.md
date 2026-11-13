# 09: Housekeeping cron

**What to build:** Every 15 minutes the system completes Confirmed bookings that have ended and cancels Requested bookings whose start passed without a decision, leaving a chatter note. When running as the system, the state-change method skips role and time checks but always applies the transition table. Covers brief rule 3. See ADR-0006.

**Blocked by:** 08

**Status:** ready-for-agent

- [ ] Ended Confirmed → Completed
- [ ] Leftover Requested → Cancelled with a chatter note
- [ ] The system still cannot make a transition outside the table
- [ ] Tests call the cron method directly
