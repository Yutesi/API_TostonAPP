from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from src.shared.services.database import get_db
from .schemas import (
    LoginInput,
    TokenResponse,
    RegistroInput,
    RecuperarContrasenaInput,
    RecuperarContrasenaResponse,
    ResetearContrasenaInput,
    ResetearContrasenaResponse,
)
from .service import (
    autenticar,
    crear_token,
    obtener_nombre_rol,
    registrar_cliente,
    solicitar_recuperacion,
    resetear_contrasena,
)
from .dependencies import obtener_usuario_actual
from src.shared.services.models import UsuarioXRol, Usuario


class PerfilUpdate(BaseModel):
    Telefono:    Optional[str] = None
    Direccion:   Optional[str] = None
    Municipio:   Optional[str] = None
    Departamento: Optional[str] = None

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenResponse)
def login(datos: LoginInput, db: Session = Depends(get_db)):
    """Login unificado para usuarios y empleados."""
    registro, tipo = autenticar(db, datos.correo, datos.contrasena)

    if not registro:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos"
        )

    nombre_rol = None
    if tipo == "empleado":
        nombre_rol = obtener_nombre_rol(db, registro.ID_Rol)

    id_persona = registro.ID_Empleado if tipo == "empleado" else registro.ID_Usuario

    token = crear_token({"id": id_persona, "tipo": tipo, "rol": nombre_rol})

    return TokenResponse(
        access_token = token,
        tipo         = tipo,
        cedula       = id_persona,
        nombre       = registro.Nombre,
        apellidos    = registro.Apellidos,
        rol          = nombre_rol
    )


@router.post("/registro", response_model=TokenResponse, status_code=201)
def registro(datos: RegistroInput, db: Session = Depends(get_db)):
    """
    Registro de nuevo cliente.
    Crea la cuenta, asigna rol Cliente automáticamente
    y retorna el token de sesión directamente.
    """
    nuevo = registrar_cliente(db, datos)

    # Leer el rol asignado desde Usuario_x_Rol
    uxr        = db.query(UsuarioXRol).filter(UsuarioXRol.ID_Usuario == nuevo.ID_Usuario).first()
    nombre_rol = obtener_nombre_rol(db, uxr.ID_Rol) if uxr else None

    token = crear_token({"id": nuevo.ID_Usuario, "tipo": "usuario", "rol": nombre_rol})

    return TokenResponse(
        access_token = token,
        tipo         = "usuario",
        cedula       = nuevo.ID_Usuario,
        nombre       = nuevo.Nombre,
        apellidos    = nuevo.Apellidos,
        rol          = nombre_rol
    )


@router.get("/me")
def obtener_perfil(actual: dict = Depends(obtener_usuario_actual)):
    """Retorna los datos del usuario autenticado."""
    registro   = actual["registro"]
    id_persona = registro.ID_Empleado if actual["tipo"] == "empleado" else registro.ID_Usuario

    return {
        "id":        id_persona,
        "cedula":    registro.Cedula,
        "nombre":    registro.Nombre,
        "apellidos": registro.Apellidos,
        "correo":    registro.Correo,
        "tipo":      actual["tipo"],
        "rol":       actual["rol"]
    }


@router.post("/recuperar-contrasena", response_model=RecuperarContrasenaResponse)
def recuperar_contrasena(datos: RecuperarContrasenaInput, db: Session = Depends(get_db)):
    """
    Genera un token de recuperación válido por 15 minutos.
    MODO ACTUAL: el token se retorna en la respuesta.
    MODO FUTURO: se enviará por correo y reset_token será vacío.
    """
    token = solicitar_recuperacion(db, datos.correo)
    return RecuperarContrasenaResponse(
        mensaje     = "Si el correo está registrado, recibirás instrucciones para recuperar tu contraseña.",
        reset_token = token,
    )


@router.post("/resetear-contrasena", response_model=ResetearContrasenaResponse)
def resetear(datos: ResetearContrasenaInput, db: Session = Depends(get_db)):
    """Recibe el token y la nueva contraseña. Actualiza si el token es válido."""
    try:
        resetear_contrasena(db, datos.token, datos.nueva_contrasena)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return ResetearContrasenaResponse(
        mensaje="Contraseña actualizada correctamente. Ya puedes iniciar sesión."
    )


@router.get("/perfil")
def ver_perfil(actual: dict = Depends(obtener_usuario_actual), db: Session = Depends(get_db)):
    """Retorna el perfil completo del usuario autenticado (incluye dirección y teléfono)."""
    if actual["tipo"] != "usuario":
        raise HTTPException(status_code=403, detail="Solo disponible para clientes")
    registro = actual["registro"]
    return {
        "ID_Usuario":   registro.ID_Usuario,
        "Nombre":       registro.Nombre,
        "Apellidos":    registro.Apellidos,
        "Correo":       registro.Correo,
        "Telefono":     registro.Telefono,
        "Direccion":    registro.Direccion,
        "Municipio":    registro.Municipio,
        "Departamento": registro.Departamento,
        "tipo":         actual["tipo"],
        "rol":          actual["rol"],
    }


@router.put("/perfil")
def actualizar_perfil(
    datos: PerfilUpdate,
    actual: dict = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db)
):
    """Permite al cliente autenticado actualizar su dirección y teléfono."""
    if actual["tipo"] != "usuario":
        raise HTTPException(status_code=403, detail="Solo disponible para clientes")
    registro = actual["registro"]
    usuario  = db.query(Usuario).filter(Usuario.ID_Usuario == registro.ID_Usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    for campo, valor in datos.model_dump(exclude_none=True).items():
        setattr(usuario, campo, valor)

    db.commit()
    db.refresh(usuario)
    return {
        "ID_Usuario":   usuario.ID_Usuario,
        "Nombre":       usuario.Nombre,
        "Apellidos":    usuario.Apellidos,
        "Correo":       usuario.Correo,
        "Telefono":     usuario.Telefono,
        "Direccion":    usuario.Direccion,
        "Municipio":    usuario.Municipio,
        "Departamento": usuario.Departamento,
    }