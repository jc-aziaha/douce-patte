import logging

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)

RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"
RECAPTCHA_ACTION = "contact"


async def verify_recaptcha(token: str | None, settings: Settings) -> bool:
    """Vérifie un token reCAPTCHA v3 auprès de Google.

    Si aucune clé secrète n'est configurée, la vérification est ignorée en
    développement/test (seul le honeypot protège alors le formulaire), mais
    la requête est rejetée par sécurité en production : une clé manquante ne
    doit jamais désactiver silencieusement la protection en ligne.
    """
    if not settings.recaptcha_secret_key:
        if settings.environment == "production":
            logger.error(
                "RECAPTCHA_SECRET_KEY manquante en production : requête rejetée par sécurité."
            )
            return False
        logger.warning("RECAPTCHA_SECRET_KEY non configurée : vérification reCAPTCHA ignorée.")
        return True

    if not token:
        logger.warning("Aucun token reCAPTCHA transmis avec la requête.")
        return False

    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(
            RECAPTCHA_VERIFY_URL,
            data={"secret": settings.recaptcha_secret_key, "response": token},
        )
    payload = response.json()

    if not payload.get("success"):
        logger.warning(
            "Vérification reCAPTCHA refusée par Google : %s", payload.get("error-codes")
        )
        return False

    action = payload.get("action")
    score = float(payload.get("score", 0))


    if action != RECAPTCHA_ACTION:
        logger.warning(
            "Action reCAPTCHA inattendue : %s (attendue : %s)", action, RECAPTCHA_ACTION
        )
        return False

    if score < settings.recaptcha_min_score:
        logger.warning(
            "Score reCAPTCHA insuffisant : %s (seuil : %s)", score, settings.recaptcha_min_score
        )
        return False

    return True

# py