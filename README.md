# LinkedIn Post Generator

A small full-stack app that turns a topic and a few writing choices into a LinkedIn post draft. The static HTML/CSS/JavaScript frontend calls a FastAPI backend, which uses local Ollama during development and can use Google Gemini in production.

## Features

- Generate posts using topic, purpose, audience, tone, length, and optional context.
- Preview and copy the generated post in the existing frontend.
- Check backend availability with `GET /health`.
- Use Ollama's `llama3.2:3b` model for local generation or Google Gemini Flash for cloud generation.
- Configure the backend URL and allowed frontend origins for deployment.

## Technology stack

- Python, FastAPI, and Uvicorn
- Ollama with `llama3.2:3b` for local development
- Google Gen AI Python SDK and Gemini Flash for production
- HTML, CSS, and vanilla JavaScript

## Run locally

### Backend setup

From the project root, create a virtual environment and install the backend dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
```

Start the API from the project root:

```bash
uvicorn main:app --reload --app-dir backend
```

The backend runs at <http://127.0.0.1:8000>. Check <http://127.0.0.1:8000/health> or open the interactive API docs at <http://127.0.0.1:8000/docs>.

By default, `AI_PROVIDER` is `ollama`; the local Ollama path does not require a cloud API key.

### Ollama setup

Install and start Ollama, then download the model:

```bash
ollama pull llama3.2:3b
ollama serve
```

If Ollama is already running as a background app or service, leave it running and skip `ollama serve`. By default, the backend connects to `http://127.0.0.1:11434`. To use another Ollama host, set `OLLAMA_BASE_URL` in the backend process environment.

To test local generation, send a request after starting Ollama and FastAPI:

```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H 'Content-Type: application/json' \
  -d '{"topic":"AI Agents Course","purpose":"Learning Progress","audience":"Students","tone":"Professional","length":"Medium","additional_info":"I found LLMs and vectors difficult at first, and learned them through practice."}'
```

### Frontend

In a separate terminal from the project root, run:

```bash
python3 -m http.server 5500 --directory frontend
```

Open <http://127.0.0.1:5500>. The API URL is configured by the `API_BASE_URL` constant near the top of `frontend/script.js`; it defaults to the local FastAPI server.

## Deployment preparation (Render)

This project is prepared for deployment, but it has not been deployed. Create a Render Web Service for the backend using the repository root as its root directory.

- Build command: `pip install -r backend/requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`
- Add `FRONTEND_ORIGINS` as an environment variable containing the deployed frontend origin, for example `https://your-frontend.onrender.com`. Multiple origins can be comma-separated. Local origins remain allowed by default.
- Set `AI_PROVIDER` to `gemini` in the Render environment.
- Add `GEMINI_API_KEY` as a secret environment variable in Render. Never put the real key in source code, the frontend, or a committed file.
- Set `GEMINI_MODEL` to `gemini-3.8-flash` (the default) or another model enabled for your Gemini API project.
- Before publishing the frontend, change `API_BASE_URL` in `frontend/script.js` to the deployed backend URL, such as `https://your-backend.onrender.com`.

Render supplies `PORT`; Uvicorn binds to `0.0.0.0` through the start command. If `AI_PROVIDER=gemini` but `GEMINI_API_KEY` is missing, `/generate` returns a clear HTTP 503 configuration error. For local Ollama, keep `AI_PROVIDER=ollama` (or leave it unset). `.env.example` contains variable names and non-secret defaults only; `.gitignore` excludes `.env` files.

## API

`POST /generate` accepts JSON containing `topic`, `purpose`, `tone`, `audience`, and `length`, with optional `additional_info`. It returns the generated draft as `{"post": "..."}`. `GET /health` returns `{"status": "ok"}`.

## Project structure

```text
backend/
  main.py          FastAPI endpoints, CORS, and Ollama/Gemini integration
  requirements.txt Python runtime dependencies
frontend/
  index.html       Form and generated-post display
  style.css        Page styling
  script.js        Form submission and configurable backend URL
.gitignore         Excludes local secrets and generated files
README.md          Setup and deployment guidance
```
