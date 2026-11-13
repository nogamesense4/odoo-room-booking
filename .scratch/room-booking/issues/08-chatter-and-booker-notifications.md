# 08: Chatter and booker notifications

**What to build:** Every booking has chatter recording changes to state, resource, booked-for, start and end. The booker follows their booking automatically and gets a message when it is confirmed, rejected or cancelled. Covers brief rule 1 (integration with a core module). See ADR-0006.

**Blocked by:** 06

**Status:** ready-for-agent

- [ ] Tracked field changes appear in chatter with author and time
- [ ] Booker is a follower on create (including when a Manager books for them)
- [ ] Confirm, reject and cancel each post a message to the booker
- [ ] Tests for follower and messages
