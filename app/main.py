from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, articles, stock, movements, reports

app = FastAPI(
    title="WIM — Warehouse Inventory Management API",
    description="WIM — Warehouse Inventory Management. Система учёта складских остатков и управления производством для малого предприятия.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене заменить на конкретный домен
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(articles.router, prefix="/api")
app.include_router(stock.router, prefix="/api")
app.include_router(movements.router, prefix="/api")
app.include_router(reports.router, prefix="/api")


@app.get("/")
def root():
    return {"status": "ok", "service": "WIM API v0.1"}


@app.get("/health")
def health():
    return {"status": "healthy"}
