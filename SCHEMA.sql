-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema tce_pb
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema tce_pb
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `tce_pb` ;
USE `tce_pb` ;

-- -----------------------------------------------------
-- Table `tce_pb`.`fornecedor`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `tce_pb`.`fornecedor` (
  `id_fornecedor` INT NOT NULL AUTO_INCREMENT,
  `cpf_cnpj` VARCHAR(20) NULL DEFAULT NULL,
  `nome` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`id_fornecedor`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `tce_pb`.`modalidade_licitacao`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `tce_pb`.`modalidade_licitacao` (
  `id_modalidade` INT NOT NULL AUTO_INCREMENT,
  `descricao_modalidade` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`id_modalidade`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `tce_pb`.`municipio`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `tce_pb`.`municipio` (
  `id_municipio` INT NOT NULL AUTO_INCREMENT,
  `nome_municipio` VARCHAR(150) NOT NULL,
  PRIMARY KEY (`id_municipio`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `tce_pb`.`unidade_gestora`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `tce_pb`.`unidade_gestora` (
  `id_unidade_gestora` INT NOT NULL AUTO_INCREMENT,
  `codigo_unidade_gestora` VARCHAR(20) NULL DEFAULT NULL,
  `descricao_unidade_gestora` VARCHAR(255) NULL DEFAULT NULL,
  `municipio_id` INT NOT NULL,
  PRIMARY KEY (`id_unidade_gestora`),
  INDEX `fk_unidade_gestora_municipio` (`municipio_id` ASC) VISIBLE,
  CONSTRAINT `fk_unidade_gestora_municipio`
    FOREIGN KEY (`municipio_id`)
    REFERENCES `tce_pb`.`municipio` (`id_municipio`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `tce_pb`.`licitacao`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `tce_pb`.`licitacao` (
  `id_licitacao` INT NOT NULL AUTO_INCREMENT,
  `numero_licitacao` VARCHAR(50) NULL DEFAULT NULL,
  `numero_protocolo_tce` VARCHAR(50) NULL DEFAULT NULL,
  `ano_licitacao` INT NULL DEFAULT NULL,
  `data_homologacao` DATE NULL DEFAULT NULL,
  `modalidade_id` INT NULL DEFAULT NULL,
  `objeto_licitacao` TEXT NULL DEFAULT NULL,
  `unidade_gestora_id` INT NOT NULL,
  `municipio_id` INT NOT NULL,
  PRIMARY KEY (`id_licitacao`),
  INDEX `fk_licitacao_modalidade` (`modalidade_id` ASC) VISIBLE,
  INDEX `fk_licitacao_unidade_gestora` (`unidade_gestora_id` ASC) VISIBLE,
  INDEX `fk_licitacao_municipio` (`municipio_id` ASC) VISIBLE,
  CONSTRAINT `fk_licitacao_modalidade`
    FOREIGN KEY (`modalidade_id`)
    REFERENCES `tce_pb`.`modalidade_licitacao` (`id_modalidade`),
  CONSTRAINT `fk_licitacao_municipio`
    FOREIGN KEY (`municipio_id`)
    REFERENCES `tce_pb`.`municipio` (`id_municipio`),
  CONSTRAINT `fk_licitacao_unidade_gestora`
    FOREIGN KEY (`unidade_gestora_id`)
    REFERENCES `tce_pb`.`unidade_gestora` (`id_unidade_gestora`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `tce_pb`.`obra`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `tce_pb`.`obra` (
  `id_obra` INT NOT NULL AUTO_INCREMENT,
  `numero_obra` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`id_obra`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `tce_pb`.`Programa`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `tce_pb`.`Programa` (
  `id_programa` INT NOT NULL AUTO_INCREMENT,
  `codigo_programa` VARCHAR(20) NULL DEFAULT NULL,
  `descricao_programa` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`id_programa`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `tce_pb`.`acao`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `tce_pb`.`acao` (
  `id_acao` INT NOT NULL AUTO_INCREMENT,
  `codigo_acao` VARCHAR(20) NULL DEFAULT NULL,
  `descricao_acao` VARCHAR(255) NOT NULL,
  `programa_id` INT NULL,
  PRIMARY KEY (`id_acao`),
  INDEX `id_programa_idx` (`programa_id` ASC) VISIBLE,
  CONSTRAINT `id_programa`
    FOREIGN KEY (`programa_id`)
    REFERENCES `tce_pb`.`Programa` (`id_programa`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `tce_pb`.`funcao`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `tce_pb`.`funcao` (
  `id_funcao` INT NOT NULL,
  `codigo_funcao` VARCHAR(45) NOT NULL,
  `descricao_funcao` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`id_funcao`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `tce_pb`.`empenho`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `tce_pb`.`empenho` (
  `id_empenho` INT NOT NULL AUTO_INCREMENT,
  `numero_empenho` VARCHAR(50) NULL DEFAULT NULL,
  `data_empenho` DATE NULL DEFAULT NULL,
  `mes` INT NULL DEFAULT NULL,
  `unidade_gestora_id` INT NOT NULL,
  `municipio_id` INT NOT NULL,
  `credor_id` INT NULL DEFAULT NULL,
  `valor_empenhado` DECIMAL(15,2) NULL DEFAULT NULL,
  `valor_liquidado` DECIMAL(15,2) NULL DEFAULT NULL,
  `valor_pago` DECIMAL(15,2) NULL DEFAULT NULL,
  `licitacao_id` INT NULL DEFAULT NULL,
  `obra_id` INT NOT NULL,
  `acao_id` INT NULL,
  `funcao_id` INT NOT NULL,
  PRIMARY KEY (`id_empenho`),
  INDEX `fk_empenho_unidade_gestora` (`unidade_gestora_id` ASC) VISIBLE,
  INDEX `fk_empenho_municipio` (`municipio_id` ASC) VISIBLE,
  INDEX `fk_empenho_fornecedor` (`credor_id` ASC) VISIBLE,
  INDEX `fk_empenho_licitacao` (`licitacao_id` ASC) VISIBLE,
  INDEX `fk_empenho_obra1_idx` (`obra_id` ASC) VISIBLE,
  INDEX `fk_empenho_acao_idx` (`acao_id` ASC) VISIBLE,
  INDEX `fk_empenho_funcao1_idx` (`funcao_id` ASC) VISIBLE,
  CONSTRAINT `fk_empenho_fornecedor`
    FOREIGN KEY (`credor_id`)
    REFERENCES `tce_pb`.`fornecedor` (`id_fornecedor`),
  CONSTRAINT `fk_empenho_licitacao`
    FOREIGN KEY (`licitacao_id`)
    REFERENCES `tce_pb`.`licitacao` (`id_licitacao`),
  CONSTRAINT `fk_empenho_municipio`
    FOREIGN KEY (`municipio_id`)
    REFERENCES `tce_pb`.`municipio` (`id_municipio`),
  CONSTRAINT `fk_empenho_unidade_gestora`
    FOREIGN KEY (`unidade_gestora_id`)
    REFERENCES `tce_pb`.`unidade_gestora` (`id_unidade_gestora`),
  CONSTRAINT `fk_empenho_obra1`
    FOREIGN KEY (`obra_id`)
    REFERENCES `tce_pb`.`obra` (`id_obra`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_empenho_acao`
    FOREIGN KEY (`acao_id`)
    REFERENCES `tce_pb`.`acao` (`id_acao`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_empenho_funcao1`
    FOREIGN KEY (`funcao_id`)
    REFERENCES `tce_pb`.`funcao` (`id_funcao`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `tce_pb`.`fonte_recurso`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `tce_pb`.`fonte_recurso` (
  `id_fonte_recurso` INT NOT NULL AUTO_INCREMENT,
  `codigo_fonte_recurso` VARCHAR(20) NULL DEFAULT NULL,
  `descricao_fonte_recurso` VARCHAR(255) NULL DEFAULT NULL,
  `ano_fonte` INT NULL DEFAULT NULL,
  PRIMARY KEY (`id_fonte_recurso`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `tce_pb`.`tipo_receita`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `tce_pb`.`tipo_receita` (
  `id_tipo_receita` INT NOT NULL AUTO_INCREMENT,
  `codigo_receita` VARCHAR(20) NULL DEFAULT NULL,
  `descricao_receita` VARCHAR(255) NULL DEFAULT NULL,
  `tipo_atualizacao_receita` VARCHAR(50) NULL DEFAULT NULL,
  PRIMARY KEY (`id_tipo_receita`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `tce_pb`.`receita`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `tce_pb`.`receita` (
  `id_receita` INT NOT NULL AUTO_INCREMENT,
  `municipio_id` INT NOT NULL,
  `unidade_gestora_id` INT NOT NULL,
  `mes_ano` VARCHAR(10) NULL DEFAULT NULL,
  `ano` INT NULL DEFAULT NULL,
  `receita_tipo_id` INT NULL DEFAULT NULL,
  `valor` DECIMAL(15,2) NULL DEFAULT NULL,
  `fonte_recurso_id` INT NULL DEFAULT NULL,
  PRIMARY KEY (`id_receita`),
  INDEX `fk_receita_municipio` (`municipio_id` ASC) VISIBLE,
  INDEX `fk_receita_unidade_gestora` (`unidade_gestora_id` ASC) VISIBLE,
  INDEX `fk_receita_tipo` (`receita_tipo_id` ASC) VISIBLE,
  INDEX `fk_receita_fonte_recurso` (`fonte_recurso_id` ASC) VISIBLE,
  CONSTRAINT `fk_receita_fonte_recurso`
    FOREIGN KEY (`fonte_recurso_id`)
    REFERENCES `tce_pb`.`fonte_recurso` (`id_fonte_recurso`),
  CONSTRAINT `fk_receita_municipio`
    FOREIGN KEY (`municipio_id`)
    REFERENCES `tce_pb`.`municipio` (`id_municipio`),
  CONSTRAINT `fk_receita_tipo`
    FOREIGN KEY (`receita_tipo_id`)
    REFERENCES `tce_pb`.`tipo_receita` (`id_tipo_receita`),
  CONSTRAINT `fk_receita_unidade_gestora`
    FOREIGN KEY (`unidade_gestora_id`)
    REFERENCES `tce_pb`.`unidade_gestora` (`id_unidade_gestora`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `tce_pb`.`unidade_orcamentaria`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `tce_pb`.`unidade_orcamentaria` (
  `id_unidade_orcamentaria` INT NOT NULL AUTO_INCREMENT,
  `codigo_unidade_orcamentaria` VARCHAR(20) NULL DEFAULT NULL,
  `descricao_unidade_orcamentaria` VARCHAR(255) NULL DEFAULT NULL,
  PRIMARY KEY (`id_unidade_orcamentaria`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `tce_pb`.`empenho_has_fonte_recurso`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `tce_pb`.`empenho_has_fonte_recurso` (
  `id_empenho` INT NOT NULL,
  `id_fonte_recurso` INT NOT NULL,
  PRIMARY KEY (`id_empenho`, `id_fonte_recurso`),
  INDEX `fk_empenho_has_fonte_recurso_fonte_recurso1_idx` (`id_fonte_recurso` ASC) VISIBLE,
  INDEX `fk_empenho_has_fonte_recurso_empenho1_idx` (`id_empenho` ASC) VISIBLE,
  CONSTRAINT `fk_empenho_has_fonte_recurso_empenho1`
    FOREIGN KEY (`id_empenho`)
    REFERENCES `tce_pb`.`empenho` (`id_empenho`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_empenho_has_fonte_recurso_fonte_recurso1`
    FOREIGN KEY (`id_fonte_recurso`)
    REFERENCES `tce_pb`.`fonte_recurso` (`id_fonte_recurso`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `tce_pb`.`empenho_has_unidade_orcamentaria`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `tce_pb`.`empenho_has_unidade_orcamentaria` (
  `id_empenho` INT NOT NULL,
  `id_unidade_orcamentaria` INT NOT NULL,
  PRIMARY KEY (`id_empenho`, `id_unidade_orcamentaria`),
  INDEX `fk_empenho_has_unidade_orcamentaria_unidade_orcamentaria1_idx` (`id_unidade_orcamentaria` ASC) VISIBLE,
  INDEX `fk_empenho_has_unidade_orcamentaria_empenho1_idx` (`id_empenho` ASC) VISIBLE,
  CONSTRAINT `fk_empenho_has_unidade_orcamentaria_empenho1`
    FOREIGN KEY (`id_empenho`)
    REFERENCES `tce_pb`.`empenho` (`id_empenho`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_empenho_has_unidade_orcamentaria_unidade_orcamentaria1`
    FOREIGN KEY (`id_unidade_orcamentaria`)
    REFERENCES `tce_pb`.`unidade_orcamentaria` (`id_unidade_orcamentaria`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
