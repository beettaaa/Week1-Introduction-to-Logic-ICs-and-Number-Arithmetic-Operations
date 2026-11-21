-- Run this script as a MariaDB administrator before starting the Flask app.
-- Change the example password and keep it identical to DB_PASSWORD in your environment.
CREATE DATABASE IF NOT EXISTS bitgate
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'bitgate_user'@'localhost' IDENTIFIED BY 'ChangeMe123!';
ALTER USER 'bitgate_user'@'localhost' IDENTIFIED BY 'ChangeMe123!';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX
  ON bitgate.* TO 'bitgate_user'@'localhost';
FLUSH PRIVILEGES;

USE bitgate;
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('student','professor') NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
