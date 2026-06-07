import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routers import auth, libreria, dashboard_libreria

app = FastAPI(title="PM Mixco ERP API", version="2.0.0")

# Permitir todos los orígenes para pruebas en Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/js", StaticFiles(directory="../Frontend/js"), name="js")
app.mount("/css", StaticFiles(directory="../Frontend/css"), name="css")

# Ruta raíz que carga tu archivo principal
@app.get("/")
async def cargar_interfaz():
    return FileResponse("../Frontend/index.html")

# Registro de enrutadores
app.include_router(auth.router, tags=["Autenticación"])
app.include_router(libreria.router, prefix="/libreria", tags=["Librería"])
app.include_router(dashboard_libreria.router, prefix="/libreria/dashboard", tags=["Dashboard Librería"])

@app.get("/health")
def health_check():
    return {"status": "online", "version": "2.0.0"}