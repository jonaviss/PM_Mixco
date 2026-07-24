import time
from collections import defaultdict
from fastapi import HTTPException, Request

_attempts = defaultdict(list)
LIMIT = 5
WINDOW = 60

def check_rate_limit(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    key = client_ip
    now = time.time()
    cutoff = now - WINDOW
    _attempts[key] = [t for t in _attempts[key] if t > cutoff]
    if len(_attempts[key]) >= LIMIT:
        raise HTTPException(status_code=429, detail="Demasiados intentos. Esperá un minuto.")
    _attempts[key].append(now)
