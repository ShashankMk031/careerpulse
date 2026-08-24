# How to Run CareerPulse

This document provides step-by-step instructions on how to build, run, and test the CareerPulse application in both development and production environments.

---

## 1. Quick Start with Docker (Recommended)

Make sure you have **Docker** and **Docker Compose** installed.

### Step 1: Initialize Environment Files
Copy the example environment files:
```bash
# Root environment
cp .env.example .env

# Backend environment
cp backend/.env.example backend/.env

# Frontend environment
cp frontend/.env.example frontend/.env
```

### Option A: Local Development Environment (with Hot Reload & pgAdmin)
Run the following command using the root Makefile:
```bash
make up
```
This spins up:
* **PostgreSQL Database** at `localhost:5433`
* **FastAPI Backend API** at `localhost:8000` (with live reload)
* **React Frontend Dashboard** at `localhost:80`
* **pgAdmin Console** at `localhost:5050` (Username: `admin@careerpulse.dev`, Password: `admin`)

To stop the development environment:
```bash
make down
```

### Option B: Hardened Production-Grade Environment (No pgAdmin, Read-Only Filesystems)
Run the following Docker Compose command directly:
```bash
docker compose -f docker-compose.prod.yml up -d
```
To stop the production environment:
```bash
docker compose -f docker-compose.prod.yml down -v
```

---

## 2. Running Locally (Without Docker)

### Running the FastAPI Backend
1. Navigate to the root directory and activate the python virtual environment:
   ```bash
   source venv/bin/activate
   ```
2. Install pip dependencies:
   ```bash
   pip install -r backend/requirements.txt # or install standard requirements
   ```
3. Run the FastAPI development server:
   ```bash
   uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
4. Access the API health check at: `http://localhost:8000/health`
5. Access Swagger documentation at: `http://localhost:8000/docs`

### Running the React Frontend
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install npm dependencies:
   ```bash
   npm ci
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
4. Access the frontend app locally at `http://localhost:5173`.

---

## 3. Running Verification and Tests

We provide Makefile commands to run tests, checks, and cleanups easily.

* **Run Backend Unit Tests:**
  ```bash
  make backend-test
  ```
* **Run Frontend Unit Tests:**
  ```bash
  make frontend-test
  ```
* **Run Code Compiler & Linter Checks:**
  ```bash
  make lint
  ```
* **Clean up Temporary Files & Docker volumes:**
  ```bash
  make clean
  ```
