from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
from decimal import Decimal

from src.shared.services.models import (
    Devolucion, DevolucionDetalle, Venta, Usuario,
    Producto, Estado, CreditoCliente, MovimientoCredito
)
from .schemas import DevolucionCreate, DevolucionResolucion, DevolucionReembolso


def _label_estado(db: Session, id_estado: int) -> str:
    estado = db.query(Estado).filter(Estado.ID_Estados == id_estado).first()
    return estado.Estado if estado else None


def _formato_devolucion(dev: Devolucion, db: Session) -> dict:
    usuario = db.query(Usuario).filter(Usuario.ID_Usuario == dev.ID_Usuario).first()

    detalles  = db.query(DevolucionDetalle).filter(
        DevolucionDetalle.ID_Devolucion == dev.ID_Devolucion
    ).all()

    productos = []
    for d in detalles:
        producto = db.query(Producto).filter(Producto.ID_Producto == d.ID_Producto).first()
        productos.append({
            "ID_Devolucion_Detalle": d.ID_Devolucion_Detalle,
            "ID_Producto":           d.ID_Producto,
            "nombre_producto":       producto.nombre if producto else None,
            "Cantidad":              d.Cantidad,
            "PrecioUnitario":        d.PrecioUnitario,
            "Subtotal":              d.Subtotal,
        })

    return {
        "ID_Devolucion":   dev.ID_Devolucion,
        "ID_Venta":        dev.ID_Venta,
        "ID_Usuario":      dev.ID_Usuario,
        "nombre_cliente":  f"{usuario.Nombre} {usuario.Apellidos}" if usuario else None,
        "ID_DetalleVenta": dev.ID_DetalleVenta,
        "FechaDevolucion": dev.FechaDevolucion,
        "Motivo":          dev.Motivo,
        "Estado":          dev.Estado,
        "estado_label":    _label_estado(db, dev.Estado) if dev.Estado else None,
        "TotalDevuelto":   dev.TotalDevuelto,
        "FechaAprobacion": dev.FechaAprobacion,
        "FechaReembolso":  dev.FechaReembolso,
        "UsuarioAprueba":  dev.UsuarioAprueba,
        "Comentario":      dev.Comentario,
        "productos":       productos,
    }


def _recargar_credito(db: Session, id_usuario: int, monto: Decimal, id_devolucion: int):
    """
    Cuando se aprueba una devolución, recarga el crédito del cliente.
    Si no tiene cuenta de crédito, la crea automáticamente.
    """
    credito = db.query(CreditoCliente).filter(
        CreditoCliente.ID_Usuario == id_usuario
    ).first()

    if not credito:
        # Primera devolución del cliente, se crea su cuenta de crédito
        credito = CreditoCliente(
            ID_Usuario   = id_usuario,
            Saldo        = Decimal("0"),
            Fecha_Update = datetime.now(),
        )
        db.add(credito)
        db.flush()

    # Suma el monto al saldo
    credito.Saldo        += monto
    credito.Fecha_Update  = datetime.now()

    # Registra el movimiento en el historial
    db.add(MovimientoCredito(
        ID_Credito    = credito.ID_Credito,
        ID_Devolucion = id_devolucion,
        ID_Venta      = None,
        Tipo          = "recarga",
        Monto         = monto,
        Fecha         = datetime.now(),
    ))


def obtener_mis_devoluciones(
    db: Session,
    id_usuario: int,
    pagina: int = 1,
    por_pagina: int = 10,
) -> dict:
    """Retorna solo las devoluciones del cliente autenticado."""
    query        = db.query(Devolucion).filter(Devolucion.ID_Usuario == id_usuario)
    total        = query.count()
    offset       = (pagina - 1) * por_pagina
    devoluciones = query.order_by(Devolucion.FechaDevolucion.desc()).offset(offset).limit(por_pagina).all()
    return {
        "total":        total,
        "pagina":       pagina,
        "por_pagina":   por_pagina,
        "devoluciones": [_formato_devolucion(d, db) for d in devoluciones],
    }


def obtener_devoluciones(
    db: Session,
    pagina: int = 1,
    por_pagina: int = 10,
    busqueda: str = None
) -> dict:
    query = db.query(Devolucion)

    if busqueda:
        termino      = f"%{busqueda}%"
        usuarios_ids = (
            db.query(Usuario.ID_Usuario)
            .filter(
                Usuario.Nombre.ilike(termino) |
                Usuario.Apellidos.ilike(termino)
            )
            .subquery()
        )
        query = query.filter(Devolucion.ID_Usuario.in_(usuarios_ids))

    total        = query.count()
    offset       = (pagina - 1) * por_pagina
    devoluciones = query.offset(offset).limit(por_pagina).all()

    return {
        "total":        total,
        "pagina":       pagina,
        "por_pagina":   por_pagina,
        "devoluciones": [_formato_devolucion(d, db) for d in devoluciones],
    }


def obtener_devolucion(db: Session, id_devolucion: int) -> dict:
    dev = db.query(Devolucion).filter(
        Devolucion.ID_Devolucion == id_devolucion
    ).first()
    if not dev:
        raise HTTPException(status_code=404, detail="Devolución no encontrada")
    return _formato_devolucion(dev, db)


def crear_devolucion(db: Session, datos: DevolucionCreate) -> dict:
    if not db.query(Venta).filter(Venta.ID_Venta == datos.ID_Venta).first():
        raise HTTPException(status_code=404, detail="Venta no encontrada")

    if not db.query(Usuario).filter(Usuario.ID_Usuario == datos.ID_Usuario).first():
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    total = sum(
        Decimal(str(p.PrecioUnitario)) * Decimal(str(p.Cantidad))
        for p in datos.productos
    )

    ESTADO_PENDIENTE = 1

    nueva = Devolucion(
        ID_Venta        = datos.ID_Venta,
        ID_Usuario      = datos.ID_Usuario,
        ID_DetalleVenta = datos.ID_DetalleVenta,
        Motivo          = datos.Motivo,
        Estado          = ESTADO_PENDIENTE,
        TotalDevuelto   = total,
        FechaDevolucion = datetime.now(),
    )
    db.add(nueva)
    db.flush()

    for p in datos.productos:
        subtotal = Decimal(str(p.PrecioUnitario)) * Decimal(str(p.Cantidad))
        db.add(DevolucionDetalle(
            ID_Devolucion  = nueva.ID_Devolucion,
            ID_Producto    = p.ID_Producto,
            Cantidad       = p.Cantidad,
            PrecioUnitario = p.PrecioUnitario,
            Subtotal       = subtotal,
        ))

    db.commit()
    db.refresh(nueva)
    return _formato_devolucion(nueva, db)


def resolver_devolucion(db: Session, id_devolucion: int, datos: DevolucionResolucion) -> dict:
    """
    Aprueba o rechaza la devolución.
    Si se aprueba (Estado=2), recarga automáticamente el crédito del cliente.
    """
    ESTADO_APROBADA  = 2
    ESTADO_RECHAZADA = 3

    dev = db.query(Devolucion).filter(
        Devolucion.ID_Devolucion == id_devolucion
    ).first()
    if not dev:
        raise HTTPException(status_code=404, detail="Devolución no encontrada")

    # Evita resolver una devolución ya resuelta
    if dev.Estado in {ESTADO_APROBADA, ESTADO_RECHAZADA}:
        raise HTTPException(
            status_code=400,
            detail="Esta devolución ya fue resuelta"
        )

    dev.Estado          = datos.Estado
    dev.Comentario      = datos.Comentario
    dev.UsuarioAprueba  = datos.UsuarioAprueba
    dev.FechaAprobacion = datetime.now()

    # Si se aprueba, recarga el crédito del cliente automáticamente
    if datos.Estado == ESTADO_APROBADA:
        _recargar_credito(
            db            = db,
            id_usuario    = dev.ID_Usuario,
            monto         = Decimal(str(dev.TotalDevuelto)),
            id_devolucion = dev.ID_Devolucion,
        )

    db.commit()
    db.refresh(dev)
    return _formato_devolucion(dev, db)