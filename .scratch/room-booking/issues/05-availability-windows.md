# 05: Availability windows

**What to build:** A booking must fit inside one continuous working interval of its resource's calendar (in the calendar's time zone). Bookings outside hours, across lunch, overnight, or on a calendar-wide holiday are rejected with a clear message. No manager override. Checked on create and when time or resource changes only. See ADR-0001.

**Blocked by:** 03

**Status:** done

- [x] Booking exactly at window start/end allowed
- [x] Across lunch, overnight, multi-day, and on a holiday rejected
- [x] Manager is also blocked
- [x] Tests for each case above
