"""
Módulo principal de la aplicación.
Inicializa FastAPI, configura CORS y registra los routers de cada módulo.
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
from routers import auth, libreria, dashboard_libreria
from routers import compras

app = FastAPI(title="PM Mixco ERP API", version="2.0.0")

# CORS configurado desde variable de entorno
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5500")

# Orígenes permitidos: el FRONTEND_URL de entorno más localhost
CORS_ORIGINS = [
    FRONTEND_URL,
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de routers por módulo
app.include_router(auth.router, tags=["Autenticación"])
app.include_router(libreria.router, prefix="/libreria", tags=["Librería"])
app.include_router(dashboard_libreria.router, prefix="/libreria/dashboard", tags=["Dashboard Librería"])
app.include_router(compras.router, prefix="/libreria/compras", tags=["Compras"])

@app.get("/health")
def health_check():
    return {"status": "online", "version": "2.0.0"}
