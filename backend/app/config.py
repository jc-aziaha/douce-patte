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


@lru_cache
def get_settings() -> Settings:
    return Settings()
