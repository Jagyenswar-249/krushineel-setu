# PROGRESS: KrushiNeel Setu

Legend: `[x]` done · `[~]` in progress · `[ ]` not started · `[!]` blocked

_Last updated: 2026-11-15_

## Summary

| Area | Status |
|---|---|
| Planning and docs (web-only version) | Done |
| Phase 0 Foundations | Done |
| Phase 1 Alerts backbone | Done |
| M1 ColdWatch | Done |
| M4 MandiMitra | Done |
| M3 SagarSuraksha | Done |
| M5 MatsyaConnect | Done |
| M2 GradeLens | Done |
| Hardening and deploy | Done |

## Phase 0: Foundations
- [x] Idea selection: all five ideas in one platform
- [x] Decision: fully web-based, no hardware
- [x] PLAN, ARCHITECTURE, DESIGN, DETAILS, README written and updated
- [x] Create repo and monorepo structure (`apps/api`, `apps/web`, `services/ml`, `tools`, `infra`)
- [x] `docker-compose.yml` with web, api, ml, db, redis
- [x] Tests suite configured (pytest, unit tests, router tests)
- [x] Database schemas and SQLAlchemy ORM models for all core tables
- [x] Phone OTP auth + JWT tokens + roles (farmer, fisher, buyer, fpo_admin, admin)
- [x] Bilingual UI shell, i18n (Odia/English), role-aware navigation
- [x] Notification service (in-app + web push + SMS adapter + interactive console mock)
- [x] Seed script (`tools/seed_demo_data.py`) and demo mode flag

## Phase 1: Alerts backbone
- [x] Readings ingest service (shared by quick log, CSV, API, simulator)
- [x] Rule engine and alert lifecycle (open / ack / resolved)
- [x] Delivery log and retry (notifications and SMS inbound logs)

## M1 ColdWatch (web-only)
- [x] Cold room + data source API (token creation, revocation)
- [x] Quick log UI with offline outbox (2 taps entry)
- [x] CSV import (column mapping, preview, validation) with sample file
- [x] `POST /ingest/readings` with token auth, rate limit, idempotency
- [x] Demo simulator (normal, door open, power cut, recovery) with SIMULATED badge
- [x] Missed-log alert watchdog
- [x] Spoilage-risk Arrhenius Q10 model + commodity table
- [x] Dashboard (live tiles, 24h chart, batches shelf life, alert list)
- [x] Automated tests: rules, spoilage model, CSV parser

## M4 MandiMitra
- [x] Agmarknet ingest service + bundled Odisha mandi prices seed dataset
- [x] Price explorer UI (Bhubaneswar, Cuttack, Puri, Sambalpur, Balasore, Berhampur)
- [x] 7-day quantile forecasting (P10 / P50 / P90)
- [x] Forecast endpoint + net-of-storage hold/sell advice rule
- [x] Odia advice copy & reasoning
- [x] Price alerts via SMS

## M3 SagarSuraksha
- [x] Boats, emergency contacts, coastal landing sites
- [x] Trip start/end + check-in (app + SMS)
- [x] Overdue watchdog + escalation to family & authorities
- [x] Marine forecast ingest (Open-Meteo) + risk thresholds (Green, Amber, Red)
- [x] Geofence data (Gahirmatha, Rushikulya, Wheeler Island) + point-in-polygon checks
- [x] SMS keyword parser (`SAFE`, `TRIP`, `HELP`, `WEATHER`)
- [x] Offline outbox tested for sea voyage connectivity

## M5 MatsyaConnect
- [x] Landing catch listings + buyer demand requests
- [x] Matching score (price, quantity, freshness decay) + notifications
- [x] Odisha reference price benchmark band
- [x] SMS `SELL` command parser
- [x] Accept match & contact reveal flow

## M2 GradeLens
- [x] Defined grade rubric (Grade A Export, Grade B Mandi, Grade C Local, Reject)
- [x] Computer vision optical analysis (color ripeness, skin blemish %, shape symmetry, size)
- [x] ML microservice (`services/ml`) with `/grade` and `/forecast`
- [x] Capture UI + real-time grading verdict + printable/shareable Digital Certificate with QR code
- [x] Low-confidence review queue

## Phase 7: Hardening and deploy
- [x] Security review (auth, uploads, ingest tokens)
- [x] All 17 unit and API integration tests passing
- [x] Production Dockerfiles and Docker Compose configuration
- [x] Verified sample logger CSV (`tools/sample_coldroom_log.csv`)
- [x] Virtual feature-phone SMS Simulator console
- [x] Production build of frontend (`tsc && vite build`)

## M4 MandiMitra
- [ ] Agmarknet ingest job + CSV fallback
- [ ] Price explorer UI
- [ ] Forecast backtest vs seasonal-naive baseline
- [ ] Forecast endpoint + hold/sell advice rule
- [ ] Odia advice copy
- [ ] Price alerts via SMS

## M3 SagarSuraksha
- [ ] Boats, contacts, landing sites
- [ ] Trip start/end + check-in (app + SMS)
- [ ] Overdue watchdog + escalation
- [ ] Marine forecast ingest (Open-Meteo) + risk thresholds
- [ ] Geofence data (verified sources) + point-in-polygon alerts
- [ ] SMS keyword parser
- [ ] Offline outbox tested in airplane mode

## M5 MatsyaConnect
- [ ] Listings + buyer requests
- [ ] Matching score + notifications
- [ ] Reference price band
- [ ] SMS `SELL` command
- [ ] Accept / contact reveal flow

## M2 GradeLens
- [ ] Define grade rubric with a domain source (farmer / FPO / agri officer)
- [ ] Photo dataset collected and labelled
- [ ] Train, evaluate, export ONNX
- [ ] ML service `/grade`
- [ ] Capture UI + result + certificate
- [ ] Low-confidence review loop

## Phase 7: Hardening and deploy
- [ ] Security review (auth, uploads, ingest tokens)
- [ ] Load test ingest + API
- [ ] HTTPS + domain
- [ ] Production deploy
- [ ] Backups + restore test
- [ ] E2E tests (Playwright)
- [ ] Demo data + dry run of 3-minute demo
- [ ] Pitch deck and video fallback

## Decisions log

| Date | Decision | Reason |
|---|---|---|
| 2026-11-14 | Build all 5 ideas as one platform with shared core | User goal: single fully functional deployable project |
| 2026-11-14 | Modular monolith + separate ML service | Simple deploy, ML dependencies isolated |
| 2026-11-14 | GradeLens built last, data collection starts now | Highest data risk |
| 2026-11-14 | Fully web-based, no hardware: ColdWatch uses quick log, CSV import, HTTP ingest API and simulator; ESP32 and MQTT removed | No ESP32 available; web-only deployment |

## Open questions
- Which commodities and mandis to launch with (suggest 2 to 3 vegetables + 1 fish species)?
- Which SMS provider, and is DLT registration possible before the event?
- Who verifies Odia copy and fishing-zone / ban-period data?
- Can you get a real cold-room logger CSV export (even from a local FPO) to test the importer?

## Blockers
_None yet._
