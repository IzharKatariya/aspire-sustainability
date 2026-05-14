"""
app/main.py
────────────
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings

app = FastAPI(
    title="Sustainability Report Generator",
    description=(
        "Upload a company ESG CSV and receive a GRI/TCFD-aligned "
        "sustainability report draft as a Word document."
    ),
    version="1.0.0",
)

# ── CORS ───────────────────────────────────────────────────────────────────────
# Allows Streamlit Cloud frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten this to your Streamlit URL after deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ─────────────────────────────────────────────────────────────────────
app.include_router(router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "service": "Sustainability Report Generator API",
        "version": "1.0.0",
        "docs": "/docs",
    }