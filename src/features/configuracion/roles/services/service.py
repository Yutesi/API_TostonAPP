from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime

from src.shared.services.models import Rol, Permiso, RolXPermiso
from .schemas import RolCreate, RolUpdate, ROLES_PROTEGIDOS


def _es_protegido(id_rol: int) -> bool:
    return id_rol in ROLES_PROTEGIDOS


def _formato_rol(rol, db: Session) -> dict:
    """Construye el dict de respuesta con permisos y flag protegido."""
    permisos = (
        db.query(Permiso)
        .join(RolXPermiso, RolXPermiso.ID_Permiso == Permiso.ID_Permiso)
        .filter(RolXPermiso.ID_Rol == rol.ID_Rol)
        .all()
    )
    return {
        "ID_Rol":         rol.ID_Rol,
        "Rol":            rol.Rol,
        "Icono":          rol.Icono,
        "Fecha_creacion": rol.Fecha_creacion,
        "protegido":      _es_protegido(rol.ID_Rol),
        "permisos": [
            {
                "ID_Permiso":  p.ID_Permiso,
                "Permiso":     p.Permiso,
                "Descripcion": p.Descripcion,
                "Estado":      p.Estado,
            }
            for p in permisos
        ],
    }


def obtener_roles(db: Session, busqueda: str = None):
    """Retorna todos los roles, opcionalmente filtrados por nombre."""
    query = db.query(Rol)
    if busqueda:
        query = query.filter(Rol.Rol.ilike(f"%{busqueda}%"))

    roles = query.all()
    return {
        "total": len(roles),
        "roles": [_formato_rol(r, db) for r in roles]
    }


def obtener_rol(db: Session, id_rol: int):
    """Retorna un rol por ID o lanza 404."""
    rol = db.query(Rol).filter(Rol.ID_Rol == id_rol).first()
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return _formato_rol(rol, db)


def crear_rol(db: Session, datos: RolCreate):
    """Crea un nuevo rol."""
    if db.query(Rol).filter(Rol.Rol == datos.Rol).first():
        raise HTTPException(status_code=400, detail="Ya existe un rol con ese nombre")

    nuevo = Rol(
        Rol            = datos.Rol,
        Icono          = datos.Icono,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return _formato_rol(nuevo, db)


def editar_rol(db: Session, id_rol: int, datos: RolUpdate):
    """Edita un rol. Los roles protegidos no se pueden editar."""
    if _es_protegido(id_rol):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este rol está protegido y no puede editarse"
        )

    rol = db.query(Rol).filter(Rol.ID_Rol == id_rol).first()
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    for campo, valor in datos.model_dump(exclude_none=True).items():
        setattr(rol, campo, valor)

    db.commit()
    db.refresh(rol)
    return _formato_rol(rol, db)


def cambiar_estado(db: Session, id_rol: int, nuevo_estado: int):
    """Cambia el estado ON/OFF de un rol."""
    if _es_protegido(id_rol):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este rol está protegido y no puede modificarse"
        )

    rol = db.query(Rol).filter(Rol.ID_Rol == id_rol).first()
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    rol.Estado = nuevo_estado
    db.commit()
    db.refresh(rol)
    return _formato_rol(rol, db)


def eliminar_rol(db: Session, id_rol: int):
    """Elimina un rol. Los roles protegidos no se pueden eliminar."""
    if _es_protegido(id_rol):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este rol está protegido y no puede eliminarse"
        )

    rol = db.query(Rol).filter(Rol.ID_Rol == id_rol).first()
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    db.delete(rol)
    db.commit()
    return {"mensaje": f"Rol {rol.Rol} eliminado correctamente"}


def asignar_permisos(db: Session, id_rol: int, permisos_ids: list[int]):
    """
    Reemplaza todos los permisos de un rol con la nueva lista enviada.
    Si se manda una lista vacía, quita todos los permisos del rol.
    """
    rol = db.query(Rol).filter(Rol.ID_Rol == id_rol).first()
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    # Elimina los permisos actuales del rol
    db.query(RolXPermiso).filter(RolXPermiso.ID_Rol == id_rol).delete()

    # Asigna los nuevos permisos
    for id_permiso in permisos_ids:
        permiso = db.query(Permiso).filter(Permiso.ID_Permiso == id_permiso).first()
        if not permiso:
            raise HTTPException(status_code=404, detail=f"Permiso {id_permiso} no encontrado")
        db.add(RolXPermiso(ID_Rol=id_rol, ID_Permiso=id_permiso))

    db.commit()
    return _formato_rol(rol, db)