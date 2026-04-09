from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

from src.shared.services.models import Usuario, Empleado, Rol

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")
EXPIRE_MIN = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Expiración del token de recuperación: 15 minutos
RESET_TOKEN_EXPIRE_MIN = 15

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ─────────────────────────────────────────
# UTILIDADES DE CONTRASEÑA Y TOKEN
# ─────────────────────────────────────────

def verificar_contrasena(contrasena_plana: str, contrasena_hash: str) -> bool:
    return pwd_context.verify(contrasena_plana, contrasena_hash)


def hashear_contrasena(contrasena: str) -> str:
    return pwd_context.hash(contrasena)


def crear_token(data: dict) -> str:
    payload = data.copy()
    expiracion = datetime.utcnow() + timedelta(minutes=EXPIRE_MIN)
    payload.update({"exp": expiracion})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def crear_reset_token(correo: str) -> str:
    """
    Genera un JWT de uso exclusivo para recuperación de contraseña.
    Se distingue del token de sesión por el campo 'tipo': 'reset'.
    Expira en 15 minutos.
    """
    payload = {
        "correo": correo,
        "tipo":   "reset",          # ← distingue este token del token de sesión
        "exp":    datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MIN),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def validar_reset_token(token: str) -> str:
    """
    Valida el token de recuperación y retorna el correo si es válido.
    Lanza ValueError con mensaje descriptivo si algo falla.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise ValueError("Token inválido o expirado")

    # Verificar que sea un token de reset, no uno de sesión
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
# RECUPERACIÓN DE CONTRASEÑA
# ─────────────────────────────────────────

def solicitar_recuperacion(db: Session, correo: str) -> str:
    """
    Busca el correo en la BD y genera un reset token.
    Siempre retorna un token (incluso si el correo no existe)
    para no revelar qué correos están registrados.
    Si el correo no existe, retorna un token dummy no funcional.

    En producción: aquí se enviaría el token por correo
    y esta función retornaría solo un mensaje genérico.
    """
    registro, _ = buscar_por_correo(db, correo)

    # Correo no registrado → token dummy para no revelar información
    if not registro:
        return crear_reset_token("no-registrado@dummy.com")

    return crear_reset_token(correo)


def resetear_contrasena(db: Session, token: str, nueva_contrasena: str) -> None:
    """
    Valida el token y actualiza la contraseña del usuario en BD.
    Lanza HTTPException si el token es inválido/expirado.
    """
    # Validar token y extraer correo
    correo = validar_reset_token(token)   # lanza ValueError si es inválido

    # Buscar el registro en BD
    registro, _ = buscar_por_correo(db, correo)
    if not registro:
        raise ValueError("El correo asociado al token no existe en el sistema")

    # Actualizar contraseña
    registro.Contrasena = hashear_contrasena(nueva_contrasena)
    db.commit()