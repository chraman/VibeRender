# VibeRender

AI-powered YouTube automation SaaS platform.

## Tech Stack

- **Frontend**: Next.js 16 (App Router), TypeScript, Tailwind CSS
- **Backend**: Node.js with Drizzle ORM
- **Worker**: Python 3.12 with psycopg2
- **Database**: PostgreSQL
- **Cache**: Redis

## Project Structure

```
VibeRender/
├── web-app/          # Next.js frontend application
├── video-worker/     # Python worker for video processing
└── docker-compose.yml # Docker services (PostgreSQL, Redis)
```

## Setup Instructions

### 1. Start Docker Services

Start PostgreSQL and Redis using Docker Compose:

```bash
docker-compose up -d
```

This will start:
- PostgreSQL on `localhost:5432`
- Redis on `localhost:6379`

### 2. Set Up the Database

1. Create a `.env.local` file in `web-app/` directory:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/viberender
```

2. Generate and run database migrations:

```bash
cd web-app
npm run db:generate
npm run db:push
```

Or use the migrate command:
```bash
npm run db:migrate
```

### 3. Start the Next.js Frontend

```bash
cd web-app
npm install
npm run dev
```

The app will be available at `http://localhost:3000`

### 4. Start the Python Worker

1. Install Python dependencies:

```bash
cd video-worker
# Using uv (recommended)
uv pip install -r requirements.txt

# Or using pip
pip install -r requirements.txt
```

2. Run the worker:

```bash
python main.py
```

The worker will poll the database every 5 seconds for new jobs.

## Environment Variables

### Web App (`web-app/.env.local`)
- `DATABASE_URL` - PostgreSQL connection string

### Video Worker (`video-worker/`)
- `DB_HOST` - Database host (default: localhost)
- `DB_PORT` - Database port (default: 5432)
- `DB_NAME` - Database name (default: viberender)
- `DB_USER` - Database user (default: postgres)
- `DB_PASSWORD` - Database password (default: postgres)
- `POLL_INTERVAL` - Polling interval in seconds (default: 5)

## Usage

1. Open the web app at `http://localhost:3000`
2. Enter a topic in the "Generate Video" input field
3. Click "Generate Video" to create a new job
4. The Python worker will detect the new job and process it
5. Check the worker console to see processing messages

## Development

### Database Migrations

- Generate migrations: `npm run db:generate`
- Push schema changes: `npm run db:push`
- Run migrations: `npm run db:migrate`

### Project Rules

- Use Drizzle ORM for database operations
- Use TypeScript for all Node.js code
- Use Python 3.12 with `uv` for package management
- Follow shadcn/ui patterns for frontend components
- Use context managers in Python to avoid memory leaks
