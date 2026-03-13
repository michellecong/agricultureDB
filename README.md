# Agriculture Research DB

Extract and query experimental data from agricultural research papers (PDF → parse → LLM extract → normalize → PostgreSQL).

## Features

- **Multi-file upload**: Select and queue many PDFs at once; async processing (max 2 concurrent)
- **Pipeline**: Parse → Gemini extract → Normalize → PostgreSQL
- **Search & Charts**: Filter experiments, visualize effect sizes

## Local Development

```bash
# Backend (terminal 1)
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env      # edit with your DB + GEMINI_API_KEY
createdb agriculture
psql agriculture -f db/schema.sql
uvicorn api.main:app --reload

# Frontend (terminal 2)
cd frontend && npm install && npm start
```

- Backend: http://localhost:8000
- Frontend: http://localhost:3001 (hot reload, DevTools for debugging)

## Pre-deploy Checklist

Before pushing to GitHub:

1. **Confirm `.env` is ignored** – `git status` should not show `.env`
2. **Confirm no secrets in code** – API keys come from env vars only
3. **Test build locally**:
   ```bash
   pip install -r requirements.txt
   cd frontend && npm install && REACT_APP_API_URL=/api npm run build
   ```
4. **Optional: remove already-tracked data** (if you previously committed `data/`):
   ```bash
   git rm -r --cached data/pdfs data/parsed data/extracted data/normalized 2>/dev/null || true
   ```

## Deploy to Render (Free Tier)

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/michellecong/agricultureDB.git
git push -u origin main
```

### 2. Create Render Account

Sign up at [render.com](https://render.com) (free).

### 3. Deploy via Blueprint

1. In Render Dashboard → **New** → **Blueprint**
2. Connect your GitHub repo
3. Render will read `render.yaml` and create:
   - **PostgreSQL** database (free)
   - **Web Service** (Python + React)
4. Add **GEMINI_API_KEY** as a secret in the Web Service → Environment
5. After first deploy, run the schema:

   ```bash
   # Get connection string from Render DB dashboard → Connect
   psql "postgresql://..." -f db/schema.sql
   ```

   Or use Render's **Shell** (Web Service → Shell) and run:

   ```bash
   python -c "
   from db.connection import get_connection
   conn = get_connection()
   cur = conn.cursor()
   cur.execute(open('db/schema.sql').read())
   conn.commit()
   cur.close()
   conn.close()
   print('Schema applied')
   "
   ```

### 4. Manual Setup (Alternative)

If Blueprint fails, create manually:

1. **PostgreSQL** → New → Create database (free plan)
2. **Web Service** → New → Connect repo
   - **Build**: `pip install -r requirements.txt && cd frontend && npm install && REACT_APP_API_URL=/api npm run build`
   - **Start**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
   - **Env**: `DATABASE_URL` (from DB), `GEMINI_API_KEY` (secret)

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (Render auto-sets) |
| `GEMINI_API_KEY` | Google Gemini API key for LLM extraction |
