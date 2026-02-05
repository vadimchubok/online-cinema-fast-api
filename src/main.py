from fastapi import FastAPI
from src.auth.router import router as auth_router
from src.interactions.router import router as interaction_router

app = FastAPI(title="Online Cinema API")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(interactions_router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"status": "Backend is running"}
