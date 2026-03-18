from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.shared.services.database import get_db
from src.features.auth.services.dependencies import solo_empleados
from .schemas import VentaCreate, VentaEstado, VentaResponse, VentaListResponse
from .service import obtener_ventas, obtener_venta, crear_venta, cambiar_estado

router = APIRouter(prefix="/ventas", tags=["Gestión de Ventas"])


@router.get("/", response_model=VentaListResponse)
def listar_ventas(
    pagina:     int           = Query(1, ge=1),
    por_pagina: int           = Query(10, ge=1, le=100),
    busqueda:   Optional[str] = Query(None),
    db:         Session       = Depends(get_db),
    _:          dict          = Depends(solo_empleados)
):
    """Lista paginada de ventas. Busca por nombre del cliente."""
    return obtener_ventas(db, pagina, por_pagina, busqueda)


@router.get("/{id_venta}", response_model=VentaResponse)
def ver_venta(
    id_venta: int,
    db:       Session = Depends(get_db),
    _:        dict    = Depends(solo_empleados)
):
    """Retorna el detalle completo de una venta con productos, crédito y descuento."""
    return obtener_venta(db, id_venta)


@router.post("/", response_model=VentaResponse, status_code=201)
def registrar_venta(
    datos: VentaCreate,
    db:    Session = Depends(get_db),
    _:     dict    = Depends(solo_empleados)
):
    """
    Crea una venta aplicando el flujo completo:
    1. Valida stock de productos
    2. Aplica crédito del cliente si usar_credito=true
    3. Aplica descuento si queda saldo (cupón, emisión o antigüedad)
    4. Descuenta stock automáticamente
    5. Crea domicilio si se incluye en el body
    """
    return crear_venta(db, datos)


@router.patch("/{id_venta}/estado", response_model=VentaResponse)
def actualizar_estado(
    id_venta: int,
    datos:    VentaEstado,
    db:       Session = Depends(get_db),
    _:        dict    = Depends(solo_empleados)
):
    """Cambia el estado de la venta."""
    return cambiar_estado(db, id_venta, datos.Estado)