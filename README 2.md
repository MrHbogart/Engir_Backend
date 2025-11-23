# Engir Backend (Django + DRF)

Engir is a lightweight teaching marketplace where instructors publish live classes, learners join via short invite codes, and hosts share open-source-compatible streaming links. This repository provides a Django REST Framework API for teachers, classrooms, sessions, and enrollments.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_demo_data  # optional demo users/classes
.venv/bin/python manage.py runserver 0.0.0.0:8000
```

Configuration lives in `.env` (production) and `.env.example` (local). When `DJANGO_DEBUG=True`, the settings from `.env.example` take precedence so SQLite is used automatically. On the server set `DJANGO_DEBUG=False` and `ENGIR_DB_BACKEND=postgres` alongside the `POSTGRES_*` vars to switch to PostgreSQL. Use `docker-compose up --build` for a gunicorn + Postgres stack that mirrors production naming (`engir_web`, `engir_db`).

Create a Django superuser to reach the admin panel:

```bash
.venv/bin/python manage.py createsuperuser
```

Browse `http://127.0.0.1:8000/admin/` to manage teachers, classes, and enrollments manually.

## API overview

High-level endpoints are listed below. Full request/response samples live in [`docs/API.md`](docs/API.md).

- `POST /api/teachers/` — register an instructor profile.
- `POST /api/classes/` — create a class; the backend issues a unique `code`.
- `GET /api/classes/code/<CODE>/` — fetch public details via the shareable code.
- `POST /api/enrollments/` — learners join by providing `class_code` + contact details.
- `POST /api/sessions/` — schedule a live session for a class and define streaming metadata.
- `POST /api/sessions/<id>/regenerate_stream_key/` — rotate the secure RTMP key + URLs for a session.
- `POST /api/sessions/<id>/start_stream/` — mark a session as live; `end_stream/` finalizes it and optionally stores a recording URL.
- `POST /api/auth/login/` — obtain JWT access/refresh tokens plus user metadata (teacher/student).
- `POST /api/auth/register/<teacher|student>/` — create an authenticated profile with the selected role.
- `GET /api/dashboard/<teacher|student>/` — role-aware snapshot used by the Vue dashboards.

The `seed_demo_data` command provisions `mentor@engir.demo / demo-classroom` (teacher) and three demo students so you can immediately sign in and explore the dashboards.

Session records keep `host_url`, `playback_url`, and `stream_key` fields so you can plug Engir into self-hosted RTMP servers or services like Mux/LiveKit. Learners only need the `playback_url` surfaced by the public endpoints; hosts rotate credentials through the protected actions above.

All endpoints currently use `AllowAny` permissions to keep experimentation simple, except the session management actions which require authentication. Tighten authentication, throttling, and email verification before going to production. Update `config/settings.py` for domain-specific CORS/CSRF policies.

## Running tests

```bash
.venv/bin/python manage.py test engir.tests
```

This uses the default SQLite database so no additional services are required. Set `ENGIR_DB_BACKEND=postgres` if you want to run tests against PostgreSQL.
