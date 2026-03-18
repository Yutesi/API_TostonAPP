from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.shared.services.database import get_db
from src.features.auth.services.dependencies import solo_empleados
from .schemas import (
    DomicilioCreate, DomicilioUpdate, DomicilioEstado,
    AsignarRepartidor, DomicilioResponse, DomicilioListResponse
)
from .service import (
    obtener_domicilios, obtener_domicilio, crear_domicilio,
    editar_domicilio, asignar_repartidor, cambiar_estado
)

router = APIRouter(prefix="/domicilios", tags=["Domicilios"])


@router.get("/", response_model=DomicilioListResponse)
def listar_domicilios(
    pagina:     int            = Query(1, ge=1),
    por_pagina: int            = Query(10, ge=1, le=100),
    busqueda:   Optional[str]  = Query(None),
    estado:     Optional[int]  = Query(None),   # filtra por estado
    db:         Session        = Depends(get_db),
    _:          dict           = Depends(solo_empleados)
):
    """
    Lista paginada de domicilios.
    Busca por nombre de cliente, repartidor o dirección.
    Filtra por estado con el query param ?estado=1
    """
    return obtener_domicilios(db, pagina, por_pagina, busqueda, estado)


@router.get("/{id_domicilio}", response_model=DomicilioResponse)
def ver_domicilio(
    id_domicilio: int,
    db:           Session = Depends(get_db),
    _:            dict    = Depends(solo_empleados)
):
    """Retorna el detalle de un domicilio."""
    return obtener_domicilio(db, id_domicilio)


@router.post("/", response_model=DomicilioResponse, status_code=201)
def agregar_domicilio(
    datos: DomicilioCreate,
    db:    Session = Depends(get_db),
    _:     dict    = Depends(solo_empleados)
):
    """
    Crea un domicilio manualmente o desde una venta.
    Si viene ID_Empleado → estado Asignado.
    Si no viene → estado Pendiente.
    """
    return crear_domicilio(db, datos)


@router.put("/{id_domicilio}", response_model=DomicilioResponse)
def actualizar_domicilio(
    id_domicilio: int,
    datos:        DomicilioUpdate,
    db:           Session = Depends(get_db),
    _:            dict    = Depends(solo_empleados)
):
    """Edita dirección, observaciones o fecha de entrega."""
    return editar_domicilio(db, id_domicilio, datos)


@router.patch("/{id_domicilio}/repartidor", response_model=DomicilioResponse)
def asignar_empleado(
    id_domicilio: int,
    datos:        AsignarRepartidor,
    db:           Session = Depends(get_db),
    _:            dict    = Depends(solo_empleados)
):
    """
    Asigna un repartidor al domicilio.
    Si estaba Pendiente cambia automáticamente a Asignado.
    """
    return asignar_repartidor(db, id_domicilio, datos.ID_Empleado)


@router.patch("/{id_domicilio}/estado", response_model=DomicilioResponse)
def actualizar_estado(
    id_domicilio: int,
    datos:        DomicilioEstado,
    db:           Session = Depends(get_db),
    _:            dict    = Depends(solo_empleados)
):
    """
    Cambia el estado del domicilio.
    Si el estado es Entregado → registra Fecha_entrega automáticamente.
    """
    return cambiar_estado(db, id_domicilio, datos.Estado)