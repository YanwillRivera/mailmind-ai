import json
import httpx
from datetime import datetime
from app.config import get_settings


def analyze_email(email: dict) -> dict:
    settings = get_settings()

    prompt = f"""Analiza este email profesional. Responde SOLO con JSON válido, sin texto adicional.

De: {email['sender_name']} <{email['sender_email']}>
Asunto: {email['subject']}
Cuerpo:
{email['body'][:1500]}

JSON requerido:
{{
  "categoria": "Soporte Técnico | Oportunidad de Negocio | Reclutamiento | Colaboración | Consulta General | Aviso / Información",
  "urgencia": "Alta | Media | Baja",
  "resumen": "máximo 15 palabras",
  "puntos_clave": ["punto 1", "punto 2", "punto 3"],
  "tono_remitente": "Formal | Informal | Urgente | Amigable",
  "accion_recomendada": "una frase de acción concreta",
  "borrador_respuesta": "borrador profesional de 3-4 líneas"
}}"""

    with httpx.Client() as client:
        response = client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30.0
        )
        response.raise_for_status()
        data = response.json()

    raw = data["content"][0]["text"].strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    result = json.loads(raw)
    result["analyzed_at"] = datetime.utcnow().isoformat()
    return result