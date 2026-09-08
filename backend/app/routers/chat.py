import logging
import time
from collections import defaultdict
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError

from app.config import Settings, get_settings
from app.schemas import ChatRequest, ChatResponse
from app.security.sanitizer import InvalidMessageError, validate_message
from app.services.chat import answer_question

logger = logging.getLogger(__name__)

router = APIRouter()

# Limite de débit dédiée à /chat, distincte de celle de /contact : une
# conversation implique plusieurs messages mais reste bornée (cf.
# 12-specifications-techniques-chatbot-ia.md §8).
_request_log: dict[str, list[float]] = defaultdict(list)


def _client_ip(request: Request) -> str:
    # Le premier maillon de X-Forwarded-For est fourni par le client et donc
    # falsifiable à volonté (il suffit d'envoyer son propre en-tête pour
    # changer d'« IP » à chaque requête et contourner la limite de débit).
    # Render n'ajoute qu'un seul relais devant l'application : c'est le
    # DERNIER maillon, que le client ne peut pas usurper, qui reflète l'IP
    # réellement observée par ce relais.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


def _rate_limit_ok(client_ip: str, settings: Settings) -> bool:
    now = time.monotonic()
    window_start = now - settings.chat_rate_limit_window_seconds
    recent = [t for t in _request_log[client_ip] if t > window_start]
    recent.append(now)
    _request_log[client_ip] = recent
    return len(recent) <= settings.chat_rate_limit_max_requests


@router.post("/chat", status_code=200)
async def chat(
    request: Request, settings: Annotated[Settings, Depends(get_settings)]
) -> ChatResponse:
    if not _rate_limit_ok(_client_ip(request), settings):
        raise HTTPException(
            status_code=429, detail="Trop de messages. Merci de réessayer plus tard."
        )

    payload = await request.json()

    try:
        fields = ChatRequest.model_validate(payload)
    except ValidationError as exc:
        errors = exc.errors(include_url=False, include_context=False)
        raise HTTPException(status_code=422, detail=errors) from exc

    try:
        message = validate_message(fields.message, settings.chat_max_message_length)
    except InvalidMessageError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return await answer_question(message, settings)
