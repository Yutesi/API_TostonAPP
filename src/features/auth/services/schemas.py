from pydantic import BaseModel, EmailStr
from typing import Optional


# ── Lo que llega en el body del login ──
class LoginInput(BaseModel):
    correo: EmailStr
    contrasena: str


# ── Lo que se guarda dentro del token JWT ──
class TokenData(BaseModel):
    cedula: Optional[int] = None
    tipo: Optional[str] = None      # "usuario" o "empleado"
    rol: Optional[str] = None


# ── Lo que se retorna al frontend después del login ──
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tipo: str                       # "usuario" o "empleado"
    cedula: int
    nombre: str
    apellidos: str
    rol: Optional[str] = None       # Solo viene si es empleado