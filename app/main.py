from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import emails, auth
from app.database import init_db

app = FastAPI(
    title="MailMind AI",
    description="Email automation pipeline powered by Claude",
    version="1.0.0"
)

# Allow requests from your frontend (localhost in dev, your domain in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    init_db()

app.include_router(auth.router,   prefix="/auth",   tags=["Auth"])
app.include_router(emails.router, prefix="/emails", tags=["Emails"])

@app.get("/")
def root():
    return {"status": "MailMind AI is running 🚀"}
