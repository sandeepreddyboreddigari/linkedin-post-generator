# LinkedIn Post Generator

A small full-stack app that turns a topic and a few writing choices into a LinkedIn post draft. The frontend is a static HTML/CSS/JavaScript page, and the backend is a FastAPI service that sends generation requests to Ollama.

## Features

- Generate posts using topic, purpose, audience, tone, length, and optional context.
- Preview and copy the generated post in the existing frontend.
- Check backend availability with `GET /health`.
- Use Ollama's `llama3.2:3b` model for local generation.
- Configure the backend URL and allowed frontend origins for deployment.

## Technology stack

- Python, FastAPI, and Uvicorn
- Ollama with `llama3.2:3b`
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

### Ollama setup

Install and start Ollama, then download the model:

```bash
ollama pull llama3.2:3b
ollama serve
```

If Ollama is already running as a background app or service, leave it running and skip `ollama serve`. By default, the backend connects to `http://127.0.0.1:11434`. To use another Ollama host, set `OLLAMA_BASE_URL` in the backend process environment.

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
- Before publishing the frontend, change `API_BASE_URL` in `frontend/script.js` to the deployed backend URL, such as `https://your-backend.onrender.com`.
- The backend defaults to local Ollama, which a public Render service cannot reach on your computer. To generate posts after deployment, provide a publicly reachable Ollama-compatible host by setting `OLLAMA_BASE_URL` in the Render service environment. Keep the local default for development.

Render supplies `PORT`; Uvicorn binds to `0.0.0.0` through the start command. The app does not require an API key. Do not add credentials or secret values to source files. `.gitignore` excludes `.env` files, including `.env.example` files.

## API

`POST /generate` accepts JSON containing `topic`, `purpose`, `tone`, `audience`, and `length`, with optional `additional_info`. It returns the generated draft as `{"post": "..."}`. `GET /health` returns `{"status": "ok"}`.

## Project structure

```text
backend/
  main.py          FastAPI endpoints, CORS, and Ollama integration
  requirements.txt Python runtime dependencies
frontend/
  index.html       Form and generated-post display
  style.css        Page styling
  script.js        Form submission and configurable backend URL
.gitignore         Excludes local secrets and generated files
README.md          Setup and deployment guidance
```
