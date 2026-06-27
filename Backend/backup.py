"""
Backup automático de todas las tablas a JSON.
Programar en Windows Task Scheduler para ejecución diaria.

Uso manual: cd Backend; python backup.py
Los archivos se guardan en C:\Backups\PM_MIXCO\
"""

import os
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from database import supabase

TABLAS = [
    "usuarios", "accesos_usuarios", "rangos", "modulos",
    "inventario_libreria", "libreria_ventas", "libreria_ventas_detalle", "libreria_pagos",
    "compras", "compras_detalle", "pagos_proveedores", "proveedores", "lotes",
    "gastos", "tipos_producto", "cat_metodos_pago", "categorias_gasto",
    "configuracion_correo", "reset_tokens",
]

OUTPUT_DIR = Path("C:/Backups/PM_MIXCO")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
carpeta_backup = OUTPUT_DIR / timestamp
carpeta_backup.mkdir(exist_ok=True)

resumen = {}

for tabla in TABLAS:
    try:
        res = supabase.table(tabla).select("*").execute()
        data = res.data or []
        archivo = carpeta_backup / f"{tabla}.json"
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        resumen[tabla] = f"{len(data)} registros"
    except Exception as e:
        resumen[tabla] = f"ERROR: {e}"

with open(carpeta_backup / "resumen.json", "w", encoding="utf-8") as f:
    json.dump(resumen, f, indent=2, ensure_ascii=False)

# Limpiar backups más viejos de 7 días
limite = datetime.now() - timedelta(days=7)
for d in OUTPUT_DIR.iterdir():
    if d.is_dir():
        try:
            fecha = datetime.strptime(d.name[:8], "%Y%m%d")
            if fecha < limite:
                shutil.rmtree(d)
                print(f"  Backup antiguo eliminado: {d.name}")
        except:
            pass

print(f"Backup completado: {carpeta_backup}")
for k, v in resumen.items():
    print(f"  {k}: {v}")
