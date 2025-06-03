-- Establecer el modo SQL
SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

-- Crear la base de datos si no existe
CREATE DATABASE IF NOT EXISTS ordenes_db;
USE ordenes_db;

-- Crear usuario y otorgar privilegios si no existe
CREATE USER IF NOT EXISTS 'servicio_tecnico'@'%' IDENTIFIED BY 'servicio_tecnico_password';
GRANT ALL PRIVILEGES ON ordenes_db.* TO 'servicio_tecnico'@'%';
FLUSH PRIVILEGES;

-- Configurar el conjunto de caracteres
ALTER DATABASE ordenes_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Crear las tablas necesarias (las tablas se crearán automáticamente con Flask-Migrate)

-- Aquí puedes agregar la creación de tablas si es necesario
-- Las migraciones de Flask-Migrate se encargarán de esto 