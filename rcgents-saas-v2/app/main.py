"""RC Agents v2 — FastAPI application entry point (Multi-Tenant SaaS)."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.database.models import init_db

# ── Routers ────────────────────────────────────────────
from app.routers import meta_webhook, whatsapp_webhook, shopify_webhook, dashboard_api

# ── Logging ──────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s")
logger = logging.getLogger("rcagents")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info(f"🚀 {settings.APP_NAME} starting — env={settings.APP_ENV}")
    init_db()
    logger.info("✅ Database initialized")
    yield
    logger.info("👋 Shutting down")


app = FastAPI(title=settings.APP_NAME, version="2.0.0", lifespan=lifespan)

# ── Static files & templates ────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ── Register routers ────────────────────────────────────
app.include_router(meta_webhook.router)
app.include_router(whatsapp_webhook.router)
app.include_router(shopify_webhook.router)
app.include_router(dashboard_api.router)


# ── Public pages ────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/privacy", response_class=HTMLResponse)
async def privacy_policy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})


@app.get("/terms", response_class=HTMLResponse)
async def terms_of_service(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})


# ── Health check ────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": "2.0.0"}
