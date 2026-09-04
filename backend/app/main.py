from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routers.contact import router as contact_router

settings = get_settings()
is_production = settings.environment == "production"

# En production, l'API n'a besoin d'aucune documentation interactive
# publique : un seul endpoint, déjà documenté côté frontend.
app = FastAPI(
    title="Douce Patte — API",
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if is_production:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


app.include_router(contact_router)

# Sert le frontend statique (build esbuild/Lightning CSS) depuis le même
# service Render que l'API, pour rester sur l'environnement unique prévu par
# les spécifications techniques — évite d'avoir à gérer un second service et
# les origines CORS qui vont avec.
frontend_dir = Path(__file__).resolve().parent.parent / settings.frontend_dist_dir
if frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
