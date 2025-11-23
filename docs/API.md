# Engir API Reference

All endpoints live under `/api/` and return JSON. Unless stated otherwise the API accepts/returns UTF-8 JSON payloads and supports pagination via DRF's `limit` / `offset` parameters.

## Authentication

Default permissions allow read access to everyone, but write actions (POST/PATCH/DELETE) should be protected by whichever scheme you plug into DRF (JWT, session auth, etc.). Session-specific actions already require authentication server-side.

## Teachers

### Create a teacher
```
POST /api/teachers/
{
  "full_name": "Ava Instructor",
  "email": "ava@example.com",
  "headline": "Live coding coach",
  "bio": "15 years building products.",
  "profile_url": "https://ava.bio",
  "avatar_url": "https://cdn.engir.app/avatars/ava.png"
}
```
Response: `201 Created` with teacher object. List/search teachers via `GET /api/teachers/?search=ava`.

## Classrooms

### Create a class
```
POST /api/classes/
{
  "teacher_id": 1,
  "title": "Intro to Streaming",
  "description": "Go live in 30 minutes.",
  "duration_minutes": 60,
  "capacity": 25,
  "tags": ["streaming", "gear"],
  "is_public": true
}
```
Response: `201 Created` with generated `code`. Fetch via `GET /api/classes/<id>/` or `GET /api/classes/code/<CODE>/`.

## Sessions

### Schedule a session
```
POST /api/sessions/
{
  "classroom_id": 5,
  "title": "Live workshop",
  "starts_at": "2025-01-10T16:00:00Z",
  "duration_minutes": 75,
  "stream_provider": "custom"
}
```
Response contains auto-generated `stream_key`, `host_url`, and `playback_url`.

### Rotate credentials
```
POST /api/sessions/12/regenerate_stream_key/
```
Returns fresh `stream_key` + URLs. Requires authentication.

### Start or end a stream
```
POST /api/sessions/12/start_stream/
POST /api/sessions/12/end_stream/
{
  "recording_url": "https://cdn.engir.app/records/12.mp4"
}
```
Used by hosts to flip the live status and optionally attach a recording link.

## Enrollments

### Join a class
```
POST /api/enrollments/
{
  "class_code": "ABC123",
  "full_name": "Leo Learner",
  "email": "leo@example.com",
  "phone_number": "+1-555-0000",
  "notes": "Need captions"
}
```
If the class is full or the email already exists for that class the API responds with `400 Bad Request`. Admins can review enrollment queues via `GET /api/enrollments/?classroom=<id>`.

---

For schema or workflow changes update this document alongside the code to keep client teams unblocked.
