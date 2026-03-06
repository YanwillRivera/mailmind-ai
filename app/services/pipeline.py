"""
Email Pipeline
──────────────
This is the heart of MailMind.
Orchestrates the full automation flow:
  Gmail → Claude → Database → Notion

Call run_pipeline() manually or from a scheduler.
"""
from datetime import datetime
from sqlmodel import Session, select

from app.database import engine, EmailRecord
from app.services.gmail_service  import fetch_unread_emails, mark_as_read
from app.services.claude_service  import analyze_email
from app.services.notion_service  import create_email_page


def run_pipeline(max_emails: int = 5) -> dict:
    """
    Full pipeline run:
      1. Fetch unread emails from Gmail
      2. Skip already-processed ones (check DB)
      3. Analyze each with Claude
      4. Save to SQLite database
      5. Create Notion page
      6. Mark email as read in Gmail

    Returns a summary dict.
    """
    print(f"\n🚀 Pipeline started at {datetime.utcnow().isoformat()}")
    summary = {"fetched": 0, "processed": 0, "skipped": 0, "errors": 0}

    # ── Step 1: Fetch unread emails ──────────────────────────────────────────
    try:
        raw_emails = fetch_unread_emails(max_results=max_emails)
    except ValueError as e:
        print(f"❌ Gmail not connected: {e}")
        return {"error": str(e)}

    summary["fetched"] = len(raw_emails)
    print(f"📬 Fetched {len(raw_emails)} unread emails")

    with Session(engine) as session:
        for email in raw_emails:
            gmail_id = email["gmail_id"]

            # ── Step 2: Skip if already processed ───────────────────────────
            existing = session.exec(
                select(EmailRecord).where(EmailRecord.gmail_id == gmail_id)
            ).first()

            if existing:
                print(f"  ⏭  Skipping already-processed: {email['subject'][:50]}")
                summary["skipped"] += 1
                continue

            print(f"  🧠 Analyzing: {email['subject'][:60]}")

            try:
                # ── Step 3: Claude analysis ──────────────────────────────────
                analysis = analyze_email(email)

                # ── Step 4: Save to DB ───────────────────────────────────────
                record = EmailRecord(
                    gmail_id          = gmail_id,
                    sender_email      = email["sender_email"],
                    sender_name       = email["sender_name"],
                    subject           = email["subject"],
                    body_preview      = email["body_preview"],
                    received_at       = email["received_at"],
                    categoria         = analysis["categoria"],
                    urgencia          = analysis["urgencia"],
                    resumen           = analysis["resumen"],
                    tono_remitente    = analysis["tono_remitente"],
                    accion_recomendada= analysis["accion_recomendada"],
                    borrador_respuesta= analysis["borrador_respuesta"],
                    analyzed_at       = datetime.utcnow(),
                    status            = "analyzed",
                )

                # ── Step 5: Create Notion page ───────────────────────────────
                try:
                    notion_id = create_email_page(email, analysis)
                    record.notion_page_id = notion_id
                except Exception as e:
                    print(f"    ⚠️  Notion failed (non-critical): {e}")

                session.add(record)
                session.commit()

                # ── Step 6: Mark as read in Gmail ────────────────────────────
                mark_as_read(gmail_id)

                summary["processed"] += 1
                print(f"    ✅ Done — Urgencia: {analysis['urgencia']} | {analysis['categoria']}")

            except Exception as e:
                print(f"    ❌ Error processing {gmail_id}: {e}")
                summary["errors"] += 1

    print(f"\n✅ Pipeline complete: {summary}")
    return summary
