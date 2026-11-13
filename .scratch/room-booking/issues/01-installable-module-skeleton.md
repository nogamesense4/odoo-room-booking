# 01: Installable module skeleton

**What to build:** A reviewer runs one command and gets Odoo 18 Community + PostgreSQL 16 with an empty "Room Booking" app installed, User and Manager groups defined, and a working test command (zero tests). Resolve the setup facts in PLAN.md (demo data loading by default, `freezegun` availability). See ADR-0005, ADR-0004 (groups).

**Blocked by:** None (can start immediately)

**Status:** done

- [x] `docker compose up` on a fresh clone installs the module into the `booking` database
- [x] Groups exist: Booking User (implied for every internal user) and Booking Manager (implies User; admin assigned)
- [x] The documented test command runs and exits cleanly
- [x] PLAN.md "to confirm" items answered and README updated
