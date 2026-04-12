from sqlalchemy.orm import Session
from fastapi import HTTPException
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

from src.shared.services.models import Usuario, Empleado, Rol, UsuarioXRol

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")
EXPIRE_MIN = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

RESET_TOKEN_EXPIRE_MIN = 15

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ─────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────

def verificar_contrasena(contrasena_plana: str, contrasena_hash: str) -> bool:
    return pwd_context.verify(contrasena_plana, contrasena_hash)


def hashear_contrasena(contrasena: str) -> str:
    return pwd_context.hash(contrasena)


def crear_token(data: dict) -> str:
    payload = data.copy()
    payload.update({"exp": datetime.utcnow() + timedelta(minutes=EXPIRE_MIN)})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def crear_reset_token(correo: str) -> str:
    payload = {
        "correo": correo,
        "tipo":   "reset",
        "exp":    datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MIN),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def validar_reset_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise ValueError("Token inválido o expirado")

    if payload.get("tipo") != "reset":
        raise ValueError("El token proporcionado no es un token de recuperación")

    correo = payload.get("correo")
    if not correo:
        raise ValueError("Token malformado")

    return correo


# ─────────────────────────────────────────
# BÚSQUEDA Y AUTENTICACIÓN
# ─────────────────────────────────────────

def buscar_por_correo(db: Session, correo: str):
    """Busca por correo en Empleados primero, luego en Usuarios."""
    empleado = db.query(Empleado).filter(Empleado.Correo == correo).first()
    if empleado:
        return empleado, "empleado"

    usuario = db.query(Usuario).filter(Usuario.Correo == correo).first()
    if usuario:
        return usuario, "usuario"

    return None, None


def obtener_nombre_rol(db: Session, id_rol: int) -> str:
    rol = db.query(Rol).filter(Rol.ID_Rol == id_rol).first()
    return rol.Rol if rol else None


def autenticar(db: Session, correo: str, contrasena: str):
    registro, tipo = buscar_por_correo(db, correo)

    if not registro:
        return None, None

    if not verificar_contrasena(contrasena, registro.Contrasena):
        return None, None

    return registro, tipo


# ─────────────────────────────────────────
# REGISTRO
# ─────────────────────────────────────────

def registrar_cliente(db: Session, datos) -> Usuario:
    """
    Crea un nuevo usuario (cliente) con los datos mínimos
    y le asigna automáticamente el rol Cliente en Usuario_x_Rol.
    Los campos opcionales quedan null hasta que complete su perfil.
    """
    if buscar_por_correo(db, datos.Correo)[0]:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    # Verificar que el rol Cliente existe en BD
    rol_cliente = db.query(Rol).filter(Rol.Rol == "Cliente").first()
    if not rol_cliente:
        raise HTTPException(status_code=500, detail="Rol Cliente no encontrado en el sistema")

    # Crear el usuario
    nuevo = Usuario(
        Nombre         = datos.Nombre,
        Apellidos      = datos.Apellidos,
        Correo         = datos.Correo,
        Contrasena     = hashear_contrasena(datos.Contrasena),
        Fecha_creacion = datetime.now(),
        Estado         = 1,
        Cedula         = None,
        Tipo_Documento = None,
        Direccion      = None,
        Municipio      = None,
        Departamento   = None,
        Telefono       = None,
    )
    db.add(nuevo)
    db.flush()  # genera el ID_Usuario sin hacer commit aún

    # Asignar rol Cliente automáticamente
    db.add(UsuarioXRol(
        ID_Rol     = rol_cliente.ID_Rol,
        ID_Usuario = nuevo.ID_Usuario,
    ))

    db.commit()
    db.refresh(nuevo)
    return nuevo


# ─────────────────────────────────────────
# RECUPERACIÓN DE CONTRASEÑA
# ─────────────────────────────────────────

def solicitar_recuperacion(db: Session, correo: str) -> str:
    registro, _ = buscar_por_correo(db, correo)
    if not registro:
        return crear_reset_token("no-registrado@dummy.com")
    return crear_reset_token(correo)


def resetear_contrasena(db: Session, token: str, nueva_contrasena: str) -> None:
    correo = validar_reset_token(token)

    registro, _ = buscar_por_correo(db, correo)
    if not registro:
        raise ValueError("El correo asociado al token no existe en el sistema")

    registro.Contrasena = hashear_contrasena(nueva_contrasena)
    db.commit()