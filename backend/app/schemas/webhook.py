from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from app.core.database import is_valid_uuid


class BankWebhookPayload(BaseModel):
    source: str = Field(..., max_length=100, example="bank", description="Origen de la notificación bancaria (ej: 'bank')")
    content: str = Field(..., max_length=2000, example="Compra realizada por $45.000 en Tienda D1 con tarjeta debito", description="Texto de la notificación")
    user_id: Optional[str] = Field(default=None, description="UUID del usuario receptor opcional")

    @field_validator("user_id")
    @classmethod
    def validate_optional_uuid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip():
            cleaned = v.strip()
            if not is_valid_uuid(cleaned):
                raise ValueError(f"user_id '{cleaned}' no es un UUID válido.")
            return cleaned
        return None


class ExtractedBankTransaction(BaseModel):
    amount: float = Field(..., example=45000.0, description="Monto numérico de la transacción")
    currency: str = Field(default="COP", example="COP", description="Código de moneda (COP, USD, EUR, etc.)")
    merchant: str = Field(..., example="Tienda D1", description="Nombre del comercio o beneficiario")
    date: str = Field(..., example="2026-09-21T12:00:00Z", description="Fecha y hora de la transacción en formato ISO o fecha legible")
    payment_method: str = Field(default="credit_card", example="credit_card", description="Medio de pago (credit_card, debit_card, transfer, etc.)")
    category: str = Field(default="general", example="food", description="Categoría asignada a la transacción")
    type: str = Field(default="expense", example="expense", description="Tipo de movimiento: 'expense' o 'income'")


class BankWebhookResponse(BaseModel):
    status: str = Field(default="success", description="Estado del procesamiento")
    message: str = Field(..., description="Mensaje descriptivo del resultado")
    transaction_id: str = Field(..., description="ID de la transacción registrada en PostgreSQL")
    extracted: ExtractedBankTransaction = Field(..., description="Datos estructurados extraídos de la notificación")
