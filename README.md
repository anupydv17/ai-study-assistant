# AI Study Assistant

Upload your PDF notes and turn them into summaries, quizzes, flashcards, and a
chat you can ask questions to.

## Features

- [x] User registration & login (JWT)
- [x] Upload PDF notes
- [x] Extract text from PDFs
- [x] AI chat with your notes
- [x] Generate summaries
- [x] Generate quizzes
- [x] Generate flashcards
- [x] Study history
- [x] Dashboard
- [x] User profile

## Tech Stack

| Layer      | Technology                        |
| ---------- | --------------------------------- |
| Backend    | Python, FastAPI, SQLAlchemy       |
| Frontend   | HTML, CSS, JavaScript (no build)  |
| Database   | SQLite (dev), PostgreSQL (prod)   |
| Migrations | Alembic                           |
| AI         | Google Gemini                     |
| PDF        | PyMuPDF                           |
| Tests      | pytest                            |
| Deployment | Render (API), Vercel (UI)         |

## Architecture

The backend is layered, so each piece has one job:

```
Browser (HTML/CSS/JS)
        │  HTTP + JSON
        ▼
   api/        routers — receive requests, return responses
   schemas/    Pydantic — validate data at the boundary
   services/   business logic — PDF extraction, AI calls, file storage
   crud/       database reads and writes
   models/     SQLAlchemy table definitions
        │
        ▼
   SQLite (dev) / PostgreSQL (prod)
```

Two rules hold the design together:

1. **Validate at the boundary.** Bad input is rejected by the schema layer
   before any business logic runs.
2. **Every database read is scoped to its owner.** Queries filter on
   `owner_id`, so one user can never read another's data.

## Local Setup

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r backend/requirements-dev.txt

# 3. Configure secrets
cp backend/.env.example backend/.env
#    then edit backend/.env and add:
#      GEMINI_API_KEY  — from https://aistudio.google.com/app/apikey
#      SECRET_KEY      — python -c "import secrets; print(secrets.token_urlsafe(48))"

# 4. Create the database
cd backend && alembic upgrade head && cd ..

# 5. Run the API
uvicorn app.main:app --reload --app-dir backend
```

In a second terminal, serve the frontend:

```bash
cd frontend && python3 -m http.server 5500
```

| What              | URL                             |
| ----------------- | ------------------------------- |
| App               | http://127.0.0.1:5500/          |
| API docs          | http://127.0.0.1:8000/docs      |
| Health check      | http://127.0.0.1:8000/health    |

The frontend must be served over HTTP on port **5500** — opening the HTML files
directly will fail, because ES modules and CORS both require a real origin.

## Tests

```bash
cd backend && pytest
```

Tests run against a throwaway in-memory database and a fake AI service, so they
never touch your data, never call Gemini, and never cost anything.

## Database Migrations

The schema is owned by Alembic, not by the application.

```bash
cd backend

alembic current                                  # where is this database?
alembic history                                  # what migrations exist?
alembic revision --autogenerate -m "description" # draft a migration
alembic upgrade head                             # apply pending migrations
alembic downgrade -1                             # undo the last one
```

Always read a generated migration before running it. Adding a `NOT NULL` column
to a table with existing rows needs a `server_default`, and autogenerate will
not add one for you.

Never edit a migration that has already run elsewhere — write a new one.

## Deployment

### Backend — Render

1. Push this repository to GitHub.
2. In Render: **New → Blueprint**, select the repo. It reads `render.yaml` and
   creates the web service plus a PostgreSQL database.
3. Set the two secrets marked `sync: false` in the Render dashboard:
   - `GEMINI_API_KEY` — your Google AI Studio key
   - `CORS_ORIGINS` — your Vercel URL, e.g. `https://your-app.vercel.app`
4. Deploy. `alembic upgrade head` runs before the server starts.

### Frontend — Vercel

1. In Vercel: **Add New → Project**, select the same repo.
2. Set **Root Directory** to `frontend`. No build command, no output directory.
3. Deploy.
4. Copy the Vercel URL into `CORS_ORIGINS` on Render.
5. Put your Render URL into `PRODUCTION_API_URL` in `frontend/js/config.js`,
   commit, and push.

### Known limitation: uploaded files are not durable

Render's free tier gives each instance an **ephemeral filesystem**. When the
service restarts or redeploys, everything in `backend/uploads/` is lost.

In practice this degrades gracefully, because the extracted text is stored in
PostgreSQL: summaries, quizzes, flashcards and chat keep working after a
restart. Only the original PDF file is gone.

Proper fixes, in order of effort:

- Attach a Render persistent disk (paid plan, smallest change)
- Store uploads in object storage such as Cloudflare R2 or Amazon S3
  (the correct answer for anything real)

## Security Notes

- Passwords are hashed with bcrypt and never stored or returned.
- Access tokens are JWTs; changing a password invalidates every token issued
  before the change.
- Uploads are checked by reading the file's magic bytes, not by trusting its
  filename or content type.
- Every document, chat and study item query filters on the owner, and missing
  or unowned resources return `404` rather than `403`.
- `.env` is git-ignored. Secrets are set through the hosting dashboard.
