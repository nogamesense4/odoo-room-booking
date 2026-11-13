# 06: Lifecycle and approval

**What to build:** The full booking lifecycle and per-resource approval from ADR-0003, enforced on the server. One transition table checked by a single state-change method; buttons shown only when role and state allow. Resources flagged for approval leave bookings Requested until a Manager confirms or rejects; Managers' own bookings confirm immediately. Moving an approval-resource booking (non-Manager) sends it back to Requested. Managers can delete only Rejected/Cancelled bookings; resources with future active bookings can't be archived. Form has a status bar; Managers get a To Approve menu.

Transition table (from ADR-0003):

    requested -> confirmed | rejected | cancelled
    confirmed -> completed | cancelled
    rejected, cancelled, completed -> (final)

**Blocked by:** 03

**Status:** ready-for-agent

- [ ] Every disallowed transition raises an error
- [ ] Confirm/reject Manager-only, and confirm not after start
- [ ] Cancel: booker before start, Manager before end; Mark as done: after end
- [ ] Approval flag off → auto-confirm; on → Requested; Manager → auto-confirm
- [ ] Moving a Confirmed approval-resource booking returns it to Requested
- [ ] Delete only Rejected/Cancelled, even for Managers
- [ ] Archiving a resource with future active bookings is blocked
- [ ] To Approve menu lists Requested bookings for Managers
