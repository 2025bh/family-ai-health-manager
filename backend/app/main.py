from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import contacts, documents, feishu, health_guard, health_logs, measurements, medication_courses, members, notifications, tasks, visits, voice
from app.core.config import settings
from app.db.seed import seed_demo
from app.db.session import Base, SessionLocal, engine
from app.services.scheduler import CheckInScheduler

checkin_scheduler = CheckInScheduler()


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.ensure_directories()
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_demo(db)
    if settings.scheduler_enabled:
        checkin_scheduler.start()
    yield
    checkin_scheduler.stop()


app = FastAPI(
    title="家医 · 家庭健康管家 API",
    version="0.2.0",
    description="聊天产生数据，而不是为了数据聊天。AI 负责整理，不替代医生诊断。",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://127.0.0.1:5173", "http://localhost:5173"],
    allow_origin_regex=r"https?://192\.168\.\d+\.\d+(?::\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (members.router, health_logs.router, health_guard.router, medication_courses.router, measurements.router, visits.router, documents.router, tasks.router, contacts.router, notifications.router, voice.router, feishu.router):
    app.include_router(router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name, "version": "0.2.0", "llm_provider": settings.llm_provider, "feishu_provider": settings.feishu_provider, "phone_provider": settings.phone_provider}
