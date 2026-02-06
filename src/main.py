from fastapi import FastAPI
from src.auth.router import router as auth_router
from src.movies.routers import router as movies_router
from src.movies.routers import genres_router as genres_router
from src.movies.routers import stars_router as stars_router
from src.interactions.router import router as interaction_router


app = FastAPI(title="Online Cinema API")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(movies_router, prefix="/api/v1")
app.include_router(genres_router, prefix="/api/v1")
app.include_router(stars_router, prefix="/api/v1")
app.include_router(interaction_router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"status": "Backend is running"}
