CREATE DATABASE IF NOT EXISTS ejercicios_flask;
USE ejercicios_flask;

CREATE TABLE IF NOT EXISTS pares_impares (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tipo VARCHAR(10) NOT NULL,
    valor INT NOT NULL
);

CREATE TABLE IF NOT EXISTS tablas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero INT NOT NULL,
    factor INT NOT NULL,
    resultado INT NOT NULL
);

CREATE TABLE IF NOT EXISTS intentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero_secreto INT NOT NULL,
    intento INT NOT NULL,
    total_intentos INT NOT NULL
);