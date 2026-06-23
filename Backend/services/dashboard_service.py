from typing import Dict, Any, Optional, List
from datetime import datetime, date
import pytz
from repositories.dashboard_repository import (
    find_creditos_pendientes, count_actividad_total, find_actividad_paginada,
    find_ventas_pagadas_periodo, find_detalle_por_venta_ids, find_all_creditos_pendientes,
    find_all_pagados
)
from repositories.gasto_repository import sum_gastos_periodo
from repositories.common_repository import find_usuarios_by_cuis

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
    nombres = find_usuarios_by_cuis(list(cuis))
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


def _calcular_ganancia_bruta(ventas: List[Dict[str, Any]], detalle: List[Dict[str, Any]]) -> float:
    """Suma (precio_unitario - costo_unitario) * cantidad para cada item en ventas pagadas."""
    detalle_por_venta: dict[str, list] = {}
    for d in detalle:
        detalle_por_venta.setdefault(d["venta_id"], []).append(d)

    ganancia = 0.0
    for v in ventas:
        for d in detalle_por_venta.get(v["id"], []):
            precio = float(d["precio_unitario"] or 0)
            costo = float(d["costo_unitario"] or 0)
            ganancia += (precio - costo) * int(d["cantidad"] or 0)
    return ganancia


def obtener_creditos_detallados(cui_filtro: Optional[str],
                                 pagina: int = 1, por_pagina: int = 10) -> dict:
    result = find_all_creditos_pendientes(cui_filtro, pagina, por_pagina)
    ventas = result["data"]
    total = result["total"]
    cuis = set()
    for v in ventas:
        if v.get("comprador_cui"): cuis.add(v["comprador_cui"])
        if v.get("digitado_por"): cuis.add(v["digitado_por"])
    if cuis:
        nombres = find_usuarios_by_cuis(list(cuis))
        for v in ventas:
            v["nombre_cliente"] = nombres.get(v.get("comprador_cui"), v.get("comprador_cui", "—"))
            v["nombre_operador"] = nombres.get(v.get("digitado_por"), v.get("digitado_por", "—"))
    total_paginas = max((total + por_pagina - 1) // por_pagina, 1)
    return {
        "data": ventas,
        "total": total,
        "pagina": pagina,
        "por_pagina": por_pagina,
        "total_paginas": total_paginas,
        "tiene_siguiente": pagina < total_paginas,
        "tiene_anterior": pagina > 1,
    }


def obtener_pagados_detallados(cui_filtro: Optional[str],
                                pagina: int = 1, por_pagina: int = 10) -> dict:
    result = find_all_pagados(cui_filtro, pagina, por_pagina)
    ventas = result["data"]
    total = result["total"]
    cuis = set()
    for v in ventas:
        if v.get("comprador_cui"): cuis.add(v["comprador_cui"])
        if v.get("digitado_por"): cuis.add(v["digitado_por"])
    if cuis:
        nombres = find_usuarios_by_cuis(list(cuis))
        for v in ventas:
            v["nombre_cliente"] = nombres.get(v.get("comprador_cui"), v.get("comprador_cui", "—"))
            v["nombre_operador"] = nombres.get(v.get("digitado_por"), v.get("digitado_por", "—"))
    total_paginas = max((total + por_pagina - 1) // por_pagina, 1)
    return {
        "data": ventas,
        "total": total,
        "pagina": pagina,
        "por_pagina": por_pagina,
        "total_paginas": total_paginas,
        "tiene_siguiente": pagina < total_paginas,
        "tiene_anterior": pagina > 1,
    }


def obtener_kpis(cui_filtro: Optional[str]) -> dict:
    ahora = datetime.now(ZONA_GT)
    fin_dia = ahora.isoformat()
    inicio_dia = ahora.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    inicio_mes = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

    creditos = find_creditos_pendientes(cui_filtro)
    hoy = str(date.today())
    inicio_mes_str = str(date.today().replace(day=1))

    ventas_hoy = find_ventas_pagadas_periodo(inicio_dia, fin_dia, cui_filtro)
    ventas_mes = find_ventas_pagadas_periodo(inicio_mes_str, hoy, cui_filtro)

    cobrado_hoy = sum(v["total_venta"] for v in ventas_hoy)
    cobrado_mes = sum(v["total_venta"] for v in ventas_mes)

    detalle_hoy = find_detalle_por_venta_ids([v["id"] for v in ventas_hoy])
    detalle_mes = find_detalle_por_venta_ids([v["id"] for v in ventas_mes])

    ganancia_hoy = _calcular_ganancia_bruta(ventas_hoy, detalle_hoy)
    ganancia_mes = _calcular_ganancia_bruta(ventas_mes, detalle_mes)

    gastos_hoy = sum_gastos_periodo(hoy, hoy)
    gastos_mes = sum_gastos_periodo(inicio_mes_str, hoy)

    return {
        "cobrado_hoy": cobrado_hoy,
        "cobrado_mes": cobrado_mes,
        "ganancia_hoy": ganancia_hoy,
        "ganancia_mes": ganancia_mes,
        "gastos_hoy": gastos_hoy,
        "gastos_mes": gastos_mes,
        "neta_hoy": ganancia_hoy - gastos_hoy,
        "neta_mes": ganancia_mes - gastos_mes,
        "creditos_pendientes_total": sum(v["total_venta"] - v["total_pagado"] for v in creditos),
        "creditos_pendientes_cantidad": len(creditos),
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
