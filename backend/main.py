from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import generate, stories, upload

app = FastAPI(title="Storyworld API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # open for iPad demo — tighten post-hackathon
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router)
app.include_router(stories.router)
app.include_router(upload.router)


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


@app.get("/debug/groq")
async def debug_groq() -> dict:
    import os
    from groq import AsyncGroq
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        return {"error": "GROQ_API_KEY not set"}
    try:
        client = AsyncGroq(api_key=key)
        resp = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Say hello in JSON: {\"hello\": true}"}],
            max_tokens=50,
        )
        return {"ok": True, "response": resp.choices[0].message.content}
    except Exception as e:
        return {"error": str(e)}
