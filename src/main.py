from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── Auth ──
from src.features.auth.services.router import router as auth_router

# ── Configuración ──
from src.features.configuracion.usuarios.services.router       import router as usuarios_router
from src.features.configuracion.roles.services.router          import router as roles_router
from src.features.configuracion.notificaciones.services.router import router as notificaciones_router
from src.features.configuracion.descuentos.services.router     import router as descuentos_router

# ── Compras ──
from src.features.compras.insumos.services.router           import router as insumos_router
from src.features.compras.categoria_insumos.services.router import router as cat_insumos_router
from src.features.compras.proveedores.services.router       import router as proveedores_router

# ── Producción ──
from src.features.produccion.productos.services.router           import router as productos_router
from src.features.produccion.categoria_productos.services.router import router as cat_productos_router
from src.features.produccion.ordenes_produccion.services.router  import router as ordenes_router

# ── Ventas ──
from src.features.ventas.clientes.services.router       import router as clientes_router
from src.features.ventas.pedidos.services.router        import router as pedidos_router
from src.features.ventas.gestion_ventas.services.router import router as ventas_router
from src.features.ventas.devoluciones.services.router   import router as devoluciones_router
from src.features.ventas.domicilios.services.router     import router as domicilios_router

# ── Dashboard ──
from src.features.dashboard.services.router import router as dashboard_router


app = FastAPI(
    title="API Proyecto",
    version="1.0.0",
    description="API para gestión de producción y ventas"
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Registro de routers ──
PREFIX = "/api"

app.include_router(auth_router,          prefix=PREFIX)
app.include_router(usuarios_router,      prefix=PREFIX)
app.include_router(roles_router,         prefix=PREFIX)
app.include_router(notificaciones_router, prefix=PREFIX)
app.include_router(descuentos_router,    prefix=PREFIX)
app.include_router(insumos_router,       prefix=PREFIX)
app.include_router(cat_insumos_router,   prefix=PREFIX)
app.include_router(proveedores_router,   prefix=PREFIX)
app.include_router(productos_router,     prefix=PREFIX)
app.include_router(cat_productos_router, prefix=PREFIX)
app.include_router(ordenes_router,       prefix=PREFIX)
app.include_router(clientes_router,      prefix=PREFIX)
app.include_router(pedidos_router,       prefix=PREFIX)
app.include_router(ventas_router,        prefix=PREFIX)
app.include_router(devoluciones_router,  prefix=PREFIX)
app.include_router(domicilios_router,    prefix=PREFIX)
app.include_router(dashboard_router,     prefix=PREFIX)


@app.get("/")
def root():
    return {"mensaje": "API funcionando ✅"}


# ── Endpoint temporal de limpieza (solo Admin) ────────────────────────────────
from fastapi import Depends
from sqlalchemy.orm import Session
from decimal import Decimal
from src.shared.services.database import get_db
from src.features.auth.services.dependencies import obtener_usuario_actual
from src.shared.services.models import (
    DevolucionDetalle, MovimientoCredito, Devolucion,
    DescuentoXVenta, DescuentoXUsuario, Descuento,
    Domicilio, DetalleVenta, VentaXProducto, Venta,
    CreditoCliente, Producto,
)

@app.delete("/api/admin/reset-transaccional")
def reset_transaccional(
    actual: dict    = Depends(obtener_usuario_actual),
    db:     Session = Depends(get_db),
):
    if actual.get("rol") != "Admin":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Solo el Admin puede ejecutar esto")

    ESTADOS_CANCELADOS = {3, 5}
    ventas_activas = db.query(Venta).filter(Venta.Estado.notin_(ESTADOS_CANCELADOS)).all()
    ids_activas    = {v.ID_Venta for v in ventas_activas}
    items = db.query(VentaXProducto).filter(VentaXProducto.ID_Venta.in_(ids_activas)).all() if ids_activas else []

    restaurados = {}
    for item in items:
        restaurados[item.ID_Producto] = restaurados.get(item.ID_Producto, 0) + item.Cantidad
    for id_prod, cant in restaurados.items():
        p = db.query(Producto).filter(Producto.ID_Producto == id_prod).first()
        if p:
            p.Stock += cant

    conteo = {}
    conteo["DevolucionDetalle"] = db.query(DevolucionDetalle).delete()
    conteo["MovimientoCredito"] = db.query(MovimientoCredito).delete()
    conteo["Devoluciones"]      = db.query(Devolucion).delete()
    conteo["DescuentoXVenta"]   = db.query(DescuentoXVenta).delete()
    conteo["Domicilios"]        = db.query(Domicilio).delete()
    conteo["DetalleVenta"]      = db.query(DetalleVenta).delete()
    conteo["VentaXProducto"]    = db.query(VentaXProducto).delete()
    conteo["Ventas"]            = db.query(Venta).delete()

    db.query(CreditoCliente).update({"Saldo": Decimal("0"), "Fecha_Update": None})
    db.query(Descuento).update({"Usos_Actuales": 0})
    db.query(DescuentoXUsuario).update({"Usado": False})

    db.commit()
    return {
        "mensaje":           "Base de datos transaccional limpiada ✅",
        "stock_restaurado":  len(restaurados),
        "filas_eliminadas":  conteo,
    }