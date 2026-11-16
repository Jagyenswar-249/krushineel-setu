# PLAN: KrushiNeel Setu

## 1. Goal

Ship one fully functional, deployable platform covering all five ideas from the theme (solar cold-room monitor, vegetable grading, fisherfolk safety alert, mandi price advisor, catch-to-market matching), usable by low-connectivity, Odia-speaking users.

## 2. Strategy: shared core, thin modules

Five products would be five times the work if built separately. They are not, because they share:

| Shared piece | Used by |
|---|---|
| Auth (phone + OTP), roles | all |
| Notification engine (push + SMS) | ColdWatch, SagarSuraksha, MandiMitra, MatsyaConnect |
| Offline sync (IndexedDB queue) | SagarSuraksha, MatsyaConnect, GradeLens |
| Time-series + alert rules | ColdWatch, SagarSuraksha |
| Price data and forecasting | MandiMitra, MatsyaConnect, GradeLens (price context) |
| Odia / English UI kit | all |

So the order is: **core platform first, then modules**, each module a vertical slice (DB, API, UI, SMS path, tests).

## 3. Scope per module (MVP = "fully functional")

### M1 ColdWatch (web-only, no hardware)
- Register cold rooms and data sources (manual log, CSV import, HTTP ingest API, demo simulator).
- Staff log temperature/humidity in two taps; CSV import for exports from any existing thermometer or logger; token-protected `POST /ingest/readings` so any future sensor or script can push data.
- Rules: out-of-range for N minutes, rapid rise, missed-log reminder (no reading for too long).
- Spoilage-risk score per stored batch (commodity table + temperature history).
- Dashboard: live tile per room, 24h chart, alert list. SMS + push on alert.

### M2 GradeLens
- Upload / capture photo, choose commodity, get grade (A/B/C/reject) with confidence.
- Store result with image hash and timestamp; shareable grade certificate (QR / link).
- FPO can bulk-grade a lot (sample N photos, aggregate).
- Low-confidence results are flagged for manual review and fed back as training data.

### M3 SagarSuraksha
- Fisher registers boat and emergency contacts; start / end trip.
- Periodic check-in (button or SMS); missed check-in escalates.
- Marine weather risk (wave, wind, forecast) per landing site / current position, shown as green / amber / red in Odia.
- Geofence alerts (restricted zones, seasonal bans) from GPS where available.
- SMS-first path: `SAFE`, `TRIP`, `HELP` keywords; works with no app.

### M4 MandiMitra
- Daily ingest of mandi prices (Agmarknet) for chosen crops and Odisha mandis.
- Trend view, 7-day forecast with error band, hold / sell hint with plain reasoning in Odia.
- Net-of-storage-cost logic (ties to ColdWatch if the user has a cold room).
- Price alerts by SMS ("tomato at Bhubaneswar above X").

### M5 MatsyaConnect
- Fisher lists landing: species, quantity, landing site, expected price, photo.
- Buyers post demand (species, quantity, radius, price band).
- Matching engine scores and notifies both sides; contact reveal on accept.
- Reference price band from recent landing / market data to reduce cheap distress sales.
- SMS listing: `SELL <species> <kg> <price> <site>`.

## 4. Phases (order of work, no time estimates)

**Phase 0: Foundations**
Repo, Docker Compose, CI, DB migrations, auth, roles, i18n, PWA shell, notification service, SMS adapter + mock, seed script.

**Phase 1: Data and alerts backbone**
Readings ingest (quick log, CSV, HTTP API), readings table, rule engine, alert lifecycle (open, ack, resolved), push + SMS delivery log.

**Phase 2: M1 ColdWatch** (logging UI, CSV import, ingest API, simulator, dashboard)

**Phase 3: M4 MandiMitra** (ingest, forecasting, advisor, SMS alerts)

**Phase 4: M3 SagarSuraksha** (trips, check-ins, weather risk, geofences, SMS keywords)

**Phase 5: M5 MatsyaConnect** (listings, buyers, matching, notifications)

**Phase 6: M2 GradeLens** (dataset collection, training, ONNX service, UI)
Placed last because it carries the most data risk. Start photo collection in Phase 0 in parallel.

**Phase 7: Hardening and deploy**
Load test, security pass, backups, HTTPS, monitoring, production deploy, demo data, pitch.

## 5. Deliverables checklist

- [ ] Running deployed URL (HTTPS)
- [ ] Public repo with README and docs
- [ ] ColdWatch demo using the built-in simulator, clearly labelled as simulated
- [ ] Trained grading model with reported metrics
- [ ] Forecast backtest with reported error vs baseline
- [ ] SMS demo path (mock or real)
- [ ] 3-minute demo script and pitch deck
- [ ] Architecture diagram in the deck

## 6. Team roles (adapt to your team)

| Role | Owns |
|---|---|
| Backend lead | API, DB, rules engine, SMS, deploy |
| Frontend lead | PWA, offline sync, i18n, design |
| ML / data | grading model, forecasting, data collection |
| Data / integrations | ColdWatch ingest API, CSV import, simulator, mandi and weather ingest |
| Pitch / field | user interviews, demo script, deck, Odia copy review |

A solo builder should follow the phase order strictly and cut M2 depth first.

## 7. Risk register

| Risk | Impact | Mitigation |
|---|---|---|
| No labelled vegetable photos | M2 weak | Collect early at a local market; 150+ photos per class per commodity; start with 1 to 2 commodities; use transfer learning and augmentation |
| Agmarknet API limits / downtime | M4 stale | Cache daily, bundled CSV fallback |
| SMS provider needs DLT registration | No real SMS | Adapter pattern; mock for demo; register early if going live |
| Simulated or manual data mistaken for live sensors | Misleading demo, lost trust | SIMULATED badge on every simulated reading; say so in the pitch; ingest API ready for real loggers |
| Manual logging is skipped by staff | ColdWatch has gaps | Missed-log alerts, two-tap log, SMS reminders |
| Scope too wide | Everything shallow | Vertical slices; each module demoable on its own; cut order below |
| Poor connectivity at venue | Live demo fails | Offline-capable PWA, local Docker demo environment |
| Safety claims overreach | Trust / liability | Clear "supplements official warnings" notice in UI and pitch |

**Cut order if forced:** GradeLens depth, then MatsyaConnect matching sophistication, then geofences. Never cut: core, ColdWatch, SagarSuraksha check-in.

## 8. Definition of "fully functional"

A module counts as done when: a real user flow works end to end on the deployed app, data persists, errors are handled, it works in Odia, it has an SMS or offline path where relevant, and it has automated tests for core logic.
