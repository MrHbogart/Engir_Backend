# Repository Guidelines

Engir is a Django + DRF backend for a classroom marketplace: teachers publish live classes, learners join via short codes, and admins track enrollments and live sessions. Keep the API lean, document schema tweaks, and ship declarative commits so future agents can ramp quickly.

## Project Structure & Module Organization
- `config/` hosts settings, ASGI/WSGI entry points, and URL routing. Environment variables are loaded from `.env` (DATABASE, CORS, CSRF, etc.).
- `engir/` is the domain app. It contains models for `Teacher`, `Classroom`, `Session`, and `Enrollment`, plus DRF serializers, viewsets, and router definitions. Put tests in `engir/tests/` following Django’s discovery rules.
- `manage.py` bootstraps Django. `docker-compose.yml` spins up `engir_web` (gunicorn) + `engir_db` (Postgres) for parity checks.
- `docs/API.md` holds the endpoint reference. Update it whenever response fields or actions change.

## Build, Test, and Development Commands
- `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` — local env setup.
- `.venv/bin/python manage.py migrate` then `.venv/bin/python manage.py runserver 0.0.0.0:8000` — apply schema changes and start the API.
- `.venv/bin/python manage.py test` — run the suite against the default SQLite DB; set `ENGIR_DB_BACKEND=postgres` to use Postgres.
- `docker-compose up --build` — gunicorn + Postgres stack that mirrors production env vars.

## Coding Style & Naming Conventions
Follow PEP 8 with 4-space indentation. Use PascalCase for models/serializers, snake_case for methods/fields, kebab-case for URL path segments, and suffix helper serializers with `Serializer`. Class codes stay uppercase, so normalize user input with `.upper()`.

## Sessions & Streaming
- `Session` models capture scheduling, provider, stream key, host/playback URLs, and recordings; they live in `engir/models.py`.
- `/api/sessions/` exposes CRUD plus `regenerate_stream_key/`, `start_stream/`, and `end_stream/`. Keep those actions authenticated in clients.
- With `stream_provider='custom'` the backend auto-generates RTMP keys + Engir-branded URLs; set provider to `zoom`, `youtube`, etc. when posting your own `host_url`/`playback_url` (and document any new providers in README/API refs).

## Testing Guidelines
Use `.venv/bin/python manage.py test` with DRF’s APIClient helpers. Store specs under `engir/tests/` (`test_classroom_api.py`, `test_session_stream_key.py`, etc.), name methods `test_<scenario>_<expected>()`, and target ≥80 % line coverage via `coverage run manage.py test && coverage report`.

## Commit & Pull Request Guidelines
Write imperative, Conventional-Commit-style subjects (`feat: add session streaming hooks`). Summarize schema changes, endpoints, migrations, and manual verification inside each PR, adding screenshots when API/admin output matters. Promote drafts only after lint + tests pass and relevant docs (README/AGENTS/changelog) are updated.

## Security & Configuration Tips
Never commit secrets—keep `.env` local and share a redacted `.env.example` when needed. Before deploying, set `DEBUG=False`, update `ALLOWED_HOSTS`, and review CORS/CSRF origins. Rotate staff credentials, serve over HTTPS, and keep analytics logs free of invite codes or stream keys.
