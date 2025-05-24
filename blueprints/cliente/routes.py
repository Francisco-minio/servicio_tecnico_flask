from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required
from models import Cliente
from extensions import db
from . import cliente_bp

@cliente_bp.route('/')
@login_required
def listar_clientes():
    clientes = Cliente.query.all()
    return render_template('clientes/lista.html', clientes=clientes)

@cliente_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_cliente():
    if request.method == 'POST':
        cliente = Cliente(
            nombre=request.form['nombre'],
            correo=request.form['correo'],
            telefono=request.form.get('telefono'),
            direccion=request.form.get('direccion')
        )
        db.session.add(cliente)
        db.session.commit()
        flash('Cliente creado exitosamente', 'success')
        return redirect(url_for('cliente.listar_clientes'))
    return render_template('clientes/form.html')

@cliente_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    if request.method == 'POST':
        cliente.nombre = request.form['nombre']
        cliente.correo = request.form['correo']
        cliente.telefono = request.form.get('telefono')
        cliente.direccion = request.form.get('direccion')
        db.session.commit()
        flash('Cliente actualizado exitosamente', 'success')
        return redirect(url_for('cliente.listar_clientes'))
    return render_template('clientes/form.html', cliente=cliente)

@cliente_bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    db.session.delete(cliente)
    db.session.commit()
    flash('Cliente eliminado exitosamente', 'success')
    return redirect(url_for('cliente.listar_clientes')) 