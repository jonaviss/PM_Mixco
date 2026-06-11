"""
Módulo principal de la aplicación.
Inicializa FastAPI, configura CORS y registra los routers de cada módulo.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, libreria, dashboard_libreria
from routers import compras

app = FastAPI(title="PM Mixco ERP API", version="2.0.0")

# CORS configurado desde variable de entorno
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5500")

# Configuración de CORS corregida para producción
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
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
