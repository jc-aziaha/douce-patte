from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routers.chat import router as chat_router
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


# Recense tout ce que le site charge réellement en externe (frontend/*.html,
# css/, js/) : polices Google, GSAP via cdnjs, et Google reCAPTCHA (script,
# iframe du widget, appels internes vers gstatic.com). 'unsafe-inline' reste
# nécessaire en script-src/style-src tant que le site est du HTML statique
# sans template serveur pour générer un nonce par requête (le thème clair/
# sombre et le JSON-LD sont des <script> inline) — la politique bloque tout
# de même le chargement de script/frame/objet depuis un domaine non listé,
# ce qui reste une vraie protection contre l'exfiltration de données ou
# l'injection de contenu tiers.
_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com "
    "https://www.google.com https://www.gstatic.com; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data:; "
    "connect-src 'self' https://www.google.com; "
    "frame-src https://www.google.com; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "frame-ancestors 'none'"
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = _CSP
    if is_production:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


app.include_router(contact_router)
app.include_router(chat_router)

# Sert le frontend statique (build esbuild/Lightning CSS) depuis le même
# service Render que l'API, pour rester sur l'environnement unique prévu par
# les spécifications techniques — évite d'avoir à gérer un second service et
# les origines CORS qui vont avec.
frontend_dir = Path(__file__).resolve().parent.parent / settings.frontend_dist_dir
if frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
