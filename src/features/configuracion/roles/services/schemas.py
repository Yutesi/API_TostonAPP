from pydantic import BaseModel
from typing import Optional


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
# FIX: eliminado campo Estado — Permiso NO tiene columna Estado en BD
class PermisoResponse(BaseModel):
    ID_Permiso:  int
    Permiso:     str
    Descripcion: Optional[str] = None

    class Config:
        from_attributes = True


# ── Respuesta de un rol ──
# FIX: eliminado Fecha_creacion — Rol NO tiene esa columna en BD
# FIX: Icono es Optional[str] porque en el service se convierte a None/base64, no bytes crudos
class RolResponse(BaseModel):
    ID_Rol:    int
    Rol:       str
    Icono:     Optional[str] = None
    Estado:    Optional[int] = None
    protegido: bool = False
    permisos:  list[PermisoResponse] = []

    class Config:
        from_attributes = True


# ── Respuesta paginada ──
class RolListResponse(BaseModel):
    total: int
    roles: list[RolResponse]


# ── Asignar/quitar permisos a un rol ──
class AsignarPermisos(BaseModel):
    permisos_ids: list[int]