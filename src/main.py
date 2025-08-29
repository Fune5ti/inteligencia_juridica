from fastapi import FastAPI
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


app = FastAPI(title="Inteligencia Juridica API", lifespan=lifespan)
app.include_router(api_router)


def lambda_handler(event, context):  
    from mangum import Mangum
    handler = Mangum(app)
    return handler(event, context)
