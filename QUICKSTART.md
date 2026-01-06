# Quick Start Guide

## 🚀 Get Running in 5 Minutes

### 1. Start Docker Services
```bash
docker-compose up -d
```

### 2. Set Up Database

**Create `.env.local` in `web-app/` folder:**
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/viberender_new
```

**Then run:**
```bash
cd web-app
npm run db:setup
```

Or use Drizzle:
```bash
npm run db:push
```

### 3. Install Python Dependencies
```bash
cd video-worker
python -m pip install psycopg2-binary
```

### 4. Start Everything

**Terminal 1 - Frontend:**
```bash
cd web-app
npm run dev
```

**Terminal 2 - Worker:**
```bash
cd video-worker
python main.py
```

### 5. Test It!

1. Open http://localhost:3000
2. Enter a topic
3. Click "Generate Video"
4. Watch the worker console - you should see it processing!

---

## ✅ Verification Checklist

- [ ] Docker containers running (`docker ps` shows postgres and redis)
- [ ] `.env.local` exists in `web-app/` with `DATABASE_URL`
- [ ] Database schema created (`npm run db:setup` succeeded)
- [ ] Python dependencies installed (`python -m pip list | findstr psycopg2`)
- [ ] Frontend running on http://localhost:3000
- [ ] Worker running and showing "Polling database every 5 seconds..."

---

## 🐛 Common Issues

**Python worker won't start:**
- Install: `python -m pip install psycopg2-binary`
- If that fails: `python -m pip install --only-binary :all: psycopg2-binary`

**Database connection errors:**
- Check Docker is running: `docker ps`
- Verify `.env.local` exists in `web-app/`
- Run `npm run db:setup` to create tables

**Frontend can't connect:**
- Restart dev server after creating `.env.local`
- Check `DATABASE_URL` format is correct

---

For detailed setup, see [SETUP.md](./SETUP.md)

