from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade
import os
from models import db
from factory import create_app

def init_db():
    app = create_app('development')
    
    with app.app_context():
        # Crear todas las tablas
        db.create_all()
        
        print("Base de datos inicializada correctamente.")

if __name__ == '__main__':
    init_db() 