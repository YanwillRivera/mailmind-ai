"""
Notion Service
──────────────
Creates a page in a Notion database for each processed email.
This gives you a beautiful, shareable log — great for your portfolio demo.

Setup:
  1. Create a Notion integration at https://www.notion.so/my-integrations
  2. Share your database with the integration
  3. Add NOTION_API_KEY and NOTION_DATABASE_ID to your .env
"""
from notion_client import Client
from app.config import get_settings

URGENCY_COLORS = {
    "Alta":  "red",
    "Media": "yellow",
    "Baja":  "green",
}

CATEGORY_COLORS = {
    "Soporte Técnico":        "red",
    "Oportunidad de Negocio": "green",
    "Reclutamiento":          "blue",
    "Colaboración":           "purple",
    "Consulta General":       "orange",
    "Aviso / Información":    "gray",
}


def create_email_page(email: dict, analysis: dict) -> str:
    """
    Create a page in the Notion database for a processed email.
    Returns the Notion page ID.
    """
    settings = get_settings()
    if not settings.notion_api_key:
        return ""   # Notion not configured, skip silently

    notion = Client(auth=settings.notion_api_key)
    urgency_color  = URGENCY_COLORS.get(analysis["urgencia"], "default")
    category_color = CATEGORY_COLORS.get(analysis["categoria"], "default")

    page = notion.pages.create(
        parent={"database_id": settings.notion_database_id},
        properties={
            # These must match your Notion database column names exactly
            "Asunto": {
                "title": [{"text": {"content": email["subject"]}}]
            },
            "Remitente": {
                "rich_text": [{"text": {"content": f"{email['sender_name']} <{email['sender_email']}>"}}]
            },
            "Urgencia": {
                "select": {"name": analysis["urgencia"], "color": urgency_color}
            },
            "Categoría": {
                "select": {"name": analysis["categoria"], "color": category_color}
            },
            "Resumen": {
                "rich_text": [{"text": {"content": analysis["resumen"]}}]
            },
            "Acción": {
                "rich_text": [{"text": {"content": analysis["accion_recomendada"]}}]
            },
            "Estado": {
                "select": {"name": "Analizado", "color": "blue"}
            },
            "Recibido": {
                "date": {"start": email["received_at"].isoformat()}
            },
        },
        children=[
            # Full body preview block
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "📧 Email original"}}]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": email.get("body_preview", "")}}]}
            },
            # Key points
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "🔑 Puntos clave"}}]}
            },
            *[{
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": point}}]}
            } for point in analysis.get("puntos_clave", [])],
            # Draft reply
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "✉️ Borrador de respuesta"}}]}
            },
            {
                "object": "block",
                "type": "quote",
                "quote": {"rich_text": [{"text": {"content": analysis["borrador_respuesta"]}}]}
            },
        ]
    )
    return page["id"]
