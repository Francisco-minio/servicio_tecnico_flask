from contextlib import contextmanager
from extensions import db
import logging

logger = logging.getLogger(__name__)

@contextmanager
def db_session():
    """Provee un contexto seguro para las transacciones de base de datos."""
    try:
        yield db.session
        db.session.commit()
    except Exception as e:
        logger.error(f"Error en la transacción de base de datos: {str(e)}")
        db.session.rollback()
        raise
    finally:
        db.session.remove()

@contextmanager
def atomic_transaction():
    """Contexto para operaciones atómicas que requieren commit o rollback."""
    session = db.session
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Transacción revertida: {str(e)}")
        raise
    finally:
        session.close() 