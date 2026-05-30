from fastapi import APIRouter, HTTPException, status
from database import supabase
from schemas import ProductoLibreriaCreate, VentaLibreriaCreate

router = APIRouter()

# La ruta final será /libreria/productos gracias al prefijo en main.py
@router.get("/productos")
async def listar_productos():
    try:
        response = supabase.table("inventario_libreria").select("*").execute()
        return response.data
    except Exception as e:
        return {"error": str(e)}

@router.post("/productos", status_code=status.HTTP_201_CREATED)
def registrar_producto_hibrido(payload: ProductoLibreriaCreate):
    data_insercion = payload.model_dump()
    try:
        response = supabase.table("inventario_libreria").insert(data_insercion).execute()
        return {"mensaje": "Producto registrado", "data": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ventas", status_code=status.HTTP_201_CREATED)
def registrar_venta_libreria(payload: VentaLibreriaCreate):
    # Lógica de venta...
    return {"mensaje": "Venta procesada"}