"""Agregar campos de preferencias de usuario

Revision ID: f79382490ba2
Revises: caea7574b92d
Create Date: 2024-05-23 23:20:34.820000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, Boolean, DateTime
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'f79382490ba2'
down_revision = 'caea7574b92d'
branch_labels = None
depends_on = None

def upgrade():
    # Crear tabla temporal para usuarios
    usuarios = table('usuarios',
        column('correo', String),
        column('email', String),
        column('activo', Boolean),
        column('fecha_registro', DateTime),
        column('notificaciones_email', Boolean),
        column('tema_oscuro', Boolean),
        column('idioma', String)
    )
    
    # Agregar columnas nuevas si no existen
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('usuarios')]
    
    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        if 'nombre' not in columns:
            batch_op.add_column(sa.Column('nombre', sa.String(length=120)))
        if 'activo' not in columns:
            batch_op.add_column(sa.Column('activo', sa.Boolean(), nullable=True))
        if 'fecha_registro' not in columns:
            batch_op.add_column(sa.Column('fecha_registro', sa.DateTime(), nullable=True))
        if 'ultimo_acceso' not in columns:
            batch_op.add_column(sa.Column('ultimo_acceso', sa.DateTime(), nullable=True))
        if 'notificaciones_email' not in columns:
            batch_op.add_column(sa.Column('notificaciones_email', sa.Boolean(), nullable=True))
        if 'tema_oscuro' not in columns:
            batch_op.add_column(sa.Column('tema_oscuro', sa.Boolean(), nullable=True))
        if 'idioma' not in columns:
            batch_op.add_column(sa.Column('idioma', sa.String(length=2), nullable=True))
        
        # Establecer valores por defecto
        op.execute(
            usuarios.update().values({
                'activo': True,
                'fecha_registro': datetime.utcnow(),
                'notificaciones_email': True,
                'tema_oscuro': False,
                'idioma': 'es'
            })
        )
        
        # Modificar columnas existentes
        batch_op.alter_column('username',
                            existing_type=sa.VARCHAR(length=50),
                            type_=sa.String(length=80),
                            existing_nullable=False)
        batch_op.alter_column('rol',
                            existing_type=sa.VARCHAR(length=20),
                            nullable=True)
        
        # Eliminar columna correo si existe
        if 'correo' in columns:
            batch_op.drop_column('correo')

def downgrade():
    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        batch_op.add_column(sa.Column('correo', sa.VARCHAR(length=100), nullable=True))
        batch_op.alter_column('rol',
                            existing_type=sa.VARCHAR(length=20),
                            nullable=False)
        batch_op.alter_column('username',
                            existing_type=sa.String(length=80),
                            type_=sa.VARCHAR(length=50),
                            existing_nullable=False)
        batch_op.drop_column('idioma')
        batch_op.drop_column('tema_oscuro')
        batch_op.drop_column('notificaciones_email')
        batch_op.drop_column('ultimo_acceso')
        batch_op.drop_column('fecha_registro')
        batch_op.drop_column('activo')
        batch_op.drop_column('nombre')
        batch_op.drop_column('email')
