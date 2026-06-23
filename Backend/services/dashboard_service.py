from typing import Dict, Any, Optional, List
from datetime import datetime
import pytz
from database import supabase
from repositories.dashboard_repository import (
    find_ventas_dia, find_creditos_pendientes, find_ventas_mes,
    count_actividad_total, find_actividad_paginada
)

ZONA_GT = pytz.timezone("America/Guatemala")


def _enriquecer_nombres(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cuis = set()
    for v in data:
        if v.get("digitado_por"):
            cuis.add(v["digitado_por"])
        if v.get("comprador_cui"):
            cuis.add(v["comprador_cui"])
    if not cuis:
        return data
    res = supabase.table("usuarios").select("cui, nombre_completo").in_("cui", list(cuis)).execute()
    nombres = {u["cui"]: u["nombre_completo"] for u in (res.data or [])}
    for v in data:
        v["nombre_operador"] = nombres.get(v.get("digitado_por"), v.get("digitado_por", "—"))
        v["nombre_cliente"] = nombres.get(v.get("comprador_cui"), v.get("comprador_cui", "—"))
    return data


def _resolver_cui_filtro(usuario: Dict[str, Any], cui_param: Optional[str]) -> Optional[str]:
    rango = usuario.get("rango", "analista")
    cui_actual = usuario.get("sub")
    if rango == "analista":
        return cui_actual
    if cui_param and rango in ["encargado", "administrador", "super_admin"]:
        return cui_param
    return None


def obtener_kpis(cui_filtro: Optional[str]) -> dict:
    ahora = datetime.now(ZONA_GT)
    inicio_dia = ahora.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

    ventas_dia = find_ventas_dia(inicio_dia, cui_filtro)
    creditos = find_creditos_pendientes(cui_filtro)
    ventas_mes = find_ventas_mes(inicio_mes, cui_filtro)

    return {
        "ventas_dia_total": sum(v["total_venta"] for v in ventas_dia),
        "ventas_dia_cantidad": len(ventas_dia),
        "creditos_pendientes_total": sum(v["total_venta"] - v["total_pagado"] for v in creditos),
        "creditos_pendientes_cantidad": len(creditos),
        "ventas_mes_total": sum(v["total_venta"] for v in ventas_mes),
        "meta_mes": 50000
    }


def obtener_actividad(pagina: int, por_pagina: int, cui_filtro: Optional[str]) -> dict:
    offset = (pagina - 1) * por_pagina
    total = count_actividad_total(cui_filtro)
    total_paginas = max((total + por_pagina - 1) // por_pagina, 1)
    data = _enriquecer_nombres(find_actividad_paginada(offset, por_pagina, cui_filtro))
    return {
        "data": data,
        "paginacion": {
            "pagina_actual": pagina,
            "por_pagina": por_pagina,
            "total_registros": total,
            "total_paginas": total_paginas,
            "tiene_siguiente": pagina < total_paginas,
            "tiene_anterior": pagina > 1
        },
        "ok": True
    }
