import sys
import os

# Agrega el directorio raíz al path para poder importar src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.shared.services.database import SessionLocal
from src.shared.services.models import Empleado, Usuario
from src.features.auth.services.service import hashear_contrasena

def actualizar_contrasenas():
    db = SessionLocal()
    try:
        contrasena_hash = hashear_contrasena("Admin123@")

        db.query(Empleado).update({"Contrasena": contrasena_hash})
        db.query(Usuario).update({"Contrasena": contrasena_hash})
        db.commit()

        print("✅ Contraseñas actualizadas correctamente")
    except Exception as e:
        db.rollback()
        print(f"❌ Error al actualizar contraseñas: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    actualizar_contrasenas()