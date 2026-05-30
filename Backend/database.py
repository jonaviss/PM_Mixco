import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def verificar_contrasena(contrasena_ingresada: str, contrasena_db: str) -> bool:
    # Comparación directa, sin librerías externas que den error
    return contrasena_ingresada == contrasena_db

print("[INFRAESTRUCTURA] Modo desarrollo activo: Verificación simple.")