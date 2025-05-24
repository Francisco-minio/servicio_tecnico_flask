from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required
from models import Cliente
from extensions import db
from . import cliente_bp
from forms import ClienteForm

@cliente_bp.route('/')
@login_required
def listar_clientes():
    clientes = Cliente.query.all()
    return render_template('clientes/lista.html', clientes=clientes)

@cliente_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_cliente():
    form = ClienteForm()
    if form.validate_on_submit():
        cliente = Cliente()
        form.populate_obj(cliente)
        db.session.add(cliente)
        db.session.commit()
        flash('Cliente creado exitosamente', 'success')
        return redirect(url_for('cliente.listar_clientes'))
    return render_template('clientes/form.html', form=form)

@cliente_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    form = ClienteForm(obj=cliente)
    
    if form.validate_on_submit():
        form.populate_obj(cliente)
        db.session.commit()
        flash('Cliente actualizado exitosamente', 'success')
        return redirect(url_for('cliente.listar_clientes'))
        
    return render_template('clientes/form.html', cliente=cliente, form=form)

@cliente_bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    db.session.delete(cliente)
    db.session.commit()
    flash('Cliente eliminado exitosamente', 'success')
    return redirect(url_for('cliente.listar_clientes')) 