from fastapi import APIRouter, HTTPException, Depends
from database import supabase
from routers.dependencies import obtener_usuario_actual
from typing import Dict, Any

router = APIRouter(prefix="/cliente", tags=["Cliente"])


@router.get("/compras")
async def mis_compras(usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    cui = usuario_actual["sub"]
    try:
        res = supabase.table("libreria_ventas") \
            .select("id, total_venta, total_pagado, estado_pago, created_at, digitado_por") \
            .eq("comprador_cui", cui) \
            .order("created_at", desc=True) \
            .execute()
        ventas = res.data or []
        cuis_operadores = list(set(v["digitado_por"] for v in ventas if v.get("digitado_por")))
        nombres = {}
        if cuis_operadores:
            res_usuarios = supabase.table("usuarios").select("cui, nombre_completo").in_("cui", cuis_operadores).execute()
            nombres = {u["cui"]: u["nombre_completo"] for u in (res_usuarios.data or [])}
        venta_ids = [v["id"] for v in ventas]
        detalles_por_venta = {}
        if venta_ids:
            res_detalles = supabase.table("libreria_ventas_detalle") \
                .select("venta_id, cantidad, precio_unitario, subtotal, inventario_libreria(nombre, tipo_producto)") \
                .in_("venta_id", venta_ids) \
                .execute()
            for d in (res_detalles.data or []):
                vid = d["venta_id"]
                if vid not in detalles_por_venta:
                    detalles_por_venta[vid] = []
                prod_info = d.get("inventario_libreria") or {}
                detalles_por_venta[vid].append({
                    "nombre": prod_info.get("nombre", "Producto"),
                    "tipo_producto": prod_info.get("tipo_producto", "—"),
                    "cantidad": d["cantidad"],
                    "precio_unitario": float(d["precio_unitario"]),
                    "subtotal": float(d["subtotal"])
                })
        for v in ventas:
            v["nombre_operador"] = nombres.get(v.get("digitado_por"), v.get("digitado_por", "—"))
            v["productos"] = detalles_por_venta.get(v["id"], [])
        return {"ventas": ventas, "ok": True}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.get("/pagos")
async def mis_pagos(usuario_actual: Dict[str, Any] = Depends(obtener_usuario_actual)):
    cui = usuario_actual["sub"]
    try:
        res_ventas = supabase.table("libreria_ventas") \
            .select("id") \
            .eq("comprador_cui", cui) \
            .execute()
        venta_ids = [v["id"] for v in (res_ventas.data or [])]
        if not venta_ids:
            return {"pagos": [], "ok": True}
        res_pagos = supabase.table("libreria_pagos") \
            .select("id, venta_id, monto_abonado, fecha_pago, digitado_por") \
            .in_("venta_id", venta_ids) \
            .order("fecha_pago", desc=True) \
            .execute()
        pagos = res_pagos.data or []
        cuis_operadores = list(set(p["digitado_por"] for p in pagos if p.get("digitado_por")))
        nombres = {}
        if cuis_operadores:
            res_usuarios = supabase.table("usuarios").select("cui, nombre_completo").in_("cui", cuis_operadores).execute()
            nombres = {u["cui"]: u["nombre_completo"] for u in (res_usuarios.data or [])}
        for p in pagos:
            p["operador"] = nombres.get(p.get("digitado_por"), "—")
            p["monto_abonado"] = float(p["monto_abonado"])
        return {"pagos": pagos, "ok": True}
    except Exception as e:
        raise HTTPException(500, detail=str(e))
