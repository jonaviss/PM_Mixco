from fastapi import APIRouter, HTTPException, status
from database import supabase, verificar_contrasena
from schemas import LoginRequest, TokenResponse
from datetime import datetime, timedelta
import os
from jose import jwt
from typing import Dict, Any

router = APIRouter()

# Configuración JWT (Importada desde las variables de entorno)
JWT_SECRET = os.getenv("JWT_SECRET", "PALABRA_MIEL_MIXCO_SECRET_KEY_2026")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 480

def generar_token_jwt(data: Dict[str, Any]) -> str:
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(payload: LoginRequest):
    credencial = payload.contrasena or payload.password
    
    response = supabase.table("usuarios") \
        .select("*") \
        .eq("cui", payload.cui) \
        .eq("activo", True) \
        .execute()
        
    if not response.data:
        raise HTTPException(status_code=401, detail="CUI o contraseña incorrectos")
    
    usuario = response.data[0]
    
    if not verificar_contrasena(credencial, usuario["contrasena_hash"]):
        raise HTTPException(status_code=401, detail="CUI o contraseña incorrectos")
    
    token_payload = {
        "sub": usuario["cui"], 
        "rango": "super_admin",
        "modulos": ["auditoria", "cafeteria", "libreria"]
    }
    jwt_token = generar_token_jwt(token_payload)
    
    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "nombre_completo": usuario["nombre_completo"],
        "rango": "super_admin",
        "modulos": ["auditoria", "cafeteria", "libreria"]
    }