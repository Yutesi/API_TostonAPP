from pydantic import BaseModel
from typing import Optional
from pydantic import Field


# ── Lo que llega en el body del login ──
class LoginInput(BaseModel):
    correo:     str = Field(example="admin@empresa.com")
    contrasena: str = Field(example="Admin123@")


# ── Lo que se guarda dentro del token JWT ──
class TokenData(BaseModel):
    cedula: Optional[int] = None
    tipo:   Optional[str] = None    # "usuario" o "empleado"
    rol:    Optional[str] = None


# ── Lo que se retorna al frontend después del login ──
class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    tipo:         str                   # "usuario" o "empleado"
    cedula:       int
    nombre:       str
    apellidos:    str
    rol:          Optional[str] = None  # Solo viene si es empleado


# ── Recuperación de contraseña ──
class RecuperarContrasenaInput(BaseModel):
    correo: str = Field(example="admin@empresa.com")


class RecuperarContrasenaResponse(BaseModel):
    mensaje:     str
    # TEMPORAL — en producción este token viajará por correo, no en la respuesta
    reset_token: str


# ── Resetear contraseña ──
class ResetearContrasenaInput(BaseModel):
    token:            str = Field(example="eyJhbGci...")
    nueva_contrasena: str = Field(example="NuevaClave123@")


class ResetearContrasenaResponse(BaseModel):
    mensaje: str