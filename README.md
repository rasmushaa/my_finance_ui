# My Finance UI
[![Backend API](https://img.shields.io/badge/Backend%20API-my__finance__api-181717?logo=github)](https://github.com/rasmushaa/my_finance_api)
[![Tests](https://github.com/rasmushaa/my_finance_ui/actions/workflows/tests.yaml/badge.svg?branch=main)](https://github.com/rasmushaa/my_finance_ui/actions/workflows/tests.yaml)

## Streamlit Frontend for Fast, Clean Money Ops
Personal finance workflows, but with less spreadsheet pain and more flow.

This repository contains the Streamlit frontend for the My Finance platform. It connects to a FastAPI backend for authentication, transaction processing, labeling, and asset tracking.

## Main Concepts
1. Login is handled with Google OAuth.
2. Frontend session stores the authenticated `User` object and JWT token.
3. All API calls include `Authorization: Bearer <token>`.
4. Transaction flow is split into upload/transform and label/save phases.
5. Assets flow captures quarterly balance snapshots (assets, liabilities, capital gains).
6. Admin pages support file-type metadata and model-performance inspection.

## Architecture At A Glance
- Entry point: `src/app.py`
- Shared utilities:
  - `src/core/auth.py` for auth/session guards
  - `src/core/env.py` for required env variable validation
  - `src/core/layout.py` for base page layout + logs column
  - `src/core/logging.py` for in-UI logs and backend error formatting
  - `src/core/focus.py` for page-change detection
- Pages:
  - `src/pages/login.py`
  - `src/pages/transaction_input.py`
  - `src/pages/transaction_labeling.py`
  - `src/pages/assets.py`
  - `src/pages/filetypes.py`
  - `src/pages/ai.py`
  - `src/pages/logout.py`

## Runtime Environment Variables
These variables are required by the application at runtime (local and Cloud Run):

| Variable | Required | Example | Used For |
| --- | --- | --- | --- |
| `ENV` | Yes | `dev`, `stg`, `prod` | UI environment badge and runtime environment context |
| `API_BASE_URL` | Yes | `http://localhost:8081` | Base URL for all backend API requests |
| `GOOGLE_CLIENT_ID` | Yes | `123...apps.googleusercontent.com` | Google OAuth client identifier for login |
| `REDIRECT_URI` | Yes | `http://localhost:8080/` | OAuth callback URI and backend auth-code exchange payload |

Optional local launcher variables (`scripts/run_local_terminal.sh`):

| Variable | Default | Purpose |
| --- | --- | --- |
| `STREAMLIT_PORT` | `8080` | Local Streamlit port |
| `APP_ENTRYPOINT` | `src/app.py` | Entry script path |
| `ENV_FILE` | `.env` | Environment file to source |

## Local Development
1. Create `.env` with the required runtime variables.
2. Install dependencies:
```bash
uv sync --group dev
```
3. Start the app:
```bash
scripts/run_local_terminal.sh
```

4. Test local Docker build + runtime (before pushing/deploying):
```bash
scripts/test_local_docker.sh
```

Alternative:
```bash
PYTHONPATH="$PWD" uv run streamlit run src/app.py --server.port 8080 --server.headless=true
```

## Deployment (GitHub Actions -> Cloud Run)
Deployment workflow: `.github/workflows/deploy.yaml`

Branch behavior:
- `main` deploys `ENV=prod`
- `stg` deploys `ENV=stg`
- `feature/*` validates build only, no deploy

### Required GitHub Secrets
| Secret | Required | Purpose |
| --- | --- | --- |
| `GCP_PROJECT_ID` | Yes | Google Cloud project id |
| `GCP_LOCATION` | Yes | Deployment region, also Artifact Registry host |
| `GCP_WORKLOAD_IDENTITY_POOL` | Yes | Workload identity provider for GitHub OIDC |
| `GCP_DEPLOY_SA` | Yes | Service account used by GitHub Actions to deploy |
| `GOOGLE_CLIENT_ID` | Yes | Runtime OAuth client id injected to Cloud Run |
| `API_BASE_URL_PROD` | Yes | Backend API URL for production frontend deploy |
| `API_BASE_URL_STG` | Yes | Backend API URL for staging frontend deploy |
| `REDIRECT_URI_PROD` | Yes | OAuth redirect URI for production frontend deploy |
| `REDIRECT_URI_STG` | Yes | OAuth redirect URI for staging frontend deploy |
| `GCP_MY_FINANCE_UI_SA` | Preferred | Service account attached to deployed Cloud Run service |

Cloud Run runtime receives exactly these app env vars:
- `API_BASE_URL`
- `GOOGLE_CLIENT_ID`
- `REDIRECT_URI`
- `ENV`
