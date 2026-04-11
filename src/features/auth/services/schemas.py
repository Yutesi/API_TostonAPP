from pydantic import BaseModel, model_validator
from typing import Optional
from pydantic import Field


# ── Login ──
class LoginInput(BaseModel):
    correo:     str = Field(example="admin@empresa.com")
    contrasena: str = Field(example="Admin123@")


# ── Token interno ──
class TokenData(BaseModel):
    cedula: Optional[int] = None
    tipo:   Optional[str] = None
    rol:    Optional[str] = None


# ── Respuesta de login / registro ──
class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    tipo:         str
    cedula:       int
    nombre:       str
    apellidos:    str
    rol:          Optional[str] = None


# ── Registro nuevo cliente ──
class RegistroInput(BaseModel):
    Nombre:               str = Field(example="Ana")
    Apellidos:            str = Field(example="García")
    Correo:               str = Field(example="ana@gmail.com")
    Contrasena:           str = Field(example="MiClave123@")
    Confirmar_contrasena: str = Field(example="MiClave123@")

    @model_validator(mode="after")
    def validar_contrasenas(self):
        if self.Contrasena != self.Confirmar_contrasena:
            raise ValueError("Las contraseñas no coinciden")
        return self


# ── Recuperación de contraseña ──
class RecuperarContrasenaInput(BaseModel):
    correo: str = Field(example="admin@empresa.com")


class RecuperarContrasenaResponse(BaseModel):
    mensaje:     str
    reset_token: str


# ── Resetear contraseña ──
class ResetearContrasenaInput(BaseModel):
    token:            str = Field(example="eyJhbGci...")
    nueva_contrasena: str = Field(example="NuevaClave123@")


class ResetearContrasenaResponse(BaseModel):
    mensaje: str