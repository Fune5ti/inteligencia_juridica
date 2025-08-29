from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
import asyncio
import logging
import subprocess
import pathlib
from .routes.api_router import api_router
from .infrastructure.db import Base, get_engine, ensure_database_exists


@asynccontextmanager
async def lifespan(app: FastAPI):  # pragma: no cover - simple setup
    """Lifespan context to perform startup/shutdown tasks.

    Creates database tables on startup for development convenience. In
    production prefer managed migrations (Alembic) and remove this.
    """
    # Ensure ORM models are imported so metadata is populated
    try:  # noqa: F401
        from .infrastructure import models  # type: ignore
    except Exception:
        logging.exception("Failed to import models module; tables may not be created")

    ensure_database_exists()
    # Run Alembic migrations to ensure schema is up to date
    project_root = pathlib.Path(__file__).resolve().parent.parent
    alembic_ini = project_root.parent / "alembic.ini"
    if alembic_ini.exists():
        try:
            subprocess.run(
                [
                    "python",
                    "-m",
                    "alembic",
                    "-c",
                    str(alembic_ini),
                    "upgrade",
                    "head",
                ],
                check=True,
                cwd=str(project_root.parent),
                capture_output=True,
                text=True,
            )
            logging.info("Alembic migrations applied")
        except subprocess.CalledProcessError as exc:  # pragma: no cover - defensive
            logging.error("Alembic upgrade failed: %s", exc.stderr)
    else:  # fallback (dev only)
        engine = get_engine()
        try:
            Base.metadata.create_all(bind=engine)
        except Exception:
            pass
    yield
    # (No teardown actions needed yet.)


app = FastAPI(
    title="Inteligencia Juridica API",
    version="0.1.0",
    description=(
        "API for legal document (PDF) extraction producing structured timeline and evidence data.\n\n"
        "Features:\n"
        "- Synchronous extraction endpoint (/extract).\n"
        "- Asynchronous job-based extraction with optional webhook (/extract/async).\n"
        "- Job status polling (/extract/jobs/{job_id}).\n"
        "Authentication: supply your API key via 'X-API-Key' header."
    ),
    contact={"name": "Inteligencia Juridica", "email": "support@example.com"},
    license_info={"name": "MIT"},
    lifespan=lifespan,
)


def custom_openapi():  # pragma: no cover - doc generation
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    # Inject API key security scheme
    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})["ApiKeyAuth"] = {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
        "description": "Provide the API key issued for your client",
    }
    # Apply as global requirement
    openapi_schema["security"] = [{"ApiKeyAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi  # type: ignore
app.include_router(api_router)


def lambda_handler(event, context):  
    from mangum import Mangum
    handler = Mangum(app)
    return handler(event, context)
