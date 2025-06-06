-- Crear la base de datos si no existe
CREATE DATABASE IF NOT EXISTS ordenes_db;
USE ordenes_db;

-- Crear usuario si no existe y dar permisos
CREATE USER IF NOT EXISTS 'servicio_tecnico'@'%' IDENTIFIED BY 'servicio_tecnico_password';
GRANT ALL PRIVILEGES ON ordenes_db.* TO 'servicio_tecnico'@'%';
FLUSH PRIVILEGES; 