from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import generate, stories, upload

app = FastAPI(title="Storyworld API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router)
app.include_router(stories.router)
app.include_router(upload.router)


@app.get("/health")
async def health() -> dict:
    return {"ok": True}
