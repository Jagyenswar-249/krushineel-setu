# DETAILS: Important notes for KrushiNeel Setu

## 1. Theme alignment

**Theme 3: Krushi & Neel Kranti (agriculture and fisheries).**
Scope: perishable produce, solar cold chains, coastal fisherfolk safety.
Ground problems addressed: post-harvest loss, no cold storage, harvest-time price crashes, fisherfolk going to sea without weather / boundary alerts, poor catch-price information.
Stakeholders: vegetable and paddy farmers, FPOs, fisherfolk in Puri, Ganjam, Kendrapara, Balasore, and Chilika communities.
The brief says to choose only what the evidence supports, so the pitch must show evidence per module (see section 9).

## 2. The five ideas and how they map

| # | Idea | Module | Feasibility / difficulty (from your table) | Commercial path |
|---|---|---|---|---|
| 1 | Cold-room monitor (web-only, no hardware) | ColdWatch | High / Medium | Subscription |
| 2 | Vegetable grading by phone camera | GradeLens | Medium (data risk) / High | Per-grade service to FPOs |
| 3 | Fisherfolk safety alert | SagarSuraksha | Medium / Medium | Government or cooperative contracts |
| 4 | Mandi price and sell-timing advisor | MandiMitra | High / Medium | Aggregator integration |
| 5 | Catch-to-market matching | MatsyaConnect | High / Low | Marketplace fee |

## 3. Cold-room data without hardware

No sensors are required. ColdWatch accepts data four ways:

| Route | Notes |
|---|---|
| Quick log | Staff enter temperature and humidity; reminders and a missed-log alert keep the record complete |
| CSV import | Works with exports from any thermometer or data logger; column mapping, preview and unit checks |
| HTTP ingest API | `POST /ingest/readings` with a revocable source token; lets any future sensor, script or spreadsheet automation push data |
| Demo simulator | Normal, door-left-open and power-cut scenarios; every simulated row is flagged and badged SIMULATED |

Pitch honesty: say clearly that demo data is simulated and that the platform is sensor-ready through the API. Do not imply live hardware.

## 4. Thresholds and reference tables (maintain in `config/`)

All numbers below are **placeholders to be filled from a cited source**; do not present them as facts in the pitch until sourced.

- Commodity table: optimal temperature range, humidity range, reference shelf life (per vegetable).
- Marine risk: wave height, wind speed, gust thresholds for amber and red (confirm with IMD / INCOIS / local fisheries guidance).
- Check-in interval defaults and grace period.
- Alert debounce windows (out-of-range minutes, offline minutes).

## 5. External data sources

| Data | Source | Notes |
|---|---|---|
| Weather + marine | Open-Meteo (weather and marine APIs) | Check current terms for commercial use before going live |
| Mandi prices | Agmarknet via data.gov.in | Needs an API key; rate limits apply; cache daily |
| Cyclone / official warnings | IMD, INCOIS | Link to official pages; do not re-issue as your own |
| Fishing zones, ban periods | Odisha Fisheries Dept / official notices | Verify polygons and dates before encoding as geofences |
| Grading photos | Self-collected | See section 6 |

## 6. GradeLens data plan

1. Pick 1 or 2 commodities (e.g. tomato, brinjal).
2. Agree a written grade rubric with an FPO member or agri officer (size, colour, blemish, damage).
3. Collect photos at real markets: varied lighting, backgrounds, phones.
4. Label with at least two people on a sample to measure agreement.
5. Split train / validation / test **by lot**, not randomly by photo, to avoid leakage.
6. Report accuracy, per-class precision / recall, confusion matrix.
7. Keep a "needs review" confidence threshold and log corrections for retraining.

Do not claim accuracy numbers you have not measured.

## 7. SMS notes

- Real transactional SMS in India requires DLT registration of sender ID and templates.
- Odia text uses UCS-2 encoding, so each segment holds about 70 characters; keep templates short.
- Provider adapter interface: `send(to, text)`, `parse_inbound(request)`; implementations: `twilio`, `fast2sms`, `mock`.
- Always rate-limit outbound alerts per user to avoid spam and cost.

## 8. Safety, ethics, legal

- Safety alerts **supplement** official warnings; show this in UI and pitch.
- Escalation contacts (family, fisheries office, coast guard) must be opt-in and editable.
- Collect minimum location data; explain use; allow deletion.
- Store images and phone numbers securely; do not sell data.
- Odia copy and emergency numbers must be verified by a native speaker / official source.
- Grades are decision support, not legal certification.

## 9. Evidence to collect for the pitch

| Claim | Evidence to gather |
|---|---|
| Post-harvest loss is large | Cited government / research figures; 2 to 3 short farmer / FPO interviews |
| Cold storage gap | Local cold-storage availability, distances |
| Fisher safety need | Incident reports, fisher interviews, SMS-only access constraint |
| Price crashes | Agmarknet price history showing harvest-season drops |
| Our accuracy | Held-out metrics and forecast backtest |
| Willingness to pay | Interview notes, pricing assumptions |

## 10. Business model sketch

- **ColdWatch:** monthly SaaS per cold room; no hardware needed, sensor-ready through the ingest API.
- **GradeLens:** per-lot grading fee to FPOs and buyers.
- **SagarSuraksha:** government / cooperative / NGO contracts (free for fishers).
- **MandiMitra:** free for farmers; revenue via aggregator / FPO integrations.
- **MatsyaConnect:** small marketplace fee on completed matches.
- Platform play: shared data and notification layer across all five.

## 11. Environment variables (`.env.example`)

```
DEMO_MODE=true
DATABASE_URL=postgresql+psycopg://app:app@db:5432/setu
REDIS_URL=redis://redis:6379/0
JWT_SECRET=change-me
SIMULATOR_ENABLED=true
INGEST_RATE_LIMIT=60/min
SMS_PROVIDER=mock            # mock | twilio | fast2sms
SMS_API_KEY=
SMS_SENDER_ID=
DATAGOV_API_KEY=
ML_SERVICE_URL=http://ml:9000
VAPID_PUBLIC_KEY=
VAPID_PRIVATE_KEY=
OBJECT_STORE_URL=
```

## 12. Naming glossary

- **Krushi** = agriculture, **Neel Kranti** = Blue Revolution (fisheries), **Setu** = bridge
- **FPO** = Farmer Producer Organisation
- **Mandi** = wholesale agricultural market
- **Agmarknet** = government agricultural marketing information network

## 13. Pitch one-liners

- "One platform from farm gate to fishing boat, built for Odia users with weak signal."
- "We turn a phone, simple logs and public data into fewer losses and safer trips."
- "Offline-first and SMS-first, because the people we serve are not always online."
