from app import create_app
from extensions import db
from models import Usuario, Cliente, Orden, Historial, Imagen, Solicitud
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Activa el contexto de la app
app = create_app()
app.app_context().push()

# Conexiones
SQLITE_URI = 'sqlite:///app.db'  # Ajusta según corresponda
MYSQL_URI = 'mysql+pymysql://usuario:contraseña@localhost/mi_base'

engine_sqlite = create_engine(SQLITE_URI)
engine_mysql = create_engine(MYSQL_URI)

SessionSqlite = sessionmaker(bind=engine_sqlite)
SessionMysql = sessionmaker(bind=engine_mysql)

session_sqlite = SessionSqlite()
session_mysql = SessionMysql()

def migrar_tabla(modelo):
    print(f"➡️ Migrando: {modelo.__tablename__}")
    registros = session_sqlite.query(modelo).all()
    for r in registros:
        session_mysql.merge(r)
    session_mysql.commit()
    print(f"✅ {len(registros)} registros migrados de {modelo.__tablename__}.")

def main():
    try:
        migrar_tabla(Usuario)
        migrar_tabla(Cliente)
        migrar_tabla(Orden)
        migrar_tabla(Historial)
        migrar_tabla(Imagen)
        migrar_tabla(Solicitud)
        print("\n🎉 Migración completada con éxito.")
    except Exception as e:
        print("\n❌ Error durante la migración:", e)
    finally:
        session_sqlite.close()
        session_mysql.close()

if __name__ == "__main__":
    main()