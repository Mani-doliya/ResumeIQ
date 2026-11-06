import logging
import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import APP_NAME, APP_VERSION, STATIC_DIR, TEMPLATES_DIR, BASE_DIR
from app.api.routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Production-ready AI/ML Resume Intelligence System with NLP, TF-IDF matching, ATS scoring and skill gap analysis."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

app.include_router(router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.on_event("startup")
async def startup_event():
    logger.info(f"{APP_NAME} v{APP_VERSION} starting")
    logger.info(f"Python {sys.version}")
    from app.services.skill_extractor import skill_extractor
    logger.info(f"Skills taxonomy loaded: {len(skill_extractor.all_skills)} skills")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down")