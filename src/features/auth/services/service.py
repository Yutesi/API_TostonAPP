from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

from src.shared.services.models import Usuario, Empleado, Rol

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")
EXPIRE_MIN = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verificar_contrasena(contrasena_plana: str, contrasena_hash: str) -> bool:
    return pwd_context.verify(contrasena_plana, contrasena_hash)


def hashear_contrasena(contrasena: str) -> str:
    return pwd_context.hash(contrasena)


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


def crear_token(data: dict) -> str:
    payload = data.copy()
    expiracion = datetime.utcnow() + timedelta(minutes=EXPIRE_MIN)
    payload.update({"exp": expiracion})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def autenticar(db: Session, correo: str, contrasena: str):
    registro, tipo = buscar_por_correo(db, correo)

    if not registro:
        return None, None

    if not verificar_contrasena(contrasena, registro.Contrasena):
        return None, None

    return registro, tipo