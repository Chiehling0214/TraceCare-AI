from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import get_settings
from app.core.database import SessionLocal, create_all
from app.seed.synthetic import seed_synthetic_data

settings = get_settings()

app = FastAPI(title="TraceCare AI Backend", version=settings.version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_, exc: Exception) -> JSONResponse:
    if hasattr(exc, "status_code") and hasattr(exc, "detail"):
        raise exc
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": "Unexpected backend error."}},
    )


@app.on_event("startup")
def on_startup() -> None:
    create_all()
    if settings.seed_on_startup:
        db = SessionLocal()
        try:
            seed_synthetic_data(db)
        finally:
            db.close()


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "version": settings.version}


app.include_router(router)
