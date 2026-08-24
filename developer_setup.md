# CareerPulse Developer Setup Guide

This guide describes how to configure and run the CareerPulse platform locally for development and testing.

---

## 1. Quick Start with Makefile
We provide a helper `Makefile` to simplify local commands:

* **`make build`**: Builds dev and prod Docker image layers.
* **`make up`**: Spins up the local development docker-compose cluster in the background (FastAPI, Nginx, PostgreSQL, and pgAdmin).
* **`make down`**: Stops and removes active local development containers.
* **`make backend-test`**: Runs the Python backend unittest discovery suite.
* **`make frontend-test`**: Runs the React Vitest tests.
* **`make lint`**: Runs backend python compiler checks and frontend oxlint checkers.
* **`make clean`**: Deletes workspace python caches, compiled outputs, and active container volumes.

---

## 2. Manual Local Setup

### Backend Setup
1. Create a Python virtual environment (Python >= 3.12):
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
2. Install pip dependencies:
   ```bash
   pip install --upgrade pip
   pip install fastapi uvicorn psycopg2-binary python-dotenv boto3 pyarrow pytest
   ```
3. Set up environment variables inside `.env`:
   ```bash
   cp .env.example .env
   ```
4. Start FastAPI server locally:
   ```bash
   uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install npm packages:
   ```bash
   npm ci
   ```
3. Configure frontend base URL inside `.env`:
   ```bash
   cp .env.example .env
   ```
4. Spin up the Vite development server:
   ```bash
   npm run dev
   ```

---

## 3. Running Test Suites

### Python Backend Unit Tests
Verify database loaders, type normalizations, S3 downloads, and FastAPI controllers:
```bash
make backend-test
```

### React Frontend Tests
Verify visual components, theme persistence, and mock pagination routing:
```bash
make frontend-test
```
To run tests with UI coverage:
```bash
npm --prefix frontend run test
```
