from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

from src.shared.services.database import get_db
from src.shared.services.models import Usuario, Empleado
from .schemas import TokenData

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def obtener_usuario_actual(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Decodifica el token y retorna el usuario o empleado activo."""
    credenciales_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload    = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id_persona = payload.get("id")          # ← ahora usa ID_Usuario o ID_Empleado
        tipo       = payload.get("tipo")

        if id_persona is None or tipo is None:
            raise credenciales_error

        token_data = TokenData(cedula=id_persona, tipo=tipo, rol=payload.get("rol"))

    except JWTError:
        raise credenciales_error

    # Busca en la tabla correcta usando el ID autoincremental
    if tipo == "empleado":
        registro = db.query(Empleado).filter(Empleado.ID_Empleado == id_persona).first()
    else:
        registro = db.query(Usuario).filter(Usuario.ID_Usuario == id_persona).first()

    if registro is None:
        raise credenciales_error

    return {"registro": registro, "tipo": tipo, "rol": token_data.rol}


def solo_empleados(actual: dict = Depends(obtener_usuario_actual)):
    """Protege endpoints exclusivos de empleados."""
    if actual["tipo"] != "empleado":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para acceder a este recurso"
        )
    return actual