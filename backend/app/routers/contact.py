import logging
import time
from collections import defaultdict
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError

from app.config import Settings, get_settings
from app.schemas import ContactFields
from app.services.email import send_contact_notification
from app.services.recaptcha import verify_recaptcha

logger = logging.getLogger(__name__)

router = APIRouter()

# Limite de débit basique en mémoire (par IP), en complément du honeypot et
# de reCAPTCHA : évite qu'un même client ne martèle l'endpoint. Suffisant
# pour une instance unique ; ne se partage pas entre plusieurs instances si
# le service venait à être mis à l'échelle horizontalement.
_RATE_LIMIT_WINDOW_SECONDS = 60
_RATE_LIMIT_MAX_REQUESTS = 5
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


def _rate_limit_ok(client_ip: str) -> bool:
    now = time.monotonic()
    window_start = now - _RATE_LIMIT_WINDOW_SECONDS
    recent = [t for t in _request_log[client_ip] if t > window_start]
    recent.append(now)
    _request_log[client_ip] = recent
    return len(recent) <= _RATE_LIMIT_MAX_REQUESTS


@router.post("/contact", status_code=200)
async def submit_contact(
    request: Request, settings: Annotated[Settings, Depends(get_settings)]
) -> dict[str, bool]:
    if not _rate_limit_ok(_client_ip(request)):
        raise HTTPException(
            status_code=429, detail="Trop de requêtes. Merci de réessayer plus tard."
        )

    payload = await request.json()

    # Honeypot puis reCAPTCHA sont vérifiés avant la validation des champs,
    # pour rejeter les requêtes suspectes sans détailler d'erreurs de
    # validation à un éventuel robot (cf. schéma de flux des spécifications
    # techniques).
    honeypot = (payload.get("website") or "").strip()
    if honeypot:
        raise HTTPException(status_code=400, detail="Requête rejetée.")

    if not await verify_recaptcha(payload.get("recaptcha_token"), settings):
        raise HTTPException(status_code=400, detail="Requête rejetée.")

    try:
        fields = ContactFields.model_validate(payload)
    except ValidationError as exc:
        errors = exc.errors(include_url=False, include_context=False)
        raise HTTPException(status_code=422, detail=errors) from exc

    try:
        await send_contact_notification(fields, settings)
    except Exception:
        logger.exception("Échec de l'envoi de l'email de notification.")
        raise HTTPException(
            status_code=502, detail="Échec de l'envoi. Merci de réessayer."
        ) from None

    return {"ok": True}
