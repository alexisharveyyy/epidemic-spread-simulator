# Epidemic Spread Simulator

[![CI](https://github.com/alexisharveyyy/epidemic-spread-simulator/actions/workflows/ci.yml/badge.svg)](https://github.com/alexisharveyyy/epidemic-spread-simulator/actions/workflows/ci.yml)
[![Live demo](https://img.shields.io/badge/live%20demo-online-00d4ff)](https://epidemic-spread-simulator.onrender.com)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/downloads/release/python-3119/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Live demo:** https://epidemic-spread-simulator.onrender.com

A fully runnable epidemiological simulation platform built around an SIR
(Susceptible-Infected-Recovered) compartmental model. The application exposes
a FastAPI REST API that accepts simulation parameters, runs a SciPy ODE solver,
and returns both structured JSON results and a base64-encoded PNG of the SIR
curves. A Jinja2 + vanilla JavaScript frontend (served by FastAPI itself) lets
users drive simulations from a browser, browse a live Outbreak Intelligence
Feed sourced from NewsAPI, and watch a Geographic Spread Simulation animate
on a Leaflet map tied to the active SIR transmission parameters.

The project demonstrates scientific computing, REST API design, server-side
visualization, and public health domain modeling in a single cohesive
application.

## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.11+ |
| Web framework | FastAPI |
| Validation | Pydantic v2 |
| ODE solver | SciPy (`scipy.integrate.odeint`) |
| Numerics | NumPy |
| Visualization | matplotlib (`Agg` backend) |
| Templating | Jinja2 |
| HTTP client | httpx (async) |
| Mapping | Leaflet.js (CDN) |
| Tabular | pandas |
| Tests | pytest, pytest-asyncio |
| Format / lint | Black, Ruff |

## Setup

```bash
# 1. Clone
git clone <your-fork-url> epidemic-simulator
cd epidemic-simulator

# 2. Virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Dependencies
pip install -r requirements.txt

# 4. Environment
cp .env.example .env
# Optionally fill in NEWS_API_KEY. Without one, the app uses a synthetic
# fallback feed so nothing breaks.

# 5. Run the dev server
uvicorn app.main:app --reload

# 6. Open the UI
open http://127.0.0.1:8000
```

## Site Map

| Page         | Path           | Description |
|---|---|---|
| Simulator    | `/`            | Interactive SIR simulator with map and live news feed |
| About        | `/about`       | The SIR model explained with equations and references |
| Scenarios    | `/scenarios`   | Pre-configured disease parameter sets to load with one click |
| Sensitivity  | `/sensitivity` | Parameter sweep analysis showing how outcomes vary with β or γ |
| Vaccination  | `/vaccination` | What-if comparison of outbreak dynamics with and without pre-existing immunity |
| History      | `/history`     | Browser-local record of recent simulations |
| Glossary     | `/glossary`    | Definitions of key epidemiology terms |
| Author       | `/author`      | About the project author |
| Credits      | `/credits`     | Open-source acknowledgements |
| Roadmap      | `/roadmap`     | Project direction and planned features |

## API Reference

| Method | Path | Description |
|---|---|---|
| `GET`  | `/`                                      | Render the HTML interface |
| `GET`  | `/api/health`                            | Liveness check |
| `POST` | `/api/simulate`                          | Run SIR simulation, return JSON + chart |
| `GET`  | `/api/simulate/defaults`                 | Return default simulation parameters |
| `GET`  | `/api/simulate/download/{filename}`      | Download a previously exported CSV |
| `GET`  | `/api/news`                              | Fetch outbreak intelligence headlines (60s cache) |
| `GET`  | `/api/news/refresh`                      | Force refresh outbreak intelligence headlines |
| `POST` | `/api/spread/preview`                    | Compute geographic spread rings for a given day |
| `GET`  | `/api/scenarios`                         | List all pre-configured scenarios |
| `GET`  | `/api/scenarios/{scenario_id}`           | Fetch a single scenario by ID |
| `POST` | `/api/sensitivity/run`                   | Run a parameter sweep and return chart + points |

### `POST /api/simulate`

Request:

```json
{
  "population": 100000,
  "beta": 0.3,
  "gamma": 0.1,
  "initial_infected": 10,
  "days": 160,
  "export_csv": false
}
```

Response (truncated):

```json
{
  "records": [
    {"day": 0, "susceptible": 99990.0, "infected": 10.0, "recovered": 0.0, "rt": 2.999}
  ],
  "summary": {
    "peak_infected": 16322,
    "peak_day": 60,
    "total_recovered": 94010,
    "outbreak_duration_days": 132,
    "herd_immunity_reached": true
  },
  "chart_b64": "iVBORw0KGgoAAA...",
  "csv_download_path": null
}
```

`chart_b64` is the raw base64 PNG payload **without** the `data:image/png;base64,`
URI prefix; the frontend prepends it before assigning to `<img src>`.

### `POST /api/spread/preview`

Request:

```json
{
  "origin_lat": 35.68,
  "origin_lng": 139.69,
  "day": 30,
  "beta": 0.3,
  "gamma": 0.1
}
```

Response (truncated):

```json
{
  "wave_rings": [
    {"center_lat": 35.68, "center_lng": 139.69, "radius_km": 4050.0, "wave_index": 0, "severity": "critical"}
  ],
  "secondary_clusters": [
    {"center_lat": 47.68, "center_lng": 157.69, "radius_km": 1234.5, "activated_day": 20}
  ],
  "summary": {
    "countries_affected": 63,
    "spread_radius_km": 17010.0,
    "wave_count": 3,
    "simulation_day": 30
  }
}
```

### `GET /api/news`

Response:

```json
[
  {
    "headline": "Outbreak declared in coastal region",
    "source": "Public Health Wire",
    "severity": "critical",
    "time": "12m ago",
    "url": null
  }
]
```

## Deployment

The live demo is hosted on Render and auto-deploys on every push to `main`.

**Manual redeploy:** push a commit to `main`, or trigger a manual deploy in
the Render dashboard.

**Environment variables (set in the host's dashboard, not in the repo):**

- `NEWS_API_KEY` — optional; falls back to synthetic headlines if unset
- `APP_ENV` — set to `production`
- `PYTHON_VERSION` — `3.11.9`

**Deploying your own copy:**

1. Fork this repo
2. Sign up at https://render.com
3. **New +** → **Blueprint** → point at your fork's `render.yaml`
4. Optionally add `NEWS_API_KEY` in the service's environment variables panel

## Tests

```bash
pytest
```

Tests cover the SIR solver invariants, all routes, chart generation,
CSV export, news fallback, and spread map computation.

## Screenshots

Add screenshots of the dashboard, chart, and spread map to `docs/screenshots/`
(create the directory if it does not exist) and reference them here. Suggested:

- `dashboard.png` - full page after a simulation run
- `chart.png`     - close-up of the SIR curves
- `spread.png`    - spread map with origin and waves placed

## Known Limitations

- The SIR model assumes homogeneous mixing; it does not account for
  demographics, vaccination, or waning immunity.
- Geographic spread rings are geometric approximations and do not account
  for real travel networks, borders, or population density.
- News severity tagging uses substring keyword matching, which can produce
  occasional false positives (e.g., `"rise"` matching inside `"sunrise"`).
- The `data/` directory grows unbounded; there is no automatic cleanup
  of old CSV exports.
- `odeint` and matplotlib are CPU-bound and run on a thread pool; under
  high concurrency, an external worker process would be more appropriate.
- The conservation tolerance (`1e-6 * N`) may fail for populations
  greater than 1e9; this scale is not currently tested.

## TODO / Extensions

- SEIR model with an `Exposed` compartment and configurable incubation period.
- Real CDC dataset integration.
- Multi-strain simulation.
- Population-density-weighted spread using raster data.
- Real flight-route data for secondary cluster placement.
- Word-boundary regex matching in `tag_severity` to eliminate substring
  false positives.
- Dependency injection via `Depends` for service objects to simplify mocking.
