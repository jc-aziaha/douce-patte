"""Doubles de test pour le chatbot — aucun ne contacte un fournisseur réel.

Cf. 12-specifications-techniques-chatbot-ia.md §11 : « les tests s'exécutent
hors ligne, sans clé d'API. C'est ce que permet l'injection des adaptateurs. »
"""

import re
import unicodedata
import zlib

import numpy as np

from app.repositories.knowledge import Passage
from app.schemas import ChatStatus, LLMAnswer
from app.services.embeddings import EmbeddingClient, EmbeddingError
from app.services.llm import LLMClient, LLMError

_STOPWORDS = {
    "le", "la", "les", "de", "des", "du", "un", "une", "et", "est", "pour",
    "vous", "votre", "vos", "je", "j", "mes", "mon", "ma", "dans", "avec",
    "que", "qui", "ce", "cette", "ces", "sur", "au", "aux", "en", "a", "d",
    "l", "se", "son", "sa", "ses", "il", "elle", "on", "sont", "être", "avoir",
    "y", "ne", "pas", "plus", "tres", "bien", "si", "ou", "mais", "comment",
    "quel", "quelle", "quels", "quelles", "faites", "vous-",
}
_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _bucket(token: str, dim: int) -> int:
    # zlib.crc32 est déterministe d'un run à l'autre, contrairement à hash()
    # (salé aléatoirement par process pour les str) : nécessaire pour que ce
    # test soit reproductible.
    return zlib.crc32(token.encode("utf-8")) % dim


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def _tokenize(text: str) -> list[str]:
    ascii_text = _strip_accents(text.lower())
    return [t for t in _TOKEN_RE.findall(ascii_text) if t not in _STOPWORDS and len(t) > 2]


class HashingVectorizer:
    """Vectoriseur lexical TF-IDF (hashing trick) — outil de test uniquement.

    Approxime le chevauchement de vocabulaire entre une question et un
    passage, pour vérifier le mécanisme de seuil/orchestration sans dépendre
    d'un modèle d'embeddings réel. La pondération IDF réduit le poids des mots
    génériques du corpus (« chien », « garde »...), qui sinon rapprochent à
    tort des passages sans lien réel. Ne préjuge en rien de la qualité de la
    similarité sémantique du modèle Mistral utilisé en production.
    """

    def __init__(self, dim: int = 8192) -> None:
        self._dim = dim
        self._idf: np.ndarray | None = None

    def fit(self, corpus_texts: list[str]) -> None:
        """Calcule l'IDF par bucket à partir du corpus, une fois pour toutes."""
        doc_freq = np.zeros(self._dim, dtype=np.float32)
        for text in corpus_texts:
            buckets = {_bucket(token, self._dim) for token in _tokenize(text)}
            for bucket in buckets:
                doc_freq[bucket] += 1.0
        n_docs = len(corpus_texts)
        self._idf = np.log((1.0 + n_docs) / (1.0 + doc_freq)) + 1.0

    def _term_frequencies(self, text: str) -> np.ndarray:
        vector = np.zeros(self._dim, dtype=np.float32)
        for token in _tokenize(text):
            vector[_bucket(token, self._dim)] += 1.0
        return vector

    def vectorize(self, text: str) -> np.ndarray:
        tf = self._term_frequencies(text)
        return tf if self._idf is None else tf * self._idf

    def vectorize_batch(self, texts: list[str]) -> np.ndarray:
        return np.array([self.vectorize(t) for t in texts], dtype=np.float32)


class FakeEmbeddingClient(EmbeddingClient):
    """Renvoie des vecteurs pré-déterminés, indexés par le texte exact reçu."""

    def __init__(
        self,
        vectors_by_text: dict[str, list[float]] | None = None,
        dim: int = 2,
        raise_error: bool = False,
    ) -> None:
        self._vectors_by_text = vectors_by_text or {}
        self._dim = dim
        self._raise_error = raise_error

    async def embed_batch(
        self, texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> np.ndarray:
        if self._raise_error:
            raise EmbeddingError("Panne simulée du fournisseur d'embeddings.")
        default = [0.0] * self._dim
        return np.array(
            [self._vectors_by_text.get(t, default) for t in texts], dtype=np.float32
        )


class FakeLLMClient(LLMClient):
    def __init__(
        self,
        answer: LLMAnswer | None = None,
        raise_error: bool = False,
        invalid_output: bool = False,
    ) -> None:
        self._answer = answer or LLMAnswer(status=ChatStatus.ANSWERED, message="Réponse simulée.")
        self._raise_error = raise_error
        self._invalid_output = invalid_output

    async def generate(self, question: str, passages: list[Passage]) -> LLMAnswer:
        if self._raise_error:
            raise LLMError("Panne simulée du fournisseur de génération.")
        if self._invalid_output:
            raise LLMError("Sortie non conforme simulée.")
        return self._answer
