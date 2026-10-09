from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.admin_cidades import router as admin_cidades_router
from app.api.v1.admin_comodidades import router as admin_comodidades_router
from app.api.v1.admin_hoteis import router as admin_hoteis_router
from app.api.v1.admin_quartos import router as admin_quartos_router
from app.api.v1.auth import router as auth_router
from app.api.v1.busca import router as busca_router
from app.api.v1.cidades import router as cidades_router
from app.api.v1.health import router as health_router
from app.api.v1.hoteis import router as hoteis_router
from app.api.v1.sobre import router as sobre_router
from app.core.config import settings
from app.core.database import SessionLocal, get_mongo_db
from app.core.seed_mongo import seed_mongo_users
from app.services.catalogo_mongo_service import CatalogoMongoService


@asynccontextmanager
async def lifespan(app: FastAPI):
    mongo_db = get_mongo_db()
    await seed_mongo_users(mongo_db)

    db_session = SessionLocal()
    try:
        mongo_service = CatalogoMongoService(mongo_db, db_session)
        await mongo_service.inicializar_indices()
    finally:
        db_session.close()

    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(sobre_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(cidades_router, prefix=settings.API_V1_STR)
app.include_router(hoteis_router, prefix=settings.API_V1_STR)
app.include_router(busca_router, prefix=settings.API_V1_STR)
app.include_router(admin_cidades_router, prefix=settings.API_V1_STR)
app.include_router(admin_hoteis_router, prefix=settings.API_V1_STR)
app.include_router(admin_comodidades_router, prefix=settings.API_V1_STR)
app.include_router(admin_quartos_router, prefix=settings.API_V1_STR)


@app.get("/")
def read_root():
    return {"message": "Bem-vindo ao Core Service do Sistema de Reservas!"}