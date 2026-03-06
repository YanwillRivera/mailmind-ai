from sqlmodel import SQLModel, create_engine, Session
from typing import Optional
from datetime import datetime
from sqlmodel import Field

# SQLite for dev — swap for PostgreSQL in production:
# DATABASE_URL = "postgresql://user:pass@host/dbname"
DATABASE_URL = "sqlite:///./mailmind.db"

engine = create_engine(DATABASE_URL, echo=False)

# ── Models ────────────────────────────────────────────────────────────────────

class EmailRecord(SQLModel, table=True):
    """Stores every processed email and its AI analysis."""
    id:                 Optional[int]      = Field(default=None, primary_key=True)
    gmail_id:           str                = Field(index=True, unique=True)
    sender_email:       str                = Field(default="")
    sender_name:        str                = Field(default="")
    subject:            str                = Field(default="")
    body_preview:       str                = Field(default="")
    received_at:        Optional[datetime] = Field(default=None)

    # AI analysis results
    categoria:          Optional[str]      = Field(default=None)
    urgencia:           Optional[str]      = Field(default=None)
    resumen:            Optional[str]      = Field(default=None)
    tono_remitente:     Optional[str]      = Field(default=None)
    accion_recomendada: Optional[str]      = Field(default=None)
    borrador_respuesta: Optional[str]      = Field(default=None)
    analyzed_at:        Optional[datetime] = Field(default=None)

    # Workflow state
    status:             str                = Field(default="pending")
    notion_page_id:     Optional[str]      = Field(default=None)


def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
