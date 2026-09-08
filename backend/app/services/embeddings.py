"""Adaptateur embeddings, derrière une interface abstraite.

Cf. 12-specifications-techniques-chatbot-ia.md §2 et §7 : changer de
fournisseur ne doit toucher que ce module, et les tests injectent un double de
test à la place de ``GeminiEmbeddingClient`` — aucun test n'appelle Gemini.
"""

from abc import ABC, abstractmethod

import httpx
import numpy as np

from app.config import Settings


class EmbeddingClient(ABC):
    """Calcule les vecteurs d'un lot de textes, dans un ordre stable.

    ``task_type`` distingue l'indexation du corpus (``RETRIEVAL_DOCUMENT``,
    valeur par défaut, utilisée par ``scripts/build_index.py``) de
    l'encodage de la question posée à l'exécution (``RETRIEVAL_QUERY``,
    passé explicitement par ``app/services/chat.py``) — les deux embeddings
    d'une même paire question/passage sont légèrement différents dans ce
    modèle, ce qui améliore la pertinence de la recherche.
    """

    @abstractmethod
    async def embed_batch(
        self, texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> np.ndarray: ...


class EmbeddingError(Exception):
    """Échec de l'appel au fournisseur d'embeddings (réseau, quota, format)."""


class GeminiEmbeddingClient(EmbeddingClient):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def embed_batch(
        self, texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> np.ndarray:
        if not self._settings.gemini_api_key:
            raise EmbeddingError("GEMINI_API_KEY non configurée.")

        model = self._settings.gemini_embedding_model
        requests = [
            {
                "model": f"models/{model}",
                "content": {"parts": [{"text": text}]},
                "embedContentConfig": {"taskType": task_type},
            }
            for text in texts
        ]

        async with httpx.AsyncClient(
            base_url=self._settings.gemini_api_base_url,
            timeout=self._settings.gemini_timeout_seconds,
        ) as client:
            try:
                response = await client.post(
                    f"/models/{model}:batchEmbedContents",
                    headers={"x-goog-api-key": self._settings.gemini_api_key},
                    json={"requests": requests},
                )
                response.raise_for_status()
                payload = response.json()
            except httpx.HTTPError as exc:
                raise EmbeddingError(f"Appel Gemini (embeddings) échoué : {exc}") from exc

        try:
            return np.array(
                [item["values"] for item in payload["embeddings"]], dtype=np.float32
            )
        except (KeyError, TypeError) as exc:
            raise EmbeddingError(f"Réponse Gemini (embeddings) inattendue : {exc}") from exc
