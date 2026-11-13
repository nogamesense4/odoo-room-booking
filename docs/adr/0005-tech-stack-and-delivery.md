# ADR-0005: Tech stack and delivery

**Status:** Accepted, 9 Nov 2026

## Context

Reviewers will clone a public GitHub repo and should be able to run the module in about two minutes. The brief requires an Odoo module but doesn't name a version.

## Decision

1. **Odoo 18.0 Community + PostgreSQL 16**, with pinned Docker tags (`odoo:18.0`, `postgres:16`).
   - 18 is stable, supported and well documented. Because most online material covers 17/18, AI tools are less likely to mix up APIs.
   - On Odoo 19, the exclusion constraint (ADR-0002) would move from `_sql_constraints` to `models.Constraint`.
   - If the company names a version, that version wins.
2. **Repo layout:** the repo root is the addons folder.
   ```
   README.md  PLAN.md  docker-compose.yml
   docs/adr/
   room_booking/   __manifest__.py, models/, security/, views/, data/, demo/, tests/
   ```
3. **Running it:** `docker-compose.yml` mounts the repo at `/mnt/extra-addons` and runs `-d booking -i room_booking`, so the first `docker compose up` creates the database and installs the module.
4. **Demo data** (`demo/`):
   - An "Office hours" calendar (Mon–Fri 9–12 and 13–18) plus one public-holiday leave
   - 3 rooms (the Boardroom has `requires_approval`), plus Projector 1 and a Camera (`requires_approval`)
   - Demo users "Booking User" and "Booking Manager", with test passwords documented in the README
   - Bookings in every state, dated relative to today
5. **Tests:** `TransactionCase` classes in `room_booking/tests/` (`test_conflict.py`, `test_availability.py`, `test_lifecycle.py`, `test_security.py`), built from the checklists in ADR-0001 to 0004.
   - They run with one documented `--test-tags /room_booking --stop-after-init` command.
   - Rules that depend on the time use relative dates, or `freezegun` if it's available.
6. **No CI pipeline.** Tests run through the documented command.
7. **AI use is disclosed in the README** ("How I used AI"), with no per-commit tags. Commits that touch the core logic get descriptive messages.

## Alternatives considered

| Option | Why rejected |
|---|---|
| Odoo 17 | Older, and support ends sooner |
| Odoo 19 | Newer APIs with less online material; AI tools are more likely to mix old and new APIs |
| Module nested inside an `addons/` subfolder | One more level of nesting for no benefit |
| Manual install steps instead of auto-install | Makes reviewers do the setup work; risk they never see it run |
| GitHub Actions CI | Setting up Odoo and Postgres in CI takes time and doesn't add to what's graded |
| Per-commit AI tags | Noise; the README section is clearer |

## Consequences

- Confirmed during setup (13 Nov): Odoo 18 loads demo data by default, so no extra flag is needed; `freezegun` 1.2.1 ships in the `odoo:18.0` image, so time-dependent tests can freeze time.
- `btree_gist` is part of the standard contrib extensions in the `postgres:16` image.
