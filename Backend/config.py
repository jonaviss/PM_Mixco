import os
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET no configurado en variables de entorno.")

JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 480
DEFAULT_PASSWORD = "PalabraMiel2026"
