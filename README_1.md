# KrushiNeel Setu

**One fully web-based platform for Odisha's farmers, FPOs and fisherfolk: cut post-harvest loss, sell at the right time, and stay safe at sea. No special hardware required.**

Built for the *Krushi & Neel Kranti* (agriculture and fisheries) hackathon theme. KrushiNeel Setu ("setu" = bridge) connects people on the ground (cold rooms, mandis, boats, landing sites) to data that can help them, through an offline-first web app (PWA) and SMS.

## What it does

| Module | Name | For | One-line value |
|---|---|---|---|
| 1 | **ColdWatch** | FPOs, cold-room owners | Log or import cold-room temperature and humidity, get alerts before produce spoils, see estimated remaining shelf life |
| 2 | **GradeLens** | Farmers, FPOs, buyers | Phone-photo vegetable grading to settle price disputes with an objective grade |
| 3 | **SagarSuraksha** | Fisherfolk (Puri, Ganjam, Kendrapara, Balasore, Chilika) | Offline-first weather and boundary alerts, boat check-in, SMS fallback |
| 4 | **MandiMitra** | Farmers, FPOs | Mandi price trends and hold / sell-now hints in Odia |
| 5 | **MatsyaConnect** | Fisherfolk, buyers | Landing-site catch listings matched to nearby buyers |

All five share one backend, one database, one login system, one notification engine (web push + SMS) and one Odia / English UI.

## No hardware: how ColdWatch gets its data

Temperature and humidity readings come in through four web-only routes:

1. **Quick log:** staff enter a reading in two taps (with reminders if a log is missed).
2. **CSV import:** upload an export from any existing digital thermometer or data logger.
3. **HTTP ingest API:** `POST /ingest/readings` with a source token, so any future sensor, script or spreadsheet automation can push data without changing the platform.
4. **Demo simulator:** built-in scenario generator (normal, door left open, power cut) for demos and testing. Simulated readings are always labelled **SIMULATED**.

## Quick start (local)

Requirements: Docker + Docker Compose, Node 20+, Python 3.11+.

```bash
git clone <your-repo-url> krushineel-setu
cd krushineel-setu
cp .env.example .env          # fill in keys (all optional for demo mode, see below)
docker compose up --build     # web, api, worker, ml service, db, redis
```

- Web app: http://localhost:5173
- API docs (Swagger): http://localhost:8000/docs

### Demo mode (no paid keys)

Set `DEMO_MODE=true` in `.env`. Then:
- The **ColdWatch simulator** can be started from the admin screen (or `python tools/seed_demo_data.py --simulate`).
- The **SMS gateway** uses a console / in-app mock instead of a real provider.
- **Mandi prices** load from a bundled CSV seed if no data.gov.in key is set.
- **Weather / marine data** use Open-Meteo (no key needed); a cached sample is used offline.

```bash
python tools/seed_demo_data.py    # users, boats, listings, prices, demo cold rooms
```

## Repository layout

```
krushineel-setu/
├── apps/
│   ├── web/                # React + Vite PWA (Odia/English, offline-first)
│   └── api/                # FastAPI backend (modular monolith)
├── services/
│   └── ml/                 # grading + price forecasting (FastAPI, ONNX)
├── tools/                  # seeders, CSV samples
├── infra/                  # docker, nginx, deploy configs
├── docs/                   # PLAN, ARCHITECTURE, DESIGN, PROGRESS, DETAILS
└── docker-compose.yml
```

## Tech stack

- **Frontend:** React, Vite, TypeScript, Tailwind, PWA (service worker + IndexedDB), i18next (Odia, English)
- **Backend:** Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL, Redis (queue + cache)
- **ML:** PyTorch (MobileNetV2 transfer learning) exported to ONNX; LightGBM for price forecasting
- **Data:** Open-Meteo (weather + marine), data.gov.in Agmarknet (mandi prices), your own labelled grading photos
- **Messaging:** Web Push + SMS provider adapter (Twilio / Fast2SMS / mock)
- **Deploy:** Docker Compose on a VPS, or Render / Fly.io + managed Postgres

## Documentation

- [PLAN](PLAN.md): scope, phases, deliverables, risks
- [ARCHITECTURE](ARCHITECTURE.md): system design, data model, APIs
- [DESIGN](DESIGN.md): UX principles, screens, Odia/offline/SMS design
- [PROGRESS](PROGRESS.md): live checklist of what is done
- [DETAILS](DETAILS.md): important details, assumptions, thresholds, data sources, pitch notes

## Honest limitations

- Without sensors, ColdWatch readings depend on people logging or importing data; the platform alerts on missed logs for this reason. Simulated data is always labelled.
- Fisherfolk alerts **supplement** official IMD / INCOIS / Fisheries Department warnings; they do not replace them.
- Grading accuracy depends on the labelled photo set you collect; report validation metrics, not guesses.
- Spoilage risk is a rule-based estimate, not a guarantee of shelf life.
- Real SMS in India needs DLT registration; demo mode uses a mock.

## License

MIT (change as needed).
