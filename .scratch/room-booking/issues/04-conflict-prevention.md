# 04: Conflict prevention

**What to build:** Overlapping active (Requested/Confirmed) bookings on the same resource are rejected with a message naming the conflicting booking (resource, time, who, state). Half-open intervals allow back-to-back bookings. A PostgreSQL exclusion constraint (`btree_gist`, `tsrange`, partial on active states) guarantees it even when two users save at once. See ADR-0002.

**Blocked by:** 03

**Status:** done

- [x] Partial overlap, containment and exact duplicate rejected; back-to-back allowed
- [x] Same time on a different resource allowed; Cancelled/Rejected/Completed don't block
- [x] Moving a booking re-checks others but not itself
- [x] Error message names the conflicting booking
- [x] Raw-SQL test proves the database rejects an overlap that bypasses Python
