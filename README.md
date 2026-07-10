
# Academic GPA Tracker

Track academic results — School, Intermediate, and every College semester — in one place, with a GitHub-styled dashboard that shows how your GPA is actually trending over time.

## What's here

- **Multi-user auth** (username + password, httpOnly JWT cookies) — built for 100+ independent accounts, each seeing only their own data.
- **Dashboard** with summary stat cards, an interactive GPA trend chart, and a rise/decline percentage against every semester.
- **History** page: a sortable table with edit and delete.
- **Add result** form with smart period suggestions (if your latest College entry is "Semester 4", it suggests "Semester 5" first).
- **Compare** page: manually enter marks for up to five people (e.g. 852/1000) and see them side by side on a bar chart. This is a scratch-pad tool — it does **not** look up other users' accounts or stored history. See "A design decision worth understanding" below for why.

---

## Project structure

```
academic-gpa-tracker/
├── backend/                   # FastAPI + PostgreSQL
│   ├── app/
│   │   ├── api/               # Route handlers (auth, records, compare)
│   │   ├── core/               # Config, database session, JWT/password helpers
│   │   ├── crud/               # Database operations, trend calculation
│   │   ├── models/             # SQLAlchemy models
│   │   ├── schemas/             # Pydantic v2 schemas
│   │   └── main.py             # App entry point
│   ├── alembic/                # Database migrations
│   ├── requirements.txt
│   ├── render.yaml             # Render Blueprint (optional one-click deploy)
│   └── .env.example
│
└── frontend/                   # Next.js 15 + TypeScript
    ├── src/
    │   ├── app/                # Pages (App Router)
    │   ├── components/
    │   │   ├── ui/              # shadcn/ui primitives
    │   │   ├── dashboard/       # Chart, summary cards, trend list
    │   │   ├── history/         # Table, edit/delete dialogs
    │   │   ├── compare/         # Comparison chart
    │   │   ├── layout/          # Nav, sidebar, auth guard
    │   │   └── providers/       # TanStack Query provider
    │   ├── lib/                 # API client, Zod schemas, utils
    │   ├── hooks/                # useCurrentUser
    │   └── types/                # Shared TypeScript types
    ├── package.json
    ├── vercel.json
    └── .env.example
```

---

## A design decision worth understanding

The brief for this app asked for two things that pull against each other: an app usable by 100+ independent people, *and* a feature to compare five people's Intermediate marks. If "compare" meant looking up five real accounts by username, any of the 100+ users could pull up a stranger's complete academic history — including backlogs or a rough semester — with no consent step at all.

The Compare page here works differently: you type in labels and marks yourself, for up to five entries, and nothing is saved or tied to any account. It solves the stated use case (see 852/1000 side by side with four others) without turning the app into a lookup tool for other people's private records. If a future version genuinely needs person-to-person comparison of stored accounts, that requires an explicit opt-in/visibility system first — it shouldn't be added by simply pointing the existing form at the users table.

---

## Local setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 14+ (or use SQLite locally — see note below)

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env: set DATABASE_URL and generate a real SECRET_KEY with:
#   openssl rand -hex 32

alembic upgrade head             # creates the users and academic_records tables
uvicorn app.main:app --reload    # runs on http://localhost:8000
```

Visit `http://localhost:8000/docs` for the interactive FastAPI docs — useful for testing endpoints directly before the frontend is running.

**Using SQLite instead of Postgres for local testing:** set `DATABASE_URL=sqlite:///./dev.db` in `.env`. Alembic's autogenerate and the app both work against SQLite, but switch to real Postgres before deploying — Render's free Postgres tier is what production uses, and a few things (the `Enum` type, in particular) behave slightly differently across dialects.

### Frontend

```bash
cd frontend
npm install

cp .env.example .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000

npm run dev                      # runs on http://localhost:3000
```

Open `http://localhost:3000` — it redirects to `/login` if you're not authenticated yet. Register an account, and you're in.

---

## Environment variables

### Backend (`backend/.env`)

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string. |
| `SECRET_KEY` | Random secret for signing JWTs. Generate with `openssl rand -hex 32` — never reuse the example value. |
| `ALGORITHM` | JWT signing algorithm. Leave as `HS256`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Session length in minutes. Defaults to 10080 (7 days). |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend origins. Must exactly match your Vercel URL in production — no trailing slash. |
| `ENVIRONMENT` | `development` locally, `production` on Render. Controls whether auth cookies are set with `Secure` + `SameSite=None` (required cross-origin) or `SameSite=Lax` (works over plain HTTP locally). |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | Base URL of the FastAPI backend, no trailing slash. |

---

## Deployment

### Backend → Render

**Option A: Blueprint (recommended)**

1. Push this repository to GitHub.
2. In the Render dashboard, choose **New → Blueprint**, point it at your repo, and select `backend/render.yaml`.
3. Render provisions both the Postgres database and the web service automatically, including a generated `SECRET_KEY`.
4. Once deployed, open the web service's settings and update `CORS_ORIGINS` to your actual Vercel URL (you'll get this in the next section) — the blueprint ships with a placeholder that blocks all cross-origin requests until you do.

**Option B: Manual dashboard setup**

1. Create a new **PostgreSQL** instance on Render. Copy its connection string.
2. Create a new **Web Service**, pointing at the `backend/` directory of your repo.
3. Build command: `pip install -r requirements.txt && alembic upgrade head`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add the environment variables listed above, using the Postgres connection string from step 1, a freshly generated `SECRET_KEY`, and `ENVIRONMENT=production`.

**Important:** Render's free tier spins down after inactivity, and the first request afterward can take 30–60 seconds while it wakes up. This is normal — the `/health` endpoint exists partly so you (or a monitoring tool) can ping it to keep the service warmer.

### Frontend → Vercel

1. Import the repository into Vercel, setting the **root directory** to `frontend/`.
2. Vercel auto-detects Next.js — no build command changes needed.
3. Add the environment variable `NEXT_PUBLIC_API_URL`, set to your Render backend's URL (e.g. `https://gpa-tracker-api.onrender.com`).
4. Deploy. Copy the resulting Vercel URL.
5. Go back to your Render backend's environment variables and set `CORS_ORIGINS` to that exact Vercel URL, then redeploy the backend so the change takes effect.

### The cross-origin cookie handshake

Because Vercel and Render are different domains, the httpOnly auth cookie only survives the trip if three things line up simultaneously:

- Backend sends the cookie with `Secure=True` and `SameSite=None` (handled automatically when `ENVIRONMENT=production`).
- Backend's `CORS_ORIGINS` exactly matches the Vercel URL — including `https://`, excluding any trailing slash.
- Frontend's every API call includes `credentials: "include"` (already the case everywhere in `lib/api.ts` — this isn't something you need to add, just something worth knowing is there if login ever mysteriously stops persisting).

If login succeeds but the very next request comes back `401 Unauthorized`, this handshake is almost always where to look first — specifically a `CORS_ORIGINS` mismatch or `ENVIRONMENT` not being set to `production`.

---

## A few things intentionally left out

- **Password reset by email.** There's no email field on the user model at all, since login is username/password only. If someone forgets their password, there's currently no self-service recovery — worth knowing before this goes out to 100 real people. Adding it later means adding an email field, an email-sending provider, and a reset-token flow; it's a real feature, not a quick patch.
- **Rate limiting on `/api/auth/register`.** Fine for a modest, mostly-trusted user base; if this app becomes fully public, add rate limiting (e.g. via `slowapi`) before that happens.
- **User-to-user record lookup.** Deliberately not built — see "A design decision worth understanding" above.

## Testing note

The backend was verified end-to-end during development: register → login-via-cookie → create records → dashboard trend calculation → user-isolation (a second account cannot see the first account's records) → the comparison endpoint's percentage math. The frontend was verified with a full production build (`npm run build`, with type-checking) and a clean ESLint pass, and every route compiles and statically generates without errors. Neither of these substitutes for clicking through the running app yourself once — do that before relying on it for anything real.
