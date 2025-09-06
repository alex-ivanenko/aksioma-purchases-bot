# bot/airtable_client.py
import httpx
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any

from .config import AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME

class AirtableClient:
    def __init__(self):
        self.base_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
        self.headers = {
            "Authorization": f"Bearer {AIRTABLE_API_KEY}",
            "Content-Type": "application/json"
        }

    async def create_record(self, fields: Dict[str, Any]) -> Dict:
        """
        Создаёт новую запись в Airtable.
        Автоматически добавляет поле "Дата создания", если его нет.
        """
        # Удаляем "Дата создания", если вдруг передано — оно вычисляемое
        if "Дата создания" in fields:
            del fields["Дата создания"]  # Удаляем, если вдруг передано

        payload = {
            "records": [
                {
                    "fields": fields
                }
            ]
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.base_url, json=payload, headers=self.headers)
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            # Пытаемся получить JSON, но если не получится — используем текст
            try:
                error_data = e.response.json()
                # Если это словарь — извлекаем сообщение
                if isinstance(error_data, dict):
                    error_message = error_data.get("error", {}).get("message", str(e))
                else:
                    # Если JSON вернул не словарь (например, строку) — используем как есть
                    error_message = str(error_data)
            except Exception:
                # Если вообще не JSON — берём текст ответа
                error_message = e.response.text or str(e)

            raise Exception(f"Airtable API Error: {error_message}")

        except Exception as e:
            raise Exception(f"Network error: {str(e)}")
