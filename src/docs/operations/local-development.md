# Local Development Runbook

## Scope

Local setup, startup commands, and troubleshooting guidance for backend and frontend.

## Prerequisites

- Python 3.14 available via local path.
- Node.js and npm installed.
- Backend env file at src/backend/.env.development.

## Backend Setup

1. Install dependencies:
   - python -m pip install -r src/backend/requirements.txt
2. Start backend:
   - python -m uvicorn --app-dir src/backend --env-file src/backend/.env.development app.main:app --reload --host 0.0.0.0 --port 8000
3. Verify:
   - GET http://localhost:8000/docs should return status 200.

## Frontend Setup

1. Install dependencies:
   - npm --prefix src/frontend install
2. Start frontend:
   - npm --prefix src/frontend run dev
3. Verify:
   - Open http://localhost:5173

## Common Issues

### Python not found

- Symptom: python command opens Microsoft Store hint.
- Fix: use full interpreter path or repair PATH/app aliases.

### uvicorn module missing

- Symptom: No module named uvicorn.
- Fix: install backend requirements with the same interpreter used to run server.

### Backend starts but DB init fails

- Symptom: getaddrinfo or database connection errors in startup logs.
- Fix: validate DATABASE_URL host/user/password/ssl configuration.
- Note: app may still start, but persistence features may fail.

### Frontend vite not found

- Symptom: vite is not recognized.
- Fix: run npm install in src/frontend.

## Enhancement Hooks

- Add make-like scripts (PowerShell or npm) for one-command startup.
- Add docker-compose for unified local stack.
- Add healthcheck scripts for CI smoke tests.
