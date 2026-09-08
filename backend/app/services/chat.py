"""Orchestration du chatbot : seuil, plafonds, replis, assemblage de la réponse.

Cf. 12-specifications-techniques-chatbot-ia.md §4 et §6. Point le plus
important de ce module : le seuil de pertinence coupe l'appel au modèle de
génération *avant* qu'il ait lieu si le meilleur score est sous le seuil — la
règle « ne jamais inventer » repose sur ce mécanisme, jamais sur la seule
consigne donnée au modèle.

Aucune branche ne renvoie d'erreur visible au visiteur : un incident
technique, un plafond atteint ou une question hors périmètre produisent tous
une réponse utile, avec renvoi vers le formulaire de contact.
"""

import logging
from datetime import UTC, datetime
from functools import lru_cache

from app.config import Settings, get_settings
from app.repositories.knowledge import KnowledgeRepository
from app.schemas import ChatResponse, ChatStatus
from app.security.sanitizer import detect_prompt_injection
from app.services.embeddings import EmbeddingClient, EmbeddingError, GeminiEmbeddingClient
from app.services.llm import GeminiLLMClient, LLMClient, LLMError

logger = logging.getLogger(__name__)

_FALLBACK_MESSAGE = (
    "Je ne peux pas vous répondre pour le moment. Merci d'utiliser le "
    "formulaire de contact : Manon vous répondra directement."
)
_OUT_OF_SCOPE_MESSAGE = (
    "Je ne peux pas répondre à cette question avec certitude à partir des "
    "informations dont je dispose. Le formulaire de contact permet d'avoir "
    "une réponse précise, directement de la part de Manon."
)
_CAP_REACHED_MESSAGE = (
    "Le chatbot a atteint son quota d'utilisation pour aujourd'hui. Merci "
    "d'utiliser le formulaire de contact : Manon vous répondra directement."
)


@lru_cache
def get_knowledge_repository() -> KnowledgeRepository:
    settings = get_settings()
    return KnowledgeRepository.load(settings.knowledge_index_path, settings.gemini_embedding_model)


@lru_cache
def get_embedding_client() -> EmbeddingClient:
    return GeminiEmbeddingClient(get_settings())


@lru_cache
def get_llm_client() -> LLMClient:
    return GeminiLLMClient(get_settings())


class DailyUsageTracker:
    """Compteur en mémoire, remis à zéro à chaque changement de jour (UTC).

    Suffisant pour une instance unique (cf. limite de débit de /contact, même
    principe) ; ne se partage pas entre plusieurs instances si le service
    venait à être mis à l'échelle horizontalement.
    """

    def __init__(self) -> None:
        self._day: str | None = None
        self._count = 0

    def _roll_if_needed(self) -> None:
        today = datetime.now(UTC).date().isoformat()
        if today != self._day:
            self._day = today
            self._count = 0

    def try_consume(self, daily_cap: int) -> bool:
        self._roll_if_needed()
        if self._count >= daily_cap:
            return False
        self._count += 1
        return True

    def reset(self) -> None:
        self._day = None
        self._count = 0


_daily_usage = DailyUsageTracker()


async def answer_question(message: str, settings: Settings) -> ChatResponse:
    if detect_prompt_injection(message):
        logger.warning("Tentative de détournement détectée sur /chat (message non journalisé).")
        return ChatResponse(status=ChatStatus.OUT_OF_SCOPE, message=_OUT_OF_SCOPE_MESSAGE)

    if not _daily_usage.try_consume(settings.chat_daily_request_cap):
        logger.warning("Plafond quotidien du chatbot atteint : requête basculée en repli.")
        return ChatResponse(status=ChatStatus.OUT_OF_SCOPE, message=_CAP_REACHED_MESSAGE)

    embedding_client = get_embedding_client()
    try:
        vectors = await embedding_client.embed_batch([message], task_type="RETRIEVAL_QUERY")
        query_vector = vectors[0]
    except EmbeddingError:
        logger.exception("Échec du calcul d'embedding pour /chat.")
        return ChatResponse(status=ChatStatus.OUT_OF_SCOPE, message=_FALLBACK_MESSAGE)

    knowledge_repo = get_knowledge_repository()
    matches = knowledge_repo.search(query_vector, settings.chat_top_k)

    if not matches or matches[0].score < settings.chat_relevance_threshold:
        top_score = matches[0].score if matches else None
        logger.info("chat.metrics status=out_of_scope top_score=%s passages=0", top_score)
        return ChatResponse(status=ChatStatus.OUT_OF_SCOPE, message=_OUT_OF_SCOPE_MESSAGE)
    top_score = matches[0].score

    llm_client = get_llm_client()
    try:
        answer = await llm_client.generate(message, [m.passage for m in matches])
    except LLMError:
        logger.exception("Échec de la génération pour /chat.")
        return ChatResponse(status=ChatStatus.OUT_OF_SCOPE, message=_FALLBACK_MESSAGE)

    logger.info(
        "chat.metrics status=%s top_score=%.3f passages=%d",
        answer.status,
        top_score,
        len(matches),
    )
    return ChatResponse(status=answer.status, message=answer.message)


def reset_daily_usage_for_tests() -> None:
    """Isole les tests de l'état de module (compteur quotidien)."""
    _daily_usage.reset()
