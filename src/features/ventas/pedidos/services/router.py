from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.shared.services.database import get_db
from src.features.auth.services.dependencies import solo_empleados
from .schemas import PedidoResponse, PedidoListResponse
from .service import obtener_pedidos, obtener_pedido, confirmar_pedido, cancelar_pedido

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


@router.get("/", response_model=PedidoListResponse)
def listar_pedidos(
    pagina:     int           = Query(1, ge=1),
    por_pagina: int           = Query(10, ge=1, le=100),
    busqueda:   Optional[str] = Query(None),
    db:         Session       = Depends(get_db),
    _:          dict          = Depends(solo_empleados)
):
    """
    Lista todos los pedidos pendientes de confirmar.
    Busca por nombre del cliente.
    """
    return obtener_pedidos(db, pagina, por_pagina, busqueda)


@router.get("/{id_venta}", response_model=PedidoResponse)
def ver_pedido(
    id_venta: int,
    db:       Session = Depends(get_db),
    _:        dict    = Depends(solo_empleados)
):
    """Retorna el detalle de un pedido pendiente."""
    return obtener_pedido(db, id_venta)


@router.patch("/{id_venta}/confirmar", response_model=PedidoResponse)
def confirmar(
    id_venta: int,
    db:       Session = Depends(get_db),
    _:        dict    = Depends(solo_empleados)
):
    """
    Confirma el pedido → se convierte en venta pagada.
    Estado cambia a Confirmado.
    """
    return confirmar_pedido(db, id_venta)


@router.patch("/{id_venta}/cancelar", response_model=PedidoResponse)
def cancelar(
    id_venta: int,
    db:       Session = Depends(get_db),
    _:        dict    = Depends(solo_empleados)
):
    """
    Cancela el pedido.
    - Devuelve el stock de productos al inventario.
    - Si se usó crédito, lo devuelve al cliente.
    - Estado cambia a Cancelado.
    """
    return cancelar_pedido(db, id_venta)