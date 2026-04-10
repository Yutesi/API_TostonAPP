from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.shared.services.database import get_db
from src.features.auth.services.dependencies import requiere_permiso
from .schemas import (
    DevolucionCreate, DevolucionResolucion,
    DevolucionResponse, DevolucionListResponse
)
from .service import (
    obtener_devoluciones, obtener_devolucion,
    crear_devolucion, resolver_devolucion
)

router = APIRouter(prefix="/devoluciones", tags=["Devoluciones"])


@router.get("/", response_model=DevolucionListResponse)
def listar_devoluciones(
    pagina:     int           = Query(1, ge=1),
    por_pagina: int           = Query(10, ge=1, le=100),
    busqueda:   Optional[str] = Query(None),
    db:         Session       = Depends(get_db),
    _:          dict          = Depends(requiere_permiso("ver_devoluciones"))
):
    """Lista paginada de devoluciones. Busca por nombre del cliente."""
    return obtener_devoluciones(db, pagina, por_pagina, busqueda)


@router.get("/{id_devolucion}", response_model=DevolucionResponse)
def ver_devolucion(
    id_devolucion: int,
    db:            Session = Depends(get_db),
    _:             dict    = Depends(requiere_permiso("ver_devoluciones"))
):
    """Retorna el detalle de una devolución con sus productos."""
    return obtener_devolucion(db, id_devolucion)


@router.post("/", response_model=DevolucionResponse, status_code=201)
def registrar_devolucion(
    datos: DevolucionCreate,
    db:    Session = Depends(get_db),
    _:     dict    = Depends(requiere_permiso("crear_devoluciones"))
):
    """Registra una devolución. El total se calcula automáticamente. Estado inicial: Pendiente."""
    return crear_devolucion(db, datos)


@router.patch("/{id_devolucion}/resolver", response_model=DevolucionResponse)
def aprobar_rechazar(
    id_devolucion: int,
    datos:         DevolucionResolucion,
    db:            Session = Depends(get_db),
    _:             dict    = Depends(requiere_permiso("editar_devoluciones"))
):
    """Aprueba o rechaza la devolución. Si se aprueba → recarga crédito automáticamente."""
    return resolver_devolucion(db, id_devolucion, datos)