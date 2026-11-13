# Plan: Room & Equipment Booking OA

**Deadline:** submit the public GitHub link by **Sun 15 Nov 2026**.
**Budget:** about 15h over Mon 9 to Sat 14 Nov (2–3h/day). Exam revision comes first each day.
**Buffer:** Sun 15 Nov is for final checks and submitting only.

## Rules

1. Never start a tier until the previous one is **tested and committed**.
2. Commit each ADR **before** the code it describes; keep commits small, one per feature or decision.
3. Don't merge code I can't explain line by line. If an AI prompt misses twice, write that part myself.
4. Write the conflict, availability and lifecycle logic myself, or rework it heavily.

## Definition of done

- **Tier 1 (must ship, baseline pass)**
  - [ ] Resources with availability windows
  - [ ] Booking CRUD with access control (User / Manager groups, `ir.model.access` + `ir.rule`)
  - [ ] Conflict prevention for overlapping bookings on the same resource
  - [ ] Bookings respect availability windows
  - [ ] Lifecycle enforced by the system
  - [ ] List view as the default
  - [ ] Tests: overlap edge cases, availability boundaries, state transitions, access rules
  - [ ] docker-compose (Odoo + Postgres), demo data, README "How to run"
  - [ ] README: assumptions, out of scope, trade-offs, ADR links, How I used AI
- **Tier 2 (target = "done")**
  - [ ] Rule 1: chatter (`mail.thread`) + link to Users
  - [ ] Rule 3: cron reminder before start and/or no-show auto-cancel
  - [ ] Calendar view
- **Tier 3 (bonus, not planned for)**
  - [ ] Rule 2: an AI feature

## Sprint goals

| Day | Goal | Done when |
|---|---|---|
| **Mon 9** | Grilling sessions 2–5; write ADRs; get Odoo running in Docker | ADRs committed; an empty module installs |
| **Tue 10** | Models (resource, availability, booking) + security groups and rules | Records can be created as User and Manager with the right permissions |
| **Wed 11** | Conflict + availability constraints, with tests written first | Edge-case tests pass |
| **Thu 12** | Lifecycle + list view + demo data + docker-compose | **Tier 1 complete**, tested and committed |
| **Fri 13** | Grilling session 6; build Tier 2 | Chatter, cron and calendar view work and are tested |
| **Sat 14** | Tier 3 if there's time, otherwise polish. Self-review: explain every file out loud without the AI chat | README finished |
| **Sun 15** | Buffer: fresh clone, run from README, push, send link | Link sent |

## Grilling sessions

- [x] 1. Scope & assumptions
- [x] 2. Resources & availability windows → ADR-0001
- [x] 3. Booking model & conflict prevention → ADR-0002
- [x] 4. Lifecycle → ADR-0003
- [x] 5. Access control → ADR-0004
- [x] 6. Additional features → ADR-0006
- [x] 7. UX & views → README "Using the module"
- [x] 8. Delivery & testing → ADR-0005

## To confirm during setup (Tue 10)

- [x] Odoo 18 loads demo data by default (`--without-demo` defaults to none); no flag needed
- [x] `freezegun` 1.2.1 is available in the `odoo:18.0` image
- [x] The test command works (README updated)
- [x] Docker Desktop running
