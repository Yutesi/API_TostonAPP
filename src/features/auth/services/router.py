from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.shared.services.database import get_db
from .schemas import (
    LoginInput,
    TokenResponse,
    RecuperarContrasenaInput,
    RecuperarContrasenaResponse,
    ResetearContrasenaInput,
    ResetearContrasenaResponse,
)
from .service import (
    autenticar,
    crear_token,
    obtener_nombre_rol,
    solicitar_recuperacion,
    resetear_contrasena,
)
from .dependencies import obtener_usuario_actual

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

    token = crear_token({
        "id":   id_persona,
        "tipo": tipo,
        "rol":  nombre_rol
    })

    return TokenResponse(
        access_token = token,
        tipo         = tipo,
        cedula       = id_persona,
        nombre       = registro.Nombre,
        apellidos    = registro.Apellidos,
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
    Genera un token de recuperación de contraseña válido por 15 minutos.

    MODO ACTUAL (sin email): el token se retorna directamente en la respuesta.
    MODO FUTURO (con email): el token se enviará al correo y este endpoint
    retornará solo { "mensaje": "...", "reset_token": "" }.
    """
    token = solicitar_recuperacion(db, datos.correo)

    return RecuperarContrasenaResponse(
        mensaje     = "Si el correo está registrado, recibirás instrucciones para recuperar tu contraseña.",
        reset_token = token,   # ← ELIMINAR cuando se integre el servicio de email
    )


@router.post("/resetear-contrasena", response_model=ResetearContrasenaResponse)
def resetear(datos: ResetearContrasenaInput, db: Session = Depends(get_db)):
    """
    Recibe el token de recuperación y la nueva contraseña.
    Actualiza la contraseña si el token es válido y no ha expirado.
    """
    try:
        resetear_contrasena(db, datos.token, datos.nueva_contrasena)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return ResetearContrasenaResponse(
        mensaje="Contraseña actualizada correctamente. Ya puedes iniciar sesión."
    )