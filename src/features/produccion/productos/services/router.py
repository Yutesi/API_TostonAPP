from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional

from src.shared.services.database import get_db
from src.features.auth.services.dependencies import solo_empleados
from .schemas import ProductoCreate, ProductoUpdate, ProductoResponse, ProductoListResponse
from .service import (
    obtener_productos,
    obtener_producto,
    crear_producto,
    editar_producto,
    agregar_imagenes,
    eliminar_imagen,
    eliminar_producto
)

router = APIRouter(prefix="/productos", tags=["Gestión de Productos"])


@router.get("/", response_model=ProductoListResponse)
def listar_productos(
    pagina:     int           = Query(1, ge=1),
    por_pagina: int           = Query(10, ge=1, le=100),
    busqueda:   Optional[str] = Query(None),
    db:         Session       = Depends(get_db),
    _:          dict          = Depends(solo_empleados)
):
    """Lista paginada de productos. Busca por nombre o categoría."""
    return obtener_productos(db, pagina, por_pagina, busqueda)


@router.get("/{id_producto}", response_model=ProductoResponse)
def ver_producto(
    id_producto: int,
    db:          Session = Depends(get_db),
    _:           dict    = Depends(solo_empleados)
):
    """Retorna el detalle de un producto con imágenes y ficha técnica."""
    return obtener_producto(db, id_producto)


@router.post("/", response_model=ProductoResponse, status_code=201)
def agregar_producto(
    datos: ProductoCreate,
    db:    Session = Depends(get_db),
    _:     dict    = Depends(solo_empleados)
):
    """
    Crea un producto. El estado se calcula automáticamente según stock.
    Opcionalmente crea la ficha técnica si se incluye en el body.
    """
    return crear_producto(db, datos)


@router.put("/{id_producto}", response_model=ProductoResponse)
def actualizar_producto(
    id_producto: int,
    datos:       ProductoUpdate,
    db:          Session = Depends(get_db),
    _:           dict    = Depends(solo_empleados)
):
    """Edita el producto. El estado se recalcula automáticamente."""
    return editar_producto(db, id_producto, datos)


@router.post("/{id_producto}/imagenes", response_model=ProductoResponse)
def subir_imagenes(
    id_producto: int,
    imagenes:    list[UploadFile] = File(...),
    db:          Session          = Depends(get_db),
    _:           dict             = Depends(solo_empleados)
):
    """
    Sube una o varias imágenes al producto.
    Enviar como multipart/form-data con el campo 'imagenes'.
    """
    return agregar_imagenes(db, id_producto, imagenes)


@router.delete("/{id_producto}/imagenes/{id_imagen}")
def borrar_imagen(
    id_producto: int,
    id_imagen:   int,
    db:          Session = Depends(get_db),
    _:           dict    = Depends(solo_empleados)
):
    """Elimina una imagen específica del producto."""
    return eliminar_imagen(db, id_imagen)


@router.delete("/{id_producto}")
def borrar_producto(
    id_producto: int,
    db:          Session = Depends(get_db),
    _:           dict    = Depends(solo_empleados)
):
    """Elimina el producto junto con sus imágenes y ficha técnica."""
    return eliminar_producto(db, id_producto)