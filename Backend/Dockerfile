# 1. Usamos una imagen de Python oficial
FROM python:3.11-slim

# 2. Carpeta de trabajo
WORKDIR /app

# 3. Instalamos dependencias (Copiamos primero para usar caché de Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiamos el resto del código
COPY . .

# 5. Exponemos el puerto
EXPOSE 8000

# 6. COMANDO FINAL (Usando 'python -m' para asegurar que encuentre uvicorn)
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]