"""
Módulo de infraestructura de base de datos.
Inicializa el cliente de Supabase y provee la función de verificación de contraseñas.
"""

import os
import bcrypt
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


def verificar_contrasena(contrasena_ingresada: str, contrasena_hash: str) -> bool:
    """
    Verifica una contraseña en texto plano contra su hash bcrypt almacenado.

    Args:
        contrasena_ingresada: Contraseña en texto plano ingresada por el usuario
        contrasena_hash: Hash bcrypt almacenado en la base de datos

    Returns:
        bool: True si la contraseña es correcta, False en caso contrario
    """
    try:
        return bcrypt.checkpw(
            contrasena_ingresada.encode("utf-8"),
            contrasena_hash.encode("utf-8")
        )
    except Exception:
        return False