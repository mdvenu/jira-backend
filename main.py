import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.database import init_db
from routes.meeting_routes import router as meeting_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

app = FastAPI(title="AI Meeting Intelligence Dashboard", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://jira-task-frontend.vercel.app",
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(meeting_router)


@app.on_event("startup")
def startup() -> None:
    try:
        init_db()
    except Exception as e:
        logging.error(f"Failed to initialize database: {e}")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
