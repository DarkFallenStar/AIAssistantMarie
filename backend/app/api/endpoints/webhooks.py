from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from app.schemas.webhook import BankWebhookPayload, BankWebhookResponse
from app.services.webhook_extractor import BankWebhookExtractor
from app.tools.transaction_tool import TransactionTools
from app.core.config import settings

router = APIRouter()
_extractor_instance = BankWebhookExtractor()
_transaction_tools = TransactionTools()


def get_webhook_extractor() -> BankWebhookExtractor:
    return _extractor_instance


def set_webhook_extractor(extractor: BankWebhookExtractor):
    global _extractor_instance
    _extractor_instance = extractor


def get_transaction_tools() -> TransactionTools:
    return _transaction_tools


def set_transaction_tools(tools: TransactionTools):
    global _transaction_tools
    _transaction_tools = tools


@router.post("/bank", response_model=BankWebhookResponse, summary="Webhook de transacciones bancarias (Fase 14)")
async def bank_webhook(
    payload: BankWebhookPayload,
    x_webhook_secret: Optional[str] = Header(None)
):
    """
    Recibe notificaciones bancarias entrantes (compras, transferencias, débitos),
    valida la carga útil, extrae los detalles mediante Structured Output (LLM / Heurístico)
    y registra la transacción en PostgreSQL (tabla 'transactions').
    """
    # 1. Validar el webhook
    source = (payload.source or "").strip()
    if not source:
        raise HTTPException(status_code=400, detail="El campo 'source' es obligatorio en el webhook.")

    content = (payload.content or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="El campo 'content' no puede estar vacío.")

    # 2. Extraer información mediante Structured Output
    extractor = get_webhook_extractor()
    try:
        extracted = await extractor.extract_from_text(content)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error extrayendo información estructurada del webhook: {exc}"
        )

    # 3. Crear la transacción en PostgreSQL
    tools = get_transaction_tools()
    tx_description = f"Compra en {extracted.merchant} vía {extracted.payment_method}" if extracted.type == "expense" else f"Ingreso desde {extracted.merchant}"
    
    tx_result = await tools.create_transaction(
        amount=extracted.amount,
        type=extracted.type,
        category=extracted.category,
        description=tx_description,
        merchant=extracted.merchant,
        currency=extracted.currency,
        source="webhook_bank",
        transaction_date=extracted.date,
        user_id=payload.user_id,
        metadata={
            "payment_method": extracted.payment_method,
            "raw_content": payload.content,
            "source": payload.source
        }
    )

    if not tx_result.success or not tx_result.data:
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo guardar la transacción en la base de datos: {tx_result.message}"
        )

    return BankWebhookResponse(
        status="success",
        message="Transacción bancaria procesada y registrada exitosamente.",
        transaction_id=tx_result.data["id"],
        extracted=extracted
    )


@router.get("/bank/recent", summary="Consultar transacciones bancarias recientes procesadas por webhook")
async def get_recent_bank_transactions(
    limit: int = 10,
    user_id: Optional[str] = None
):
    """
    Retorna las transacciones registradas con source='webhook_bank' para
    monitoreo en tiempo real desde la aplicación móvil o paneles de automatización.
    """
    tools = get_transaction_tools()
    res = await tools.get_transactions(limit=limit, user_id=user_id, source="webhook_bank")
    if not res.success or not res.data:
        return {"status": "success", "total": 0, "transactions": []}

    return {
        "status": "success",
        "total": res.data.get("count", 0),
        "transactions": res.data.get("transactions", [])
    }

