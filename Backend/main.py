from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, libreria

app = FastAPI(title="PM Mixco ERP API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inyección de módulos (Routers)
app.include_router(auth.router, tags=["Autenticación"])
app.include_router(libreria.router, prefix="/libreria", tags=["Librería"])

@app.get("/health")
def health_check():
    return {"status": "online", "architecture": "professional_modular"}