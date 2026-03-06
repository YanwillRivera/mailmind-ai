# MailMind AI — Email Automation Pipeline

> Automatically reads, analyzes and drafts replies to emails using Claude AI.  
> Built with Python · FastAPI · Gmail API · Anthropic Claude · Notion

---

## 🏗️ Architecture

```
Gmail Inbox
    ↓  (Gmail API — reads unread emails)
FastAPI Backend
    ↓  (Anthropic Claude — analyzes each email)
    ├── SQLite DB  (stores results)
    ├── Notion     (creates a page per email — optional)
    └── REST API   (serves data to the React dashboard)
         ↓
React Dashboard  (shows emails sorted by urgency)
```

---

## 🚀 Quick Start

### 1. Clone and install dependencies

```bash
git clone https://github.com/tu-usuario/mailmind-ai
cd mailmind-backend

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your API keys (see setup guides below)
```

### 3. Set up Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project → **Enable Gmail API**
3. Go to **Credentials** → **Create OAuth 2.0 Client ID** (Web application)
4. Add `http://localhost:8000/auth/callback` as an Authorized redirect URI
5. Copy the `client_id` and `client_secret` to your `.env`

### 4. Set up Notion (optional)

1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Create a new integration → copy the **API Key**
3. Create a database in Notion with these columns:
   - `Asunto` (Title), `Remitente` (Text), `Urgencia` (Select), `Categoría` (Select),
     `Resumen` (Text), `Acción` (Text), `Estado` (Select), `Recibido` (Date)
4. Share the database with your integration → copy the **Database ID** from the URL

### 5. Run the server

```bash
# Terminal 1 — API server
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Scheduler (polls Gmail every 60s)
python scheduler.py
```

### 6. Connect Gmail

Open your browser and go to:
```
http://localhost:8000/auth/login
```
Log in with Google and grant permissions. That's it.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/emails/` | List all processed emails (sorted by urgency) |
| `GET`  | `/emails/?urgencia=Alta` | Filter by urgency |
| `GET`  | `/emails/{id}` | Get one email with full analysis |
| `POST` | `/emails/run` | Trigger pipeline manually |
| `POST` | `/emails/{id}/reply` | Send the AI-drafted reply |
| `GET`  | `/emails/stats/summary` | Stats for dashboard header |
| `GET`  | `/auth/login` | Start Gmail OAuth flow |
| `GET`  | `/auth/status` | Check if Gmail is connected |

Interactive docs: `http://localhost:8000/docs`

---

## 📁 Project Structure

```
mailmind-backend/
├── app/
│   ├── main.py              # FastAPI app + middleware
│   ├── config.py            # Environment variables
│   ├── database.py          # SQLite models + engine
│   ├── routers/
│   │   ├── auth.py          # Google OAuth endpoints
│   │   └── emails.py        # Email CRUD + pipeline trigger
│   └── services/
│       ├── gmail_service.py  # Gmail API integration
│       ├── claude_service.py # Anthropic Claude analysis
│       ├── notion_service.py # Notion logging
│       └── pipeline.py       # Main orchestrator
├── scheduler.py             # Runs pipeline on a schedule
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚢 Deploy to Railway (free tier)

```bash
# Install Railway CLI
npm install -g @railway/cli

railway login
railway init
railway up
```

Set your environment variables in the Railway dashboard.  
Your API will be live at `https://your-app.railway.app`

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11 + FastAPI |
| AI | Anthropic Claude (claude-sonnet) |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Email | Gmail API via Google OAuth 2.0 |
| Logging | Notion API |
| Scheduler | `schedule` library |
| Deploy | Railway.app |

---

## 📈 Next Steps

- [ ] Add email reply directly from the dashboard
- [ ] Support multiple Gmail accounts
- [ ] Add Slack notifications for high-urgency emails
- [ ] Switch to PostgreSQL for production
- [ ] Add webhook support (instead of polling)
