from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.shared.services.database import get_db
from .schemas import LoginInput, TokenResponse
from .service import autenticar, crear_token, obtener_nombre_rol
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

    # Usa el ID autoincremental según el tipo
    id_persona = registro.ID_Empleado if tipo == "empleado" else registro.ID_Usuario

    token = crear_token({
        "id":   id_persona,         # ← ID autoincremental
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
    registro = actual["registro"]
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