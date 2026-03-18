from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.shared.services.database import get_db
from src.features.auth.services.dependencies import solo_empleados
from .schemas import RolCreate, RolUpdate, RolEstado, AsignarPermisos, RolResponse, RolListResponse
from .service import (
    obtener_roles,
    obtener_rol,
    crear_rol,
    editar_rol,
    cambiar_estado,
    eliminar_rol,
    asignar_permisos
)

router = APIRouter(prefix="/roles", tags=["Roles y Permisos"])


@router.get("/", response_model=RolListResponse)
def listar_roles(
    busqueda: Optional[str] = Query(None),
    db:       Session       = Depends(get_db),
    _:        dict          = Depends(solo_empleados)
):
    """Lista todos los roles. Soporta búsqueda por nombre."""
    return obtener_roles(db, busqueda)


@router.get("/{id_rol}", response_model=RolResponse)
def ver_rol(
    id_rol: int,
    db:     Session = Depends(get_db),
    _:      dict    = Depends(solo_empleados)
):
    """Retorna el detalle de un rol con sus permisos."""
    return obtener_rol(db, id_rol)


@router.post("/", response_model=RolResponse, status_code=201)
def agregar_rol(
    datos: RolCreate,
    db:    Session = Depends(get_db),
    _:     dict    = Depends(solo_empleados)
):
    """Crea un nuevo rol."""
    return crear_rol(db, datos)


@router.put("/{id_rol}", response_model=RolResponse)
def actualizar_rol(
    id_rol: int,
    datos:  RolUpdate,
    db:     Session = Depends(get_db),
    _:      dict    = Depends(solo_empleados)
):
    """Edita el nombre o ícono de un rol. Roles protegidos retornan 403."""
    return editar_rol(db, id_rol, datos)


@router.patch("/{id_rol}/estado", response_model=RolResponse)
def toggle_estado(
    id_rol: int,
    datos:  RolEstado,
    db:     Session = Depends(get_db),
    _:      dict    = Depends(solo_empleados)
):
    """Cambia el estado ON/OFF de un rol."""
    return cambiar_estado(db, id_rol, datos.Estado)


@router.delete("/{id_rol}")
def borrar_rol(
    id_rol: int,
    db:     Session = Depends(get_db),
    _:      dict    = Depends(solo_empleados)
):
    """Elimina un rol. Roles protegidos retornan 403."""
    return eliminar_rol(db, id_rol)


@router.put("/{id_rol}/permisos", response_model=RolResponse)
def gestionar_permisos(
    id_rol: int,
    datos:  AsignarPermisos,
    db:     Session = Depends(get_db),
    _:      dict    = Depends(solo_empleados)
):
    """
    Reemplaza los permisos del rol con la lista enviada.
    Para quitar todos los permisos enviar: { 'permisos_ids': [] }
    """
    return asignar_permisos(db, id_rol, datos.permisos_ids)