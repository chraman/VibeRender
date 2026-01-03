# VibeRender Setup Guide

Step-by-step instructions to get VibeRender running.

## Prerequisites

- Docker Desktop installed and running
- Node.js 18+ installed
- Python 3.12+ installed
- npm or yarn package manager

## Step 1: Start Docker Services

First, start PostgreSQL and Redis using Docker Compose:

```bash
docker-compose up -d
```

Verify the containers are running:
```bash
docker ps
```

You should see `viberender-postgres` and `viberender-redis` running.

## Step 2: Set Up the Database

### 2.1 Create Environment File

Create a `.env.local` file in the `web-app/` directory:

**Windows (PowerShell):**
```powershell
cd web-app
New-Item -Path .env.local -ItemType File
```

**Mac/Linux:**
```bash
cd web-app
touch .env.local
```

### 2.2 Add Database URL

Open `web-app/.env.local` and add:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/viberender
```

### 2.3 Create Database Schema

Run the Drizzle push command to create the tables:

```bash
cd web-app
npm run db:push
```

You should see output like:
```
✓ No schema changes, nothing to migrate
```

Or if it's the first time:
```
✓ Pushed schema to database
```

**Alternative: Manual SQL Setup**

If `db:push` doesn't work, you can connect to PostgreSQL directly:

```bash
# Connect to PostgreSQL (password is 'postgres')
docker exec -it viberender-postgres psql -U postgres -d viberender
```

Then run:
```sql
CREATE TABLE IF NOT EXISTS jobs (
  id SERIAL PRIMARY KEY,
  topic TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

Type `\q` to exit.

## Step 3: Set Up Python Worker

### 3.1 Install Python Dependencies

**Option A: Using pip (if available)**
```bash
cd video-worker
python -m pip install psycopg2-binary
```

**Option B: Using uv (recommended per project rules)**
```bash
cd video-worker
uv pip install psycopg2-binary
```

**Option C: If you get build errors on Windows**

Try installing a pre-built wheel:
```bash
cd video-worker
python -m pip install --only-binary :all: psycopg2-binary
```

Or use an alternative package:
```bash
python -m pip install psycopg2-binary --prefer-binary
```

### 3.2 Test the Worker

Run the worker to verify it connects:

```bash
cd video-worker
python main.py
```

You should see:
```
VibeRender Video Worker started
Polling database every 5 seconds...
Database: viberender@localhost:5432
Press Ctrl+C to stop
```

If you see connection errors, make sure:
- Docker containers are running (`docker ps`)
- Database is accessible on port 5432
- The database `viberender` exists

## Step 4: Start the Next.js Frontend

```bash
cd web-app
npm install
npm run dev
```

The app will be available at `http://localhost:3000`

## Step 5: Test the Full Flow

1. Open `http://localhost:3000` in your browser
2. Enter a topic (e.g., "How to make pizza")
3. Click "Generate Video"
4. Check the Python worker console - you should see:
   ```
   Found 1 new job(s)
   Processing video for: How to make pizza (Job ID: 1)
   Completed processing job 1 for topic: How to make pizza
   ```

## Troubleshooting

### Python Worker Can't Connect to Database

1. Check if Docker containers are running:
   ```bash
   docker ps
   ```

2. Test database connection:
   ```bash
   docker exec -it viberender-postgres psql -U postgres -d viberender -c "SELECT 1;"
   ```

3. Verify environment variables in `video-worker/` (or use defaults):
   - `DB_HOST=localhost`
   - `DB_PORT=5432`
   - `DB_NAME=viberender`
   - `DB_USER=postgres`
   - `DB_PASSWORD=postgres`

### Database Schema Not Created

1. Check if `.env.local` exists in `web-app/`
2. Verify `DATABASE_URL` is correct
3. Try running `npm run db:push` again
4. Check for errors in the console

### psycopg2 Installation Fails on Windows

This is a common issue. Try:

1. Install Visual C++ Build Tools (if missing)
2. Use pre-built wheels: `python -m pip install --only-binary :all: psycopg2-binary`
3. Or use `uv` package manager as recommended in project rules

### Next.js Can't Connect to Database

1. Verify `.env.local` exists in `web-app/`
2. Check `DATABASE_URL` format is correct
3. Restart the Next.js dev server after creating `.env.local`
4. Ensure Docker containers are running

## Quick Start Commands Summary

```bash
# 1. Start services
docker-compose up -d

# 2. Setup database (in web-app/)
cd web-app
# Create .env.local with DATABASE_URL
npm run db:push

# 3. Start frontend (in web-app/)
npm run dev

# 4. Start worker (in video-worker/)
cd ../video-worker
python -m pip install psycopg2-binary
python main.py
```

