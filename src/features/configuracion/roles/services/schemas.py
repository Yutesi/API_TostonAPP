from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ── IDs de roles protegidos (no se pueden editar ni eliminar) ──
ROLES_PROTEGIDOS = [1]  # ID del rol Admin


# ── Crear rol ──
class RolCreate(BaseModel):
    Rol:   str
    Icono: Optional[str] = None     # URL, ruta o emoji


# ── Editar rol ──
class RolUpdate(BaseModel):
    Rol:   Optional[str] = None
    Icono: Optional[str] = None


# ── Cambiar estado ON/OFF ──
class RolEstado(BaseModel):
    Estado: int


# ── Respuesta de un permiso (para listar dentro del rol) ──
class PermisoResponse(BaseModel):
    ID_Permiso:  int
    Permiso:     str
    Descripcion: Optional[str] = None

    class Config:
        from_attributes = True


# ── Respuesta de un rol ──
class RolResponse(BaseModel):
    ID_Rol:         int
    Rol:            str
    Icono:          Optional[str] = None
    Estado:         Optional[int] = None
    protegido:      bool = False            # calculado en el código
    permisos:       list[PermisoResponse] = []

    class Config:
        from_attributes = True


# ── Respuesta paginada ──
class RolListResponse(BaseModel):
    total: int
    roles: list[RolResponse]


# ── Asignar/quitar permisos a un rol ──
class AsignarPermisos(BaseModel):
    permisos_ids: list[int]     # lista de IDs de permisos a asignar