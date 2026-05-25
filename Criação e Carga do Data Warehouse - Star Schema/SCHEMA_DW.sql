-- =============================================================================
-- DATA WAREHOUSE - TCE-PB - STAR SCHEMA
-- =============================================================================
-- Schema alvo : tce_pb_dw
-- Schema fonte: tce_pb (OLTP relacional, ja carregado pelo etl_tce_pb.py)
-- Modelagem   : Star Schema (1 fato + 7 dimensoes)
--
--   Dimensoes:
--     1. dim_tempo                      (calendario)
--     2. dim_municipio
--     3. dim_estrutura_administrativa   (UG + UO denormalizadas)
--     4. dim_fornecedor                 (com tipo_pessoa derivado: PF/PJ/ND)
--     5. dim_programa_acao              (Programa + Acao denormalizadas)
--     6. dim_fonte_recurso
--     7. dim_licitacao                  (com modalidade, objeto, homologacao)
--
--   Fato:
--     fato_empenho   (grao: 1 linha por empenho)
--        Degenerate dimensions: numero_empenho, numero_obra
--        Medidas: valor_empenhado, valor_liquidado, valor_pago, saldo_a_pagar
--
--   Sentinel rows (sk = -1): "NAO INFORMADO" / "SEM LICITACAO"
-- =============================================================================

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------------------------------
-- Schema tce_pb_dw
-- -----------------------------------------------------------------------------
DROP SCHEMA IF EXISTS `tce_pb_dw`;
CREATE SCHEMA IF NOT EXISTS `tce_pb_dw`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;
USE `tce_pb_dw`;

-- =============================================================================
-- DIMENSOES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. dim_tempo  (sk_tempo = YYYYMMDD)
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `tce_pb_dw`.`dim_tempo`;
CREATE TABLE IF NOT EXISTS `tce_pb_dw`.`dim_tempo` (
  `sk_tempo`         INT          NOT NULL COMMENT 'Surrogate key formato YYYYMMDD',
  `data`             DATE         NOT NULL,
  `ano`              SMALLINT     NOT NULL,
  `mes`              TINYINT      NOT NULL,
  `nome_mes`         VARCHAR(15)  NOT NULL,
  `trimestre`        TINYINT      NOT NULL,
  `nome_trimestre`   VARCHAR(5)   NOT NULL,
  `semestre`         TINYINT      NOT NULL,
  `dia`              TINYINT      NOT NULL,
  `dia_semana`       TINYINT      NOT NULL COMMENT '1=Segunda, 7=Domingo',
  `nome_dia_semana`  VARCHAR(15)  NOT NULL,
  `eh_fim_semana`    BOOLEAN      NOT NULL DEFAULT FALSE,
  PRIMARY KEY (`sk_tempo`),
  UNIQUE KEY `uk_data` (`data`)
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

-- -----------------------------------------------------------------------------
-- 2. dim_municipio
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `tce_pb_dw`.`dim_municipio`;
CREATE TABLE IF NOT EXISTS `tce_pb_dw`.`dim_municipio` (
  `sk_municipio`    INT           NOT NULL AUTO_INCREMENT,
  `nome_municipio`  VARCHAR(150)  NOT NULL,
  PRIMARY KEY (`sk_municipio`),
  UNIQUE KEY `uk_nome_municipio` (`nome_municipio`)
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

-- -----------------------------------------------------------------------------
-- 3. dim_estrutura_administrativa  (UG + UO denormalizadas)
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `tce_pb_dw`.`dim_estrutura_administrativa`;
CREATE TABLE IF NOT EXISTS `tce_pb_dw`.`dim_estrutura_administrativa` (
  `sk_estrutura_admin`             INT           NOT NULL AUTO_INCREMENT,
  `codigo_unidade_gestora`         VARCHAR(20),
  `descricao_unidade_gestora`      VARCHAR(255),
  `codigo_unidade_orcamentaria`    VARCHAR(20),
  `descricao_unidade_orcamentaria` VARCHAR(255),
  PRIMARY KEY (`sk_estrutura_admin`),
  UNIQUE KEY `uk_ug_uo` (`codigo_unidade_gestora`, `codigo_unidade_orcamentaria`)
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

-- -----------------------------------------------------------------------------
-- 4. dim_fornecedor
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `tce_pb_dw`.`dim_fornecedor`;
CREATE TABLE IF NOT EXISTS `tce_pb_dw`.`dim_fornecedor` (
  `sk_fornecedor`  INT           NOT NULL AUTO_INCREMENT,
  `cpf_cnpj`       VARCHAR(20),
  `nome`           VARCHAR(255)  NOT NULL,
  `tipo_pessoa`    CHAR(2)       NOT NULL DEFAULT 'ND' COMMENT 'PF=Fisica, PJ=Juridica, ND=Nao Definido',
  PRIMARY KEY (`sk_fornecedor`),
  UNIQUE KEY `uk_cpf_cnpj` (`cpf_cnpj`)
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

-- -----------------------------------------------------------------------------
-- 5. dim_programa_acao  (Programa + Acao denormalizadas)
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `tce_pb_dw`.`dim_programa_acao`;
CREATE TABLE IF NOT EXISTS `tce_pb_dw`.`dim_programa_acao` (
  `sk_programa_acao`     INT           NOT NULL AUTO_INCREMENT,
  `codigo_programa`      VARCHAR(20),
  `descricao_programa`   VARCHAR(255),
  `codigo_acao`          VARCHAR(20),
  `descricao_acao`       VARCHAR(255),
  PRIMARY KEY (`sk_programa_acao`),
  UNIQUE KEY `uk_prog_acao` (`codigo_programa`, `codigo_acao`)
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

-- -----------------------------------------------------------------------------
-- 6. dim_fonte_recurso
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `tce_pb_dw`.`dim_fonte_recurso`;
CREATE TABLE IF NOT EXISTS `tce_pb_dw`.`dim_fonte_recurso` (
  `sk_fonte_recurso`         INT           NOT NULL AUTO_INCREMENT,
  `codigo_fonte_recurso`     VARCHAR(20),
  `descricao_fonte_recurso`  VARCHAR(255),
  `ano_fonte`                VARCHAR(10),
  PRIMARY KEY (`sk_fonte_recurso`),
  UNIQUE KEY `uk_fonte_ano` (`codigo_fonte_recurso`, `ano_fonte`)
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

-- -----------------------------------------------------------------------------
-- 7. dim_licitacao  (com modalidade, objeto, homologacao)
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `tce_pb_dw`.`dim_licitacao`;
CREATE TABLE IF NOT EXISTS `tce_pb_dw`.`dim_licitacao` (
  `sk_licitacao`           INT           NOT NULL AUTO_INCREMENT,
  `numero_licitacao`       VARCHAR(50),
  `numero_protocolo_tce`   VARCHAR(50),
  `ano_licitacao`          SMALLINT,
  `modalidade`             VARCHAR(100)  NOT NULL DEFAULT 'NAO INFORMADO',
  `objeto_licitacao`       TEXT,
  `data_homologacao`       DATE,
  PRIMARY KEY (`sk_licitacao`),
  UNIQUE KEY `uk_licitacao` (`numero_licitacao`, `numero_protocolo_tce`)
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

-- =============================================================================
-- FATO
-- =============================================================================

-- -----------------------------------------------------------------------------
-- fato_empenho
--   Grao: 1 linha por empenho
--   Degenerate dimensions: numero_empenho, numero_obra
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `tce_pb_dw`.`fato_empenho`;
CREATE TABLE IF NOT EXISTS `tce_pb_dw`.`fato_empenho` (
  `id_fato_empenho`      BIGINT         NOT NULL AUTO_INCREMENT,

  -- Foreign keys para as 7 dimensoes (sk = -1 quando NAO INFORMADO)
  `sk_tempo`             INT            NOT NULL,
  `sk_municipio`         INT            NOT NULL,
  `sk_estrutura_admin`   INT            NOT NULL,
  `sk_fornecedor`        INT            NOT NULL,
  `sk_programa_acao`     INT            NOT NULL,
  `sk_fonte_recurso`     INT            NOT NULL,
  `sk_licitacao`         INT            NOT NULL,

  -- Degenerate dimensions (ficam no fato sem tabela propria)
  `numero_empenho`       VARCHAR(50)             COMMENT 'Degenerate Dimension',
  `numero_obra`          VARCHAR(100)            COMMENT 'Degenerate Dimension',

  -- Medidas
  `valor_empenhado`      DECIMAL(15,2)  NOT NULL DEFAULT 0,
  `valor_liquidado`      DECIMAL(15,2)  NOT NULL DEFAULT 0,
  `valor_pago`           DECIMAL(15,2)  NOT NULL DEFAULT 0,
  `saldo_a_pagar`        DECIMAL(15,2)  NOT NULL DEFAULT 0 COMMENT 'Calculada: empenhado - pago',

  PRIMARY KEY (`id_fato_empenho`),

  INDEX `idx_fato_tempo`        (`sk_tempo`),
  INDEX `idx_fato_municipio`    (`sk_municipio`),
  INDEX `idx_fato_estrutura`    (`sk_estrutura_admin`),
  INDEX `idx_fato_fornecedor`   (`sk_fornecedor`),
  INDEX `idx_fato_prog_acao`    (`sk_programa_acao`),
  INDEX `idx_fato_fonte`        (`sk_fonte_recurso`),
  INDEX `idx_fato_licitacao`    (`sk_licitacao`),

  CONSTRAINT `fk_fato_tempo`
    FOREIGN KEY (`sk_tempo`)        REFERENCES `tce_pb_dw`.`dim_tempo`                    (`sk_tempo`),
  CONSTRAINT `fk_fato_municipio`
    FOREIGN KEY (`sk_municipio`)    REFERENCES `tce_pb_dw`.`dim_municipio`                (`sk_municipio`),
  CONSTRAINT `fk_fato_estrutura`
    FOREIGN KEY (`sk_estrutura_admin`) REFERENCES `tce_pb_dw`.`dim_estrutura_administrativa` (`sk_estrutura_admin`),
  CONSTRAINT `fk_fato_fornecedor`
    FOREIGN KEY (`sk_fornecedor`)   REFERENCES `tce_pb_dw`.`dim_fornecedor`               (`sk_fornecedor`),
  CONSTRAINT `fk_fato_prog_acao`
    FOREIGN KEY (`sk_programa_acao`) REFERENCES `tce_pb_dw`.`dim_programa_acao`            (`sk_programa_acao`),
  CONSTRAINT `fk_fato_fonte`
    FOREIGN KEY (`sk_fonte_recurso`) REFERENCES `tce_pb_dw`.`dim_fonte_recurso`            (`sk_fonte_recurso`),
  CONSTRAINT `fk_fato_licitacao`
    FOREIGN KEY (`sk_licitacao`)    REFERENCES `tce_pb_dw`.`dim_licitacao`                (`sk_licitacao`)
) ENGINE = InnoDB DEFAULT CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

-- =============================================================================
-- SENTINEL ROWS (sk = -1)
--   Pattern Kimball: evita NULL em FK, garante integridade referencial.
-- =============================================================================
INSERT INTO `tce_pb_dw`.`dim_tempo`
  (sk_tempo, data, ano, mes, nome_mes, trimestre, nome_trimestre, semestre,
   dia, dia_semana, nome_dia_semana, eh_fim_semana)
VALUES
  (-1, '1900-01-01', 1900, 1, 'NAO INFORMADO', 1, 'T1', 1, 1, 1, 'NAO INFORMADO', FALSE);

INSERT INTO `tce_pb_dw`.`dim_municipio` (sk_municipio, nome_municipio)
VALUES (-1, 'NAO INFORMADO');

INSERT INTO `tce_pb_dw`.`dim_estrutura_administrativa`
  (sk_estrutura_admin, codigo_unidade_gestora, descricao_unidade_gestora,
   codigo_unidade_orcamentaria, descricao_unidade_orcamentaria)
VALUES
  (-1, 'ND', 'NAO INFORMADO', 'ND', 'NAO INFORMADO');

INSERT INTO `tce_pb_dw`.`dim_fornecedor` (sk_fornecedor, cpf_cnpj, nome, tipo_pessoa)
VALUES (-1, '00000000000', 'NAO INFORMADO', 'ND');

INSERT INTO `tce_pb_dw`.`dim_programa_acao`
  (sk_programa_acao, codigo_programa, descricao_programa, codigo_acao, descricao_acao)
VALUES
  (-1, 'ND', 'NAO INFORMADO', 'ND', 'NAO INFORMADO');

INSERT INTO `tce_pb_dw`.`dim_fonte_recurso`
  (sk_fonte_recurso, codigo_fonte_recurso, descricao_fonte_recurso, ano_fonte)
VALUES
  (-1, 'ND', 'NAO INFORMADO', 'ND');

INSERT INTO `tce_pb_dw`.`dim_licitacao`
  (sk_licitacao, numero_licitacao, numero_protocolo_tce, ano_licitacao,
   modalidade, objeto_licitacao, data_homologacao)
VALUES
  (-1, 'SEM LICITACAO', 'SEM LICITACAO', NULL, 'SEM LICITACAO', NULL, NULL);

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
