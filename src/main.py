from fastapi import FastAPI
from src.auth.router import router as auth_router
from src.movies.routers.movies_router import router as movies_router
from src.movies.routers.genres_router import router as genres_router
from src.movies.routers.stars_router import router as stars_router
from src.interactions.router import router as interaction_router
from src.orders.routers import router as order_router
from src.payments.routers import router as payment_router
from src.cart.routers import router as cart_router

app = FastAPI(title="Online Cinema API", debug=True)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(movies_router, prefix="/api/v1")
app.include_router(genres_router, prefix="/api/v1")
app.include_router(stars_router, prefix="/api/v1")
app.include_router(interaction_router, prefix="/api/v1")

app.include_router(cart_router, prefix="/api/v1")
app.include_router(order_router, prefix="/api/v1")

app.include_router(payment_router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"status": "Backend is running"}
