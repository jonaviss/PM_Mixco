"""
Backup de todas las tablas a archivos JSON.
Uso: cd Backend; python backup.py
Los archivos se guardan en ./backups/
"""

import os
import json
from datetime import datetime
from pathlib import Path
from database import supabase

TABLAS = [
    "usuarios", "accesos_usuarios", "rangos", "modulos",
    "inventario_libreria", "libreria_ventas", "libreria_ventas_detalle", "libreria_pagos",
    "compras", "compras_detalle", "pagos_proveedores", "proveedores", "lotes",
    "gastos", "tipos_producto", "cat_metodos_pago", "categorias_gasto",
    "configuracion_correo", "reset_tokens",
]

OUTPUT_DIR = Path(__file__).parent / "backups"
OUTPUT_DIR.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
resumen = {}

for tabla in TABLAS:
    try:
        res = supabase.table(tabla).select("*").execute()
        data = res.data or []
        archivo = OUTPUT_DIR / f"{timestamp}_{tabla}.json"
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        resumen[tabla] = f"{len(data)} registros -> {archivo.name}"
    except Exception as e:
        resumen[tabla] = f"ERROR: {e}"

# Resumen general
resumen_path = OUTPUT_DIR / f"{timestamp}_resumen.json"
with open(resumen_path, "w", encoding="utf-8") as f:
    json.dump(resumen, f, indent=2, ensure_ascii=False)

print(f"Backup completado: {OUTPUT_DIR / timestamp}")
for k, v in resumen.items():
    print(f"  {k}: {v}")
print(f"\nResumen: {resumen_path.name}")
