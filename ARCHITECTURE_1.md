# ARCHITECTURE: KrushiNeel Setu

## 1. Style

Fully web-based modular monolith (FastAPI) + a separate ML service + a background worker. One repo, one database, no hardware or device broker. Modules are Python packages with their own routers, models and services, communicating through service interfaces and an internal event bus. This keeps deployment simple while allowing a module to be split out later.

## 2. System diagram

```
 ┌──────────────┐   HTTPS    ┌───────────────────────────────────────────────┐
 │  PWA (React) │◀──────────▶│                FastAPI (apps/api)             │
 │ offline queue│            │  auth │ coldwatch │ gradelens │ sagar │ mandi │
 └──────┬───────┘            │  matsya │ notify │ ingest │ admin             │
        │ Web Push           └───┬───────────┬──────────────┬────────────────┘
        │                        │           │              │
 ┌──────┴───────┐          ┌─────▼────┐  ┌───▼────┐   ┌─────▼──────────┐
 │ SMS users    │◀────────▶│ SMS      │  │ Redis  │   │ PostgreSQL     │
 │ (feature ph.)│   SMS    │ gateway  │  │ queue/ │   │ (+ object      │
 └──────────────┘          │ adapter  │  │ cache  │   │ store for imgs)│
                           └──────────┘  └───┬────┘   └────────────────┘
 Other readings sources                      │
 (CSV upload, any logger/script        ┌─────▼──────────┐        ┌───────────────┐
  via POST /ingest/readings, ────────▶ │ Worker (RQ):   │───────▶│ ML service    │
  demo simulator)                      │ rules, ingest, │  HTTP  │ grading ONNX, │
                                       │ simulator,     │        │ forecasting   │
                                       │ matching, send │        └───────────────┘
                                       └────────────────┘
                External: Open-Meteo (weather + marine), data.gov.in (Agmarknet)
```

## 3. Components

| Component | Tech | Responsibility |
|---|---|---|
| `apps/web` | React, Vite, TS, Tailwind, Workbox | UI, offline cache, queued writes, push subscription |
| `apps/api` | FastAPI, SQLAlchemy, Alembic | REST API, auth, business logic, SMS webhook, ingest endpoint |
| `worker` | Python, RQ (Redis) | Scheduled ingest, rule evaluation, simulator, notification delivery, matching |
| `services/ml` | FastAPI, ONNX Runtime, LightGBM | `/grade`, `/forecast` endpoints |
| Postgres | 15+ | System of record |
| Redis | 7 | Job queue, rate limits, short caches |
| Object storage | S3-compatible or local volume | Grading images |

## 4. Data model (core tables)

```
users(id, phone, name, role, language, district, created_at)
otp_codes(id, phone, code_hash, expires_at, attempts)
organizations(id, name, type[fpo|coop|buyer_firm], district)
memberships(user_id, org_id, role)

-- ColdWatch
cold_rooms(id, org_id, name, location, capacity_kg, min_temp, max_temp, max_rh, log_interval_min)
data_sources(id, cold_room_id, kind[manual|csv|api|simulated], token_hash, last_seen_at)
sensor_readings(id, cold_room_id, source_id, ts, temp_c, rh, entered_by, is_simulated)  -- indexed (cold_room_id, ts)
batches(id, cold_room_id, commodity, qty_kg, stored_at, owner_id, shelf_life_days_ref)
spoilage_scores(batch_id, ts, risk_pct, remaining_days)
alert_rules(id, scope, kind, params_json)
alerts(id, kind, severity, subject_type, subject_id, opened_at, acked_at, resolved_at, payload)

-- GradeLens
grading_requests(id, user_id, commodity, image_key, image_sha256, created_at)
grading_results(id, request_id, grade, confidence, model_version, needs_review, reviewed_grade)

-- SagarSuraksha
boats(id, owner_id, reg_no, name, landing_site_id, crew_size)
emergency_contacts(id, user_id, name, phone, kind[family|fisheries|coastguard])
landing_sites(id, name, district, lat, lon)
trips(id, boat_id, departed_at, expected_return_at, status, checkin_interval_min)
checkins(id, trip_id, ts, lat, lon, source[app|sms], note)
geofences(id, name, kind[restricted|seasonal_ban|boundary], polygon_geojson, active_from, active_to)
marine_forecasts(id, site_id, ts, wave_m, wind_kmh, gust_kmh, risk_level)

-- MandiMitra
mandis(id, name, district, lat, lon)
commodities(id, name_en, name_or, category[veg|paddy|fish])
mandi_prices(id, mandi_id, commodity_id, date, min_price, max_price, modal_price, arrivals)
price_forecasts(id, mandi_id, commodity_id, made_on, horizon_days, p10, p50, p90, model_version)
price_alerts(id, user_id, mandi_id, commodity_id, direction, threshold)

-- MatsyaConnect
catch_listings(id, fisher_id, site_id, species, qty_kg, ask_price, photo_key, status, created_at, expires_at)
buyer_requests(id, buyer_id, species, qty_kg, max_price, radius_km, status)
matches(id, listing_id, request_id, score, status[proposed|accepted|declined|expired])

-- Platform
notifications(id, user_id, channel[push|sms], template, payload, status, sent_at, error)
sms_inbound(id, from_phone, body, parsed_command, handled_at)
audit_log(id, user_id, action, entity, entity_id, ts)
```

## 5. API surface (v1, representative)

```
POST /auth/otp/request          POST /auth/otp/verify        GET /me

POST /coldrooms                 GET  /coldrooms/{id}/readings?from&to
POST /coldrooms/{id}/readings   (manual quick log)
POST /coldrooms/{id}/import     (CSV upload with column mapping + preview)
POST /coldrooms/{id}/sources    (creates an API source and shows its token once)
POST /ingest/readings           (header X-Source-Token; JSON array; idempotent)
GET  /coldrooms/{id}/alerts     POST /alerts/{id}/ack
POST /batches                   GET  /batches/{id}/risk
POST /admin/simulator/start     POST /admin/simulator/scenario   (demo mode only)

POST /grading                   (multipart image + commodity)  GET /grading/{id}
GET  /grading/{id}/certificate

POST /boats   POST /trips   POST /trips/{id}/checkin   POST /trips/{id}/end
GET  /sites/{id}/marine-risk    GET /geofences?bbox=
POST /sms/inbound               (provider webhook)

GET  /prices?mandi&commodity&from&to
GET  /advice/sell-hold?mandi&commodity&qty&storage_cost
POST /price-alerts

POST /listings   GET /listings?species&site&radius
POST /buyer-requests   GET /matches   POST /matches/{id}/accept

GET  /notifications   POST /push/subscribe
GET  /admin/stats
```

### Ingest payload

```json
POST /ingest/readings
X-Source-Token: <token>
[{"ts": "2026-11-14T10:15:00+05:30", "temp_c": 4.2, "rh": 88, "id": "optional-idempotency-key"}]
```

Rate limited per source; timestamps in the future or far past are rejected; duplicates are ignored by key.

## 6. ColdWatch data intake (no hardware)

| Route | Who | Notes |
|---|---|---|
| Quick log | Cold-room staff | Two taps; offline-capable via outbox; entered_by recorded |
| CSV import | FPO manager | Upload, map columns, preview, validate units and timestamps, then commit |
| HTTP ingest API | Any script / future logger | Token per source; hardware-agnostic |
| Simulator | Demo and tests | Worker generates readings per scenario (normal, door left open, power cut); rows flagged `is_simulated` and badged in UI |

Because intake can be human, the rule set adds a **missed-log** alert (no reading within `log_interval_min` plus grace).

## 7. Key algorithms

### 7.1 ColdWatch spoilage risk
- Each commodity has `optimal_temp_range`, `reference_shelf_life_days` (from a sourced table you maintain).
- Ageing rate multiplier per interval: `Q10 ^ ((T - T_ref) / 10)` with Q10 around 2 to 3, clamped to 1 inside the optimal range.
- `consumed_life += multiplier * dt / shelf_life_ref`; `remaining_days = (1 - consumed_life) * shelf_life_ref`.
- Gaps between readings are interpolated carefully and flagged as lower confidence when the gap is long.
- Risk % rises as consumed life approaches 1 and when humidity is out of range.
- Alerts: out-of-range for N min, rate-of-rise, missed log, source stale.

### 7.2 GradeLens
- Transfer learning from MobileNetV2 (ImageNet), fine-tuned per commodity on your labelled photos.
- Preprocessing: resize, colour normalization, optional OpenCV background crop.
- Output: grade + softmax confidence; below threshold means `needs_review`.
- Export to ONNX, served by the ML service on CPU.
- Report per-class precision / recall on a held-out set.

### 7.3 SagarSuraksha risk and escalation
- Risk level from marine forecast thresholds (wave height, wind, gust) configured by district; red blocks "safe to sail" messaging and sends alerts to registered fishers at the site.
- Check-in watchdog: if `now > last_checkin + interval + grace`, state goes `overdue`, then notify contacts, then fisheries officer contact (configurable) as `escalated`.
- Position comes from the browser Geolocation API when permitted; geofence test is point-in-polygon (Shapely) against active polygons; seasonal bans use date windows.

### 7.4 MandiMitra forecasting and advice
- Features: lags, rolling means, day-of-week, month, arrivals, rainfall (optional).
- Models: seasonal-naive baseline and LightGBM; quantile outputs for p10/p50/p90.
- Backtest with rolling origin; ship only if it beats baseline on MAPE; otherwise show trend only.
- Advice rule: `hold` if `E[p50 at horizon] - today - storage_cost - spoilage_loss > margin`, else `sell`. Always show the reasoning and the uncertainty band.

### 7.5 MatsyaConnect matching
- Score = weighted sum of: price fit, quantity fit, distance (haversine), freshness (hours since landing).
- Hard filters first (species, radius, status), then rank; Hungarian assignment when many-to-many conflicts.
- Notify top K buyers; reveal contacts only after mutual accept.

## 8. Offline and SMS design

- **PWA:** service worker caches shell and last data; writes (check-in, listing, reading log) go to an IndexedDB outbox, synced with background sync and idempotency keys.
- **SMS:** inbound webhook parses fixed keyword grammar in English or transliterated Odia; every command returns a short confirmation. Outbound templates are under 160 chars (GSM-7) or sized for Unicode (Odia uses UCS-2, so ~70 chars per segment).

## 9. Security and privacy

- Phone OTP login with rate limiting and attempt caps; short-lived JWT + refresh.
- Role-based access (farmer, fisher, buyer, FPO admin, platform admin).
- Ingest tokens hashed at rest, shown once, revocable; per-source rate limits.
- CSV and image uploads: type/size validation, random keys, no public bucket.
- Location data minimised; trip location visible only to the fisher and chosen contacts.
- Audit log for admin and escalation actions; secrets via env, never committed.

## 10. Deployment

- `docker-compose.yml`: `web`, `api`, `worker`, `ml`, `db`, `redis`, `nginx`.
- Production: single VPS with Caddy/Nginx + Let's Encrypt, or Render/Fly for api/web/ml/worker with managed Postgres and Redis.
- CI: lint, unit tests, build images; CD on tag.
- Backups: nightly `pg_dump` to object storage; restore tested once.
- Observability: structured logs, `/healthz`, uptime check, Sentry (optional).

## 11. Testing strategy

| Level | Focus |
|---|---|
| Unit | spoilage model, geofence, matching score, SMS parser, advice rule, CSV parser |
| Integration | ingest to alert to notification; check-in watchdog; OTP flow |
| ML | held-out metrics, backtest report committed to `docs/` |
| E2E | Playwright: login, add cold room, run simulator scenario, receive alert |
| Manual | real phone, airplane-mode offline test, CSV from a real logger export |
