from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    environment: str = "development"

    smtp_host: str = "sandbox.smtp.mailtrap.io"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True

    from_email: str = "Douce Patte <contact@douce-patte.fr>"
    notify_email: str = "contact@douce-patte.fr"

    recaptcha_secret_key: str = ""
    recaptcha_min_score: float = 0.5

    cors_allow_origins: list[str] = ["http://localhost:8123", "https://douce-patte.fr"]

    # Dossier des fichiers statiques du frontend (build esbuild/Lightning CSS ou
    # sources brutes). Si absent, l'API tourne seule sans servir de pages.
    frontend_dist_dir: str = "../frontend/dist"

    # ----- Chatbot IA (RAG) -----
    # Fournisseur : Google Gemini (API AI Studio). Choisi pour son palier
    # gratuit sans carte bancaire — Mistral, retenu initialement, impose
    # l'activation d'un "Pay-As-You-Go" qui en demande une. Écart assumé par
    # rapport à 12-specifications-techniques-chatbot-ia.md §2 (préférence UE) :
    # à documenter côté cadrage si ce choix est confirmé.
    gemini_api_key: str = ""
    gemini_embedding_model: str = "gemini-embedding-001"
    gemini_llm_model: str = "gemini-3.5-flash-lite"
    gemini_api_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_timeout_seconds: float = 8.0

    # Chemin de l'index versionné (relatif au dossier backend/), construit par
    # scripts/build_index.py. Voir app/repositories/knowledge.py.
    knowledge_index_path: str = "data/knowledge_index.npz"

    # Sous le seuil, la réponse hors périmètre part directement, sans appel au
    # modèle de génération (cf. 12-specifications-techniques-chatbot-ia.md §6).
    chat_relevance_threshold: float = 0.55
    chat_top_k: int = 4

    chat_max_message_length: int = 500
    chat_rate_limit_window_seconds: int = 300
    chat_rate_limit_max_requests: int = 10
    chat_daily_request_cap: int = 200


@lru_cache
def get_settings() -> Settings:
    return Settings()
