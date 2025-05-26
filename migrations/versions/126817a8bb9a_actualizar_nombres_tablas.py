"""actualizar_nombres_tablas

Revision ID: 126817a8bb9a
Revises: 8dc5a87660f4
Create Date: 2024-05-24 22:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '126817a8bb9a'
down_revision = '8dc5a87660f4'
branch_labels = None
depends_on = None

def table_exists(table_name):
    """Verifica si una tabla existe en la base de datos."""
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    return table_name in inspector.get_table_names()

def upgrade():
    # Desactivar verificación de claves foráneas temporalmente
    op.execute('SET FOREIGN_KEY_CHECKS=0')
    
    try:
        # Verificar y manejar la tabla cliente/clientes
        if table_exists('cliente') and not table_exists('clientes'):
            op.rename_table('cliente', 'clientes')
        
        # Crear tabla imagenes si no existe
        if not table_exists('imagenes'):
            op.create_table('imagenes',
                sa.Column('id', sa.Integer(), nullable=False),
                sa.Column('orden_id', sa.Integer(), nullable=False),
                sa.Column('filename', sa.String(length=120), nullable=False),
                sa.ForeignKeyConstraint(['orden_id'], ['ordenes.id'], ),
                sa.PrimaryKeyConstraint('id')
            )
        
        # Crear tabla solicitudes si no existe
        if not table_exists('solicitudes'):
            op.create_table('solicitudes',
                sa.Column('id', sa.Integer(), nullable=False),
                sa.Column('tipo', sa.String(length=50), nullable=True),
                sa.Column('descripcion', sa.Text(), nullable=False),
                sa.Column('orden_id', sa.Integer(), nullable=False),
                sa.Column('usuario_id', sa.Integer(), nullable=False),
                sa.Column('fecha', sa.DateTime(), nullable=True),
                sa.ForeignKeyConstraint(['orden_id'], ['ordenes.id'], ),
                sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
                sa.PrimaryKeyConstraint('id')
            )
        
        # Actualizar las columnas de ordenes
        with op.batch_alter_table('ordenes', schema=None) as batch_op:
            # Eliminar las restricciones de clave foránea existentes
            for fk in Inspector.from_engine(op.get_bind()).get_foreign_keys('ordenes'):
                if fk['referred_table'] == 'usuarios' and 'usuario_id' in fk['constrained_columns']:
                    batch_op.drop_constraint(fk['name'], type_='foreignkey')
            
            # Agregar columnas si no existen
            columns = [c['name'] for c in Inspector.from_engine(op.get_bind()).get_columns('ordenes')]
            
            if 'fecha_actualizacion' not in columns:
                batch_op.add_column(sa.Column('fecha_actualizacion', sa.DateTime(), nullable=True))
            
            if 'usuario_id' in columns:
                batch_op.drop_column('usuario_id')
        
        # Actualizar las referencias en solicitud_cotizacion
        if table_exists('solicitud_cotizacion'):
            with op.batch_alter_table('solicitud_cotizacion', schema=None) as batch_op:
                # Actualizar la referencia a la tabla clientes
                fks = Inspector.from_engine(op.get_bind()).get_foreign_keys('solicitud_cotizacion')
                for fk in fks:
                    if fk['referred_table'] == 'cliente':
                        batch_op.drop_constraint(fk['name'], type_='foreignkey')
                        batch_op.create_foreign_key(
                            f"{fk['name']}_new",
                            'clientes',
                            ['cliente_id'],
                            ['id']
                        )
    
    finally:
        # Reactivar verificación de claves foráneas
        op.execute('SET FOREIGN_KEY_CHECKS=1')

def downgrade():
    # No implementamos downgrade para evitar pérdida de datos
    pass
