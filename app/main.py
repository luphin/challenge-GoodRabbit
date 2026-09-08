from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    description="API Challenge - Manejo de turnos",
    version=settings.app_version,
    docs_url="/docs"
)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Challenge - API manejo de turnos."
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "environment": settings.environment,
        "version": settings.app_version,
    }
