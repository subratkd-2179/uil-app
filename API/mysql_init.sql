-- MySQL initialization script for UIL Tutor AI
-- Adjust hostname/credentials as needed before running

SET FOREIGN_KEY_CHECKS = 0;

CREATE DATABASE IF NOT EXISTS `uil_tutor` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `uil_tutor`;

-- Students table
CREATE TABLE IF NOT EXISTS `students` (
  `student_id` VARCHAR(64) NOT NULL,
  `name` VARCHAR(255) DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`student_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Evaluations table
CREATE TABLE IF NOT EXISTS `evaluations` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `student_id` VARCHAR(64) NOT NULL,
  `correct_answers` INT DEFAULT NULL,
  `wrong_answers` INT DEFAULT NULL,
  `total_questions` INT DEFAULT NULL,
  `accuracy` DOUBLE DEFAULT NULL,
  `focus_areas` TEXT,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_evaluations_student` (`student_id`),
  CONSTRAINT `fk_eval_student` FOREIGN KEY (`student_id`) REFERENCES `students` (`student_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Training data table
CREATE TABLE IF NOT EXISTS `training_data` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `filename` VARCHAR(255) DEFAULT NULL,
  `upload_date` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `file_type` VARCHAR(50) DEFAULT NULL,
  `status` VARCHAR(50) DEFAULT 'processing',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Users table for authentication
CREATE TABLE IF NOT EXISTS `users` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(150) NOT NULL,
  `email` VARCHAR(255) DEFAULT NULL,
  `password_hash` VARCHAR(255) NOT NULL,
  `token` VARCHAR(128) DEFAULT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_users_username` (`username`),
  UNIQUE KEY `uq_users_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
