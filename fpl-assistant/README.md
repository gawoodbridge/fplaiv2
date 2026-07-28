# FPL Assistant

A responsive web application that helps Fantasy Premier League (FPL) managers
build smarter squads using live data from the official, public FPL API.

- **Backend:** Python (Flask REST API, SQLite via SQLAlchemy, JWT auth)
- **Frontend:** Vanilla HTML, CSS and JavaScript (no build step, no framework)

## Features

- Secure registration / login (passwords hashed, JWT-based sessions)
- Live player, team and fixture data pulled from `fantasy.premierleague.com/api`
- Player search with filters (position, team, price) and sorting
- Side-by-side player comparison (2-5 players)
- Interactive squad builder with a pitch view, formation selector, live
  budget tracking, captain/vice-captain selection, and squad rating
- **AI squad optimiser**: given a budget and any players you want to keep,
  it fills the remaining slots to build the strongest legal 15-man squad
  (2 GKP / 5 DEF / 5 MID / 3 FWD, max 3 players per club, within budget)
- Save multiple squads to your account, accessible from any device
- Watchlist for players you're tracking before a transfer
- Responsive layout: sidebar navigation on desktop, bottom tab bar on mobile

## Project structure

```
fpl-assistant/
  backend/
    app.py              Flask application factory / entry point
    config.py            Configuration (reads environment variables)
    extensions.py         SQLAlchemy instance
    models.py             User / Squad / WatchlistItem database models
    fpl_client.py          Cached wrapper around the official FPL API
    transform.py           Converts raw FPL API payloads to clean JSON
    optimizer.py            Squad optimisation algorithm
    routes/
      auth.py, players.py, teams.py, fixtures.py, squads.py, watchlist.py
    utils/auth_utils.py     JWT helpers + @login_required decorator
    requirements.txt
  frontend/
    index.html              Login / registration
    dashboard.html            Overview: saved squads, in-form players, fixtures
    squad-builder.html         Pitch view + AI optimiser
    players.html                 Search & filter all players
    compare.html                   Side-by-side player comparison
    watchlist.html                  Saved watchlist
    css/style.css
    js/ (api.js, nav.js, auth.js, dashboard.js, players.js,
         compare.js, watchlist.js, squad-builder.js)
```

## Running it locally

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

The API starts on `http://localhost:5000`. A `fpl_assistant.db` SQLite file
is created automatically on first run — no external database needed.

### 2. Frontend

The frontend is static, so any local web server works. From the `frontend/`
folder:

```bash
cd frontend
python3 -m http.server 8080
```

Then open `http://localhost:8080` in your browser.

> The frontend expects the API at `http://localhost:5000/api` by default.
> To point it somewhere else (e.g. a deployed backend), set
> `window.FPL_API_BASE` before `api.js` loads, e.g. add this to the
> `<head>` of each HTML file:
> `<script>window.FPL_API_BASE = 'https://your-api.example.com/api';</script>`

## Notes on the FPL API

No API key is required — `https://fantasy.premierleague.com/api/` is public.
The backend caches responses in memory (5 minutes by default, configurable
via the `FPL_CACHE_TTL` environment variable) so the app stays fast and
doesn't hammer the upstream service.

## About the optimiser

The squad optimiser is a value-density greedy construction with randomized
restarts and a local swap-improvement pass — it is not a full integer linear
program, so it doesn't guarantee a mathematically optimal squad, but it
consistently finds strong, budget-legal squads in milliseconds without
requiring an external solver dependency.

## Environment variables (optional)

| Variable | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | dev-secret-change-me | Flask secret key |
| `JWT_SECRET` | dev-jwt-secret-change-me | Signs auth tokens — **change in production** |
| `JWT_EXPIRY_HOURS` | 72 | Session length |
| `DATABASE_URL` | local SQLite file | Swap for Postgres/MySQL in production |
| `FPL_CACHE_TTL` | 300 | Seconds to cache FPL API responses |
| `CORS_ORIGINS` | * | Restrict in production to your frontend's origin |

## Next steps for production

- Replace SQLite with a managed database (Postgres) and set `DATABASE_URL`
- Set strong, unique `SECRET_KEY` / `JWT_SECRET` values
- Serve the frontend from a CDN or static host, and the backend behind
  HTTPS (e.g. Gunicorn + Nginx, or a PaaS such as Render/Fly.io/Heroku)
- Add rate limiting to the public `/api/squads/optimise` and `/api/squads/rate`
  endpoints since they don't require authentication
