"""
Módulo principal de la aplicación.
Inicializa FastAPI, configura CORS y registra los routers de cada módulo.
"""

import os
import asyncio
import logging
import threading
from datetime import datetime, time, timedelta
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
from routers import auth, libreria, dashboard_libreria
from routers import compras, cliente, admin, usuario, configuracion, gastos, telegram

logger = logging.getLogger(__name__)

HORA_BACKUP = 5  # 5 AM


def _ejecutar_backup_diario():
    import time as t
    while True:
        ahora = datetime.now()
        objetivo = datetime(ahora.year, ahora.month, ahora.day, HORA_BACKUP, 0, 0)
        if ahora > objetivo:
            objetivo += timedelta(days=1)
        espera = (objetivo - ahora).total_seconds()
        t.sleep(espera)
        try:
            from services.backup_service import enviar_backup_correo
            enviar_backup_correo()
            logger.info("Backup diario completado")
        except Exception as e:
            logger.error(f"Backup diario falló: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(telegram.polling_loop())
    hilo = threading.Thread(target=_ejecutar_backup_diario, daemon=True)
    hilo.start()
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="PM Mixco ERP API", version="2.0.0", lifespan=lifespan)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    logger.exception("Error no manejado: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Error interno del servidor"})

# CORS configurado desde variable de entorno
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5500")

# Orígenes permitidos: frontend en Render + localhost para desarrollo
CORS_ORIGINS = [
    FRONTEND_URL,
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "https://pm-mixco-frontend.onrender.com",
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
app.include_router(cliente.router)
app.include_router(admin.router)
app.include_router(usuario.router)
app.include_router(configuracion.router)
app.include_router(gastos.router)
app.include_router(telegram.router)

@app.get("/health")
def health_check():
    return {"status": "online", "version": "2.0.0"}
