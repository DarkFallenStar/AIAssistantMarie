import re
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from app.schemas.webhook import ExtractedBankTransaction
from app.services.llm import get_llm_service, BaseLLMService


BANK_EXTRACTION_SYSTEM_PROMPT = """
Eres un analizador financiero especializado en procesar notificaciones bancarias de texto no estructurado.
Tu tarea es analizar el texto de la notificación y extraer un único objeto JSON estructurado con la información de la transacción.

El formato del JSON DEBE coincidir exactamente con este esquema:
{
    "amount": <float>,
    "currency": "<string, ej: COP, USD, EUR>",
    "merchant": "<string, nombre del comercio o persona>",
    "date": "<string en formato ISO o fecha legible>",
    "payment_method": "<string: 'credit_card', 'debit_card', 'transfer', 'cash'>",
    "category": "<string: 'food', 'transport', 'shopping', 'utilities', 'entertainment', 'health', 'general'>",
    "type": "<string: 'expense' o 'income'>"
}

Reglas estrictas:
1. Responde ÚNICAMENTE con el objeto JSON válido.
2. No agregues explicaciones, preámbulos ni bloques de texto adicionales fuera del JSON.
3. El monto debe ser un número positivo (float). Si dice '$45.000', el monto es 45000.0.
4. Si la moneda no se especifica pero tiene signo '$' en un contexto hispano, usa 'COP'. Si dice 'USD' o 'dólares', usa 'USD'.
"""


class BankWebhookExtractor:
    """
    Service for extracting structured financial transaction details from bank notifications.
    Uses LLM Structured Output with a robust deterministic heuristic fallback.
    """

    def __init__(self, llm_service: Optional[BaseLLMService] = None):
        self._llm = llm_service

    def get_llm(self) -> BaseLLMService:
        if self._llm is None:
            return get_llm_service()
        return self._llm

    async def extract_from_text(self, text: str) -> ExtractedBankTransaction:
        clean_text = (text or "").strip()
        if not clean_text:
            raise ValueError("El texto de la notificación bancaria está vacío.")

        # 1. Intentar extracción con LLM (Structured Output)
        try:
            llm = self.get_llm()
            user_prompt = f"Notificación bancaria recibida:\n\"{clean_text}\"\n\nExtrae la transacción en formato JSON estricto."
            llm_response = await llm.generate(
                prompt=user_prompt,
                system_prompt=BANK_EXTRACTION_SYSTEM_PROMPT
            )
            raw_output = llm_response.text.strip()
            
            # Limpiar bloques de código markdown ```json ... ```
            cleaned_json = raw_output
            if "```" in cleaned_json:
                cleaned_json = re.sub(r"^```(?:json)?\s*", "", cleaned_json, flags=re.MULTILINE)
                cleaned_json = re.sub(r"\s*```$", "", cleaned_json, flags=re.MULTILINE).strip()

            data = json.loads(cleaned_json)
            # Validar y normalizar con el esquema Pydantic
            raw_date = data.get("date")
            if not raw_date or not isinstance(raw_date, str) or raw_date.strip().lower() in ["none", "null", ""]:
                date_val = datetime.now(timezone.utc).isoformat()
            else:
                date_val = raw_date.strip()

            return ExtractedBankTransaction(
                amount=abs(float(data.get("amount", 0))),
                currency=str(data.get("currency", "COP")).upper(),
                merchant=str(data.get("merchant", "Comercio")),
                date=date_val,
                payment_method=str(data.get("payment_method", "credit_card")),
                category=str(data.get("category", "general")).lower(),
                type=str(data.get("type", "expense")).lower()
            )
        except Exception as exc:
            print(f"[WEBHOOK-EXTRACTOR] LLM extraction failed or timed out ({exc}). Using heuristic regex fallback.")
            return self.heuristic_extract(clean_text)

    def heuristic_extract(self, text: str) -> ExtractedBankTransaction:
        """
        Deterministic regex and rule-based extractor for offline or fallback operation.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        lower_text = text.lower()

        # 1. Type
        tx_type = "expense"
        if any(term in lower_text for term in ["transferencia recibida", "abono", "ingreso", "nomina", "nómina", "consignacion", "consignación", "recibiste"]):
            tx_type = "income"

        # 2. Currency
        currency = "COP"
        if "usd" in lower_text or "dolares" in lower_text or "dólares" in lower_text:
            currency = "USD"
        elif "eur" in lower_text or "euros" in lower_text:
            currency = "EUR"

        # 3. Amount
        # Matches formats: $45.000, $45,000.50, 45000, $120.000 COP, etc.
        amount = 0.0
        amount_match = re.search(r'\$\s*([\d\.,]+)', text)
        if amount_match:
            raw_num = amount_match.group(1).strip()
            # Spanish/Colombian format: $45.000 -> 45000
            if '.' in raw_num and ',' not in raw_num:
                # If only dots and followed by 3 digits (e.g. 45.000), it's thousands
                parts = raw_num.split('.')
                if len(parts[-1]) == 3:
                    raw_num = "".join(parts)
                else:
                    raw_num = raw_num.replace('.', '.')
            elif ',' in raw_num and '.' in raw_num:
                # 45.000,50 or 45,000.50
                if raw_num.rfind(',') > raw_num.rfind('.'):
                    raw_num = raw_num.replace('.', '').replace(',', '.')
                else:
                    raw_num = raw_num.replace(',', '')
            elif ',' in raw_num:
                if len(raw_num.split(',')[-1]) == 3:
                    raw_num = raw_num.replace(',', '')
                else:
                    raw_num = raw_num.replace(',', '.')

            try:
                amount = abs(float(raw_num))
            except ValueError:
                amount = 0.0
        else:
            # Match plain numbers
            num_match = re.search(r'\b(\d+(?:[\.,]\d+)?)\b', text)
            if num_match:
                try:
                    amount = abs(float(num_match.group(1).replace(',', '.')))
                except ValueError:
                    amount = 0.0

        # 4. Merchant
        merchant = "Comercio"
        en_match = re.search(r'\ben\s+([A-Za-z0-9\sáéíóúÁÉÍÓÚñÑ\.\-&]+?)(?:\s+(?:con|el|por|vía|via|desde|para)|$)', text, re.IGNORECASE)
        if en_match:
            candidate = en_match.group(1).strip()
            if candidate and len(candidate) > 1 and candidate.lower() not in ["tarjeta", "cuenta", "efectivo", "banco"]:
                merchant = candidate
        else:
            other_match = re.search(r'\b(?:de|a)\s+([A-Za-z0-9\sáéíóúÁÉÍÓÚñÑ\.\-&]+?)(?:\s+(?:con|el|por|vía|via|desde|para)|$)', text, re.IGNORECASE)
            if other_match:
                candidate = other_match.group(1).strip()
                if candidate and len(candidate) > 1 and candidate.lower() not in ["tarjeta", "cuenta", "efectivo", "banco", "compra", "realizada"]:
                    merchant = candidate

        # 5. Payment method
        payment_method = "credit_card"
        if any(term in lower_text for term in ["credito", "crédito", "tc"]):
            payment_method = "credit_card"
        elif any(term in lower_text for term in ["debito", "débito", "td"]):
            payment_method = "debit_card"
        elif any(term in lower_text for term in ["transferencia", "pse", "nequi", "daviplata"]):
            payment_method = "transfer"
        elif "efectivo" in lower_text:
            payment_method = "cash"

        # 6. Category
        category = "general"
        if any(term in lower_text for term in ["restaurante", "comida", "almuerzo", "cena", "d1", "exito", "éxito", "metro", "jumbo", "supermercado", "cafeteria", "cafetería", "burger", "pizza"]):
            category = "food"
        elif any(term in lower_text for term in ["uber", "didi", "taxi", "gasolina", "combustible", "peaje", "transporte", "metro", "bus"]):
            category = "transport"
        elif any(term in lower_text for term in ["netflix", "spotify", "cine", "teatro", "concierto", "juego", "steam"]):
            category = "entertainment"
        elif any(term in lower_text for term in ["farmacia", "drogueria", "droguería", "salud", "medico", "médico", "hospital", "clinica", "clínica"]):
            category = "health"
        elif any(term in lower_text for term in ["luz", "agua", "gas", "internet", "claro", "tigo", "movistar", "servicios"]):
            category = "utilities"
        elif any(term in lower_text for term in ["tienda", "ropa", "zapatos", "mall", "centro comercial", "falabella", "zara"]):
            category = "shopping"

        return ExtractedBankTransaction(
            amount=amount,
            currency=currency,
            merchant=merchant,
            date=now_iso,
            payment_method=payment_method,
            category=category,
            type=tx_type
        )
