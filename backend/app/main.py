from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import CORS_ALLOWED_ORIGINS

app = FastAPI(title="MP Job Saathi", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(CORS_ALLOWED_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
