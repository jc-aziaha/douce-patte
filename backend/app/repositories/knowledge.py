"""Chargement de l'index de connaissance et recherche par similarité.

Masque le moteur de recherche (cosinus en mémoire, numpy) au reste de
l'application — cf. 12-specifications-techniques-chatbot-ia.md §3 et §7. Si le
corpus changeait un jour d'ordre de grandeur, seule cette classe serait à
remplacer.

L'index est un fichier ``.npz`` versionné dans le dépôt (voir
``scripts/build_index.py``), construit une seule fois en local. Le nom du
modèle d'embeddings utilisé à l'indexation y est stocké et comparé à la
configuration au chargement : un écart imposerait une réindexation complète,
les vecteurs n'étant alors plus comparables.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Passage:
    id: str
    title: str
    text: str


@dataclass(frozen=True)
class ScoredPassage:
    passage: Passage
    score: float


class KnowledgeRepository:
    """Recherche par similarité cosinus sur un petit corpus tenant en mémoire.

    À ce volume (quelques dizaines de passages), la comparaison exhaustive est
    exacte et plus rapide qu'un moteur de recherche approximative — aucune
    base de données vectorielle n'est nécessaire.
    """

    def __init__(self, passages: list[Passage], vectors: np.ndarray) -> None:
        self._passages = passages
        # Normalisés une fois pour toutes : la similarité cosinus devient un
        # simple produit scalaire avec le vecteur (normalisé) de la question.
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self._unit_vectors = vectors / norms

    @property
    def is_empty(self) -> bool:
        return len(self._passages) == 0

    def search(self, query_vector: np.ndarray, k: int) -> list[ScoredPassage]:
        if self.is_empty:
            return []

        query_norm = np.linalg.norm(query_vector)
        if query_norm == 0:
            return []
        unit_query = query_vector / query_norm

        scores = self._unit_vectors @ unit_query
        top_k = min(k, len(self._passages))
        top_indices = np.argsort(-scores)[:top_k]

        return [
            ScoredPassage(passage=self._passages[i], score=float(scores[i])) for i in top_indices
        ]

    @classmethod
    def load(cls, index_path: str | Path, expected_model: str) -> "KnowledgeRepository":
        """Charge l'index depuis le disque.

        Ne lève jamais d'exception : un index absent, corrompu ou construit
        avec un autre modèle d'embeddings produit un dépôt vide plutôt qu'un
        crash au démarrage — le chatbot répond alors systématiquement hors
        périmètre, ce qui reste un comportement utile (cf. règle « aucune
        branche ne renvoie une erreur visible »).
        """
        path = Path(index_path)
        if not path.is_file():
            logger.error(
                "Index de connaissance introuvable (%s) : le chatbot répondra "
                "hors périmètre à toutes les questions tant qu'il n'est pas "
                "généré par scripts/build_index.py.",
                path,
            )
            return cls([], np.empty((0, 0), dtype=np.float32))

        try:
            with np.load(path, allow_pickle=False) as data:
                indexed_model = str(data["model"])
                if indexed_model != expected_model:
                    logger.error(
                        "Index de connaissance construit avec le modèle '%s', "
                        "mais la configuration attend '%s' : réindexation "
                        "nécessaire (scripts/build_index.py). Index ignoré.",
                        indexed_model,
                        expected_model,
                    )
                    return cls([], np.empty((0, 0), dtype=np.float32))

                ids = data["ids"]
                titles = data["titles"]
                texts = data["texts"]
                vectors = data["vectors"].astype(np.float32)
        except Exception:
            logger.exception("Échec de lecture de l'index de connaissance (%s).", path)
            return cls([], np.empty((0, 0), dtype=np.float32))

        passages = [
            Passage(id=str(ids[i]), title=str(titles[i]), text=str(texts[i]))
            for i in range(len(ids))
        ]
        return cls(passages, vectors)
