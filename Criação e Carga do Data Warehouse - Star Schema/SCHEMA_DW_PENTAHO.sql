-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
-- -----------------------------------------------------
-- Schema tce_pb
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema tce_pb
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `tce_pb` ;
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `tce_pb_dw` ;

USE `tce_pb_dw` ;

-- -----------------------------------------------------
-- Table `tce_pb_dw`.`dim_tempo`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `tce_pb_dw`.`dim_tempo` (
  `sk_tempo` INT NOT NULL COMMENT 'Surrogate key formato YYYYMMDD',
  `data` DATE NOT NULL,
  `ano` SMALLINT NOT NULL,
  `mes` TINYINT NOT NULL,
  `nome_mes` VARCHAR(15) NOT NULL,
  `trimestre` TINYINT NOT NULL,
  `nome_trimestre` VARCHAR(5) NOT NULL,
  `semestre` TINYINT NOT NULL,
  `dia` TINYINT NOT NULL,
  `dia_semana` TINYINT NOT NULL COMMENT '1=Segunda, 7=Domingo',
  `nome_dia_semana` VARCHAR(15) NOT NULL,
  `eh_fim_semana` TINYINT NOT NULL DEFAULT FALSE,
  `date_to` TIMESTAMP NULL,
  `date_from` TIMESTAMP NULL,
  `version` INT(11) NULL,
  PRIMARY KEY (`sk_tempo`),
  UNIQUE INDEX `uk_data` (`data` ASC) VISIBLE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `tce_pb_dw`.`dim_estrutura_administrativa`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `tce_pb_dw`.`dim_estrutura_administrativa` (
  `sk_estrutura_admin` INT NOT NULL AUTO_INCREMENT,
  `codigo_unidade_gestora` VARCHAR(20) NOT NULL,
  `descricao_unidade_gestora` VARCHAR(255) NOT NULL,
  `codigo_unidade_orcamentaria` VARCHAR(20) NOT NULL,
  `descricao_unidade_orcamentaria` VARCHAR(255) NOT NULL,
  `nome_municipio` VARCHAR(150) NOT NULL,
  `date_to` TIMESTAMP NULL,
  `date_from` TIMESTAMP NULL,
  `version` INT(11) NULL,
  PRIMARY KEY (`sk_estrutura_admin`),
  UNIQUE INDEX `uk_ug_uo` (`codigo_unidade_gestora` ASC, `codigo_unidade_orcamentaria` ASC) VISIBLE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `tce_pb_dw`.`dim_fornecedor`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `tce_pb_dw`.`dim_fornecedor` (
  `sk_fornecedor` INT NOT NULL AUTO_INCREMENT,
  `cpf_cnpj` VARCHAR(20) NULL DEFAULT NULL,
  `nome` VARCHAR(255) NOT NULL,
  `tipo_pessoa` CHAR(2) NOT NULL DEFAULT 'ND' COMMENT 'PF=Fisica, PJ=Juridica, ND=Nao Definido',
  `date_to` TIMESTAMP NULL,
  `date_from` TIMESTAMP NULL,
  `version` INT(11) NULL,
  PRIMARY KEY (`sk_fornecedor`),
  UNIQUE INDEX `uk_cpf_cnpj` (`cpf_cnpj` ASC) VISIBLE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `tce_pb_dw`.`dim_programa_acao`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `tce_pb_dw`.`dim_programa_acao` (
  `sk_programa_acao` INT NOT NULL AUTO_INCREMENT,
  `codigo_programa` VARCHAR(20) NULL DEFAULT NULL,
  `descricao_programa` VARCHAR(255) NULL DEFAULT NULL,
  `codigo_acao` VARCHAR(20) NULL DEFAULT NULL,
  `descricao_acao` VARCHAR(255) NULL DEFAULT NULL,
  `date_to` TIMESTAMP NULL,
  `date_from` TIMESTAMP NULL,
  `version` INT(11) NULL,
  PRIMARY KEY (`sk_programa_acao`),
  INDEX `uk_prog_acao` (`codigo_programa` ASC, `codigo_acao` ASC) VISIBLE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `tce_pb_dw`.`dim_fonte_recurso`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `tce_pb_dw`.`dim_fonte_recurso` (
  `sk_fonte_recurso` INT NOT NULL AUTO_INCREMENT,
  `codigo_fonte_recurso` VARCHAR(20) NOT NULL,
  `descricao_fonte_recurso` VARCHAR(255) NOT NULL,
  `ano_fonte` VARCHAR(10) NOT NULL,
  `date_to` TIMESTAMP NULL,
  `date_from` TIMESTAMP NULL,
  `version` INT(11) NULL,
  PRIMARY KEY (`sk_fonte_recurso`),
  UNIQUE INDEX `uk_fonte_ano` (`codigo_fonte_recurso` ASC, `ano_fonte` ASC) VISIBLE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `tce_pb_dw`.`dim_licitacao`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `tce_pb_dw`.`dim_licitacao` (
  `sk_licitacao` INT NOT NULL AUTO_INCREMENT,
  `numero_licitacao` VARCHAR(50) NULL DEFAULT NULL,
  `numero_protocolo_tce` VARCHAR(50) NULL DEFAULT NULL,
  `ano_licitacao` SMALLINT NULL DEFAULT NULL,
  `modalidade` VARCHAR(100) NOT NULL DEFAULT 'NAO INFORMADO',
  `objeto_licitacao` TEXT NULL DEFAULT NULL,
  `data_homologacao` DATE NULL DEFAULT NULL,
  `date_to` TIMESTAMP NULL,
  `date_from` TIMESTAMP NULL,
  `version` INT(11) NULL,
  PRIMARY KEY (`sk_licitacao`),
  UNIQUE INDEX `uk_licitacao` (`numero_licitacao` ASC, `numero_protocolo_tce` ASC) VISIBLE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `tce_pb_dw`.`fato_empenho`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `tce_pb_dw`.`fato_empenho` (
  `sk_tempo` INT NOT NULL,
  `sk_estrutura_admin` INT NOT NULL,
  `sk_fornecedor` INT NOT NULL,
  `sk_programa_acao` INT NOT NULL,
  `sk_fonte_recurso` INT NOT NULL,
  `sk_licitacao` INT NOT NULL,
  `valor_empenhado` DECIMAL(15,2) NOT NULL DEFAULT 0,
  `valor_liquidado` DECIMAL(15,2) NOT NULL DEFAULT 0,
  `valor_pago` DECIMAL(15,2) NOT NULL DEFAULT 0,
  `saldo_a_pagar` DECIMAL(15,2) NOT NULL DEFAULT 0 COMMENT 'Calculada: empenhado - pago',
  PRIMARY KEY (`sk_tempo`, `sk_estrutura_admin`, `sk_fornecedor`, `sk_programa_acao`, `sk_fonte_recurso`, `sk_licitacao`),
  INDEX `idx_fato_tempo` (`sk_tempo` ASC) VISIBLE,
  INDEX `idx_fato_estrutura` (`sk_estrutura_admin` ASC) VISIBLE,
  INDEX `idx_fato_fornecedor` (`sk_fornecedor` ASC) VISIBLE,
  INDEX `idx_fato_prog_acao` (`sk_programa_acao` ASC) VISIBLE,
  INDEX `idx_fato_fonte` (`sk_fonte_recurso` ASC) VISIBLE,
  INDEX `idx_fato_licitacao` (`sk_licitacao` ASC) VISIBLE,
  CONSTRAINT `fk_fato_tempo`
    FOREIGN KEY (`sk_tempo`)
    REFERENCES `tce_pb_dw`.`dim_tempo` (`sk_tempo`),
  CONSTRAINT `fk_fato_estrutura`
    FOREIGN KEY (`sk_estrutura_admin`)
    REFERENCES `tce_pb_dw`.`dim_estrutura_administrativa` (`sk_estrutura_admin`),
  CONSTRAINT `fk_fato_fornecedor`
    FOREIGN KEY (`sk_fornecedor`)
    REFERENCES `tce_pb_dw`.`dim_fornecedor` (`sk_fornecedor`),
  CONSTRAINT `fk_fato_prog_acao`
    FOREIGN KEY (`sk_programa_acao`)
    REFERENCES `tce_pb_dw`.`dim_programa_acao` (`sk_programa_acao`),
  CONSTRAINT `fk_fato_fonte`
    FOREIGN KEY (`sk_fonte_recurso`)
    REFERENCES `tce_pb_dw`.`dim_fonte_recurso` (`sk_fonte_recurso`),
  CONSTRAINT `fk_fato_licitacao`
    FOREIGN KEY (`sk_licitacao`)
    REFERENCES `tce_pb_dw`.`dim_licitacao` (`sk_licitacao`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
