# 02: Managers manage resources

**What to build:** Managers create and edit rooms and equipment under Configuration: name, type, capacity (rooms only), working-hours calendar (required, defaults to company hours), approval flag, description, active. Users can read resources but not change them. Demo data includes the "Office hours" calendar (with lunch break and one public holiday) and sample resources. See ADR-0001, ADR-0004.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] Manager can create/edit/archive a resource; User can only read
- [ ] Capacity shown only for rooms
- [ ] Demo calendar and resources load
- [ ] Access test: User cannot write to resources
