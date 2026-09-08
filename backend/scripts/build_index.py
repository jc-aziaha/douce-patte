"""Construit l'index de connaissance du chatbot à partir de data/corpus.json.

À exécuter en local, jamais sur le serveur (cf. 12-specifications-techniques-
chatbot-ia.md §5) : `python -m scripts.build_index`, depuis le dossier
`backend/`, avec GEMINI_API_KEY configurée dans l'environnement ou le `.env`.

À relancer à chaque modification du corpus. Le fichier produit
(`data/knowledge_index.npz` par défaut) est versionné dans le dépôt : il
survit ainsi au système de fichiers éphémère du serveur en production.
"""

import asyncio
import json
import logging
from pathlib import Path

import numpy as np

from app.config import get_settings
from app.services.embeddings import GeminiEmbeddingClient

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent.parent
CORPUS_PATH = BACKEND_DIR / "data" / "corpus.json"


async def main() -> None:
    settings = get_settings()

    if not settings.gemini_api_key:
        raise SystemExit(
            "GEMINI_API_KEY non configurée : impossible de calculer les embeddings."
        )

    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))["passages"]
    if not corpus:
        raise SystemExit(f"Corpus vide ({CORPUS_PATH}) : rien à indexer.")

    ids = [p["id"] for p in corpus]
    titles = [p["title"] for p in corpus]
    texts = [p["text"] for p in corpus]
    # Le titre est inclus dans le texte encodé, cf. spécifications techniques
    # §5 : « titre conservé, un passage doit se suffire à lui-même ».
    inputs = [f"{title}\n{text}" for title, text in zip(titles, texts, strict=True)]

    logger.info(
        "Calcul des embeddings pour %d passages (modèle %s)...",
        len(inputs),
        settings.gemini_embedding_model,
    )
    client = GeminiEmbeddingClient(settings)
    vectors = await client.embed_batch(inputs)

    output_path = BACKEND_DIR / settings.knowledge_index_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        output_path,
        ids=np.array(ids),
        titles=np.array(titles),
        texts=np.array(texts),
        vectors=vectors.astype(np.float32),
        model=np.array(settings.gemini_embedding_model),
    )
    logger.info(
        "Index écrit dans %s (%d passages, %d dimensions).",
        output_path,
        len(ids),
        vectors.shape[1],
    )


if __name__ == "__main__":
    asyncio.run(main())
