"""
ETL TCE-PB -> Data Warehouse (Star Schema)
==========================================
Carrega o DW dimensional (schema `tce_pb_dw`) a partir do OLTP relacional
(schema `tce_pb`) que ja foi populado pelo `etl_tce_pb.py`.

Modelo dimensional conforme SCHEMA_DW_REVISION.sql:
  - 1 Fato:       fato_empenho agregada por combinacao das SKs
  - 6 Dimensoes:  dim_tempo, dim_estrutura_administrativa, dim_fornecedor,
                  dim_programa_acao, dim_fonte_recurso, dim_licitacao

Pre-requisitos:
  1. SCHEMA_DW_REVISION.sql executado
  2. `tce_pb` populado pelo `etl_tce_pb.py` original
  3. pip install -r requirements.txt
"""

import os
import glob
import logging
import getpass
import argparse
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError

# =============================================================================
# CONFIGURACAO
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

DB_USER = os.getenv("DB_USER", "root")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))

SCHEMA_OLTP = os.getenv("SCHEMA_OLTP", "tce_pb")
SCHEMA_DW = os.getenv("SCHEMA_DW", "tce_pb_dw")

# Janela analitica do DW (usada apenas para gerar dim_tempo)
ANO_INICIO = 2023
ANO_FIM    = 2025

# =============================================================================
# UTILITARIOS
# =============================================================================
def criar_engine_mysql(schema: str, senha: str):
    url = URL.create(
        "mysql+pymysql",
        username=DB_USER,
        password=senha,
        host=DB_HOST,
        port=DB_PORT,
        database=schema,
    )
    return create_engine(url, pool_recycle=3600)


def obter_senha_mysql():
    return os.getenv("DB_PASS") or getpass.getpass("Digite a senha do banco de dados: ")


def padronizar_numero_licitacao(num):
    """Mesma logica do etl_tce_pb.py original. Garante chave consistente entre OLTP e CSV."""
    num = str(num).strip()
    if num in ('0', 'nan', 'None', '', '0.0'):
        return '0'
    num = num.replace('.0', '')
    if '/' in num:
        partes = num.split('/')
        if len(partes) == 2:
            numero = partes[0].zfill(5)
            ano = partes[1]
            return f"{numero}/{ano}"
    else:
        if len(num) >= 5:
            ano = num[-4:]
            numero = num[:-4].zfill(5)
            return f"{numero}/{ano}"
    return num


def truncar_tabelas_dw(engine):
    """Limpa todas as tabelas do DW (incluindo sentinel rows)."""
    tabelas = ['fato_empenho', 'dim_tempo', 'dim_estrutura_administrativa', 'dim_fornecedor',
               'dim_programa_acao', 'dim_fonte_recurso', 'dim_licitacao']

    logging.info("Limpando tabelas do DW...")
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for tabela in tabelas:
            conn.execute(text(f"TRUNCATE TABLE {tabela}"))
            logging.info(f"  TRUNCATE {tabela}")
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))


def inserir_sentinel_rows(engine):
    """Re-insere os registros 'NAO INFORMADO' / 'SEM LICITACAO' (sk = -1)."""
    logging.info("Inserindo sentinel rows (sk = -1)...")
    statements = [
        """INSERT INTO dim_tempo
             (sk_tempo, data, ano, mes, nome_mes, trimestre, nome_trimestre,
              semestre, dia, dia_semana, nome_dia_semana, eh_fim_semana,
              date_from, date_to, version)
           VALUES
             (-1, '1900-01-01', 1900, 1, 'NAO INFORMADO', 1, 'T1', 1, 1, 1, 'NAO INFORMADO', FALSE, NOW(), NULL, 1)""",
        """INSERT INTO dim_estrutura_administrativa
             (sk_estrutura_admin, codigo_unidade_gestora, descricao_unidade_gestora,
              codigo_unidade_orcamentaria, descricao_unidade_orcamentaria,
              nome_municipio, date_from, date_to, version)
           VALUES (-1, 'ND', 'NAO INFORMADO', 'ND', 'NAO INFORMADO', 'NAO INFORMADO', NOW(), NULL, 1)""",
        """INSERT INTO dim_fornecedor
             (sk_fornecedor, cpf_cnpj, nome, tipo_pessoa, date_from, date_to, version)
           VALUES (-1, '00000000000', 'NAO INFORMADO', 'ND', NOW(), NULL, 1)""",
        """INSERT INTO dim_programa_acao
             (sk_programa_acao, codigo_programa, descricao_programa, codigo_acao, descricao_acao,
              date_from, date_to, version)
           VALUES (-1, 'ND', 'NAO INFORMADO', 'ND', 'NAO INFORMADO', NOW(), NULL, 1)""",
        """INSERT INTO dim_fonte_recurso
             (sk_fonte_recurso, codigo_fonte_recurso, descricao_fonte_recurso, ano_fonte,
              date_from, date_to, version)
           VALUES (-1, 'ND', 'NAO INFORMADO', 'ND', NOW(), NULL, 1)""",
        """INSERT INTO dim_licitacao
             (sk_licitacao, numero_licitacao, numero_protocolo_tce, ano_licitacao,
              modalidade, objeto_licitacao, data_homologacao, date_from, date_to, version)
           VALUES (-1, 'SEM LICITACAO', 'SEM LICITACAO', NULL, 'SEM LICITACAO', NULL, NULL, NOW(), NULL, 1)""",
    ]
    with engine.begin() as conn:
        for sql in statements:
            conn.execute(text(sql))

# =============================================================================
# DIM_TEMPO  -- gerador de calendario
# =============================================================================
def gerar_dim_tempo(ano_inicio: int, ano_fim: int) -> pd.DataFrame:
    """Gera tabela de calendario com surrogate key no formato YYYYMMDD."""
    datas = pd.date_range(start=f"{ano_inicio}-01-01", end=f"{ano_fim}-12-31", freq='D')

    nomes_meses = {
        1: 'JANEIRO',  2: 'FEVEREIRO', 3: 'MARCO',    4: 'ABRIL',
        5: 'MAIO',     6: 'JUNHO',     7: 'JULHO',    8: 'AGOSTO',
        9: 'SETEMBRO', 10: 'OUTUBRO',  11: 'NOVEMBRO', 12: 'DEZEMBRO'
    }
    nomes_dias = {
        0: 'SEGUNDA', 1: 'TERCA',  2: 'QUARTA', 3: 'QUINTA',
        4: 'SEXTA',   5: 'SABADO', 6: 'DOMINGO'
    }

    df = pd.DataFrame({'data': datas})
    df['sk_tempo']        = df['data'].dt.strftime('%Y%m%d').astype(int)
    df['ano']             = df['data'].dt.year.astype('int16')
    df['mes']             = df['data'].dt.month.astype('int8')
    df['nome_mes']        = df['mes'].map(nomes_meses)
    df['trimestre']       = df['data'].dt.quarter.astype('int8')
    df['nome_trimestre']  = 'T' + df['trimestre'].astype(str)
    df['semestre']        = ((df['mes'] - 1) // 6 + 1).astype('int8')
    df['dia']             = df['data'].dt.day.astype('int8')
    df['dia_semana']      = (df['data'].dt.dayofweek + 1).astype('int8')  # 1=Seg, 7=Dom
    df['nome_dia_semana'] = df['data'].dt.dayofweek.map(nomes_dias)
    df['eh_fim_semana']   = df['data'].dt.dayofweek.isin([5, 6])
    df['data']            = df['data'].dt.date

    df['date_from'] = pd.Timestamp.now()
    df['date_to'] = None
    df['version'] = 1

    return df[['sk_tempo', 'data', 'ano', 'mes', 'nome_mes', 'trimestre',
               'nome_trimestre', 'semestre', 'dia', 'dia_semana',
               'nome_dia_semana', 'eh_fim_semana', 'date_from', 'date_to',
               'version']]

# =============================================================================
# CARGA DE DIMENSOES
# =============================================================================
def carregar_dim_tempo(engine_dw):
    logging.info("Carregando dim_tempo...")
    df = gerar_dim_tempo(ANO_INICIO, ANO_FIM)
    df.to_sql('dim_tempo', engine_dw, if_exists='append', index=False, chunksize=1000)
    logging.info(f"  {len(df)} datas inseridas em dim_tempo")


def executar_carga_sql(engine_dw, sql: str, descricao: str):
    with engine_dw.begin() as conn:
        resultado = conn.execute(text(sql))
    logging.info(f"  {descricao}: {resultado.rowcount if resultado.rowcount is not None else 'N/D'} linhas inseridas")


def carregar_dim_estrutura_administrativa(engine_dw):
    """Carrega apenas as combinacoes UG x UO que realmente aparecem nos empenhos."""
    logging.info("Carregando dim_estrutura_administrativa (combinacoes UG x UO reais)...")
    sql = f"""
        INSERT INTO {SCHEMA_DW}.dim_estrutura_administrativa (
            codigo_unidade_gestora,
            descricao_unidade_gestora,
            codigo_unidade_orcamentaria,
            descricao_unidade_orcamentaria,
            nome_municipio,
            date_from,
            date_to,
            version
        )
        SELECT
            codigo_unidade_gestora,
            MAX(descricao_unidade_gestora) AS descricao_unidade_gestora,
            codigo_unidade_orcamentaria,
            MAX(descricao_unidade_orcamentaria) AS descricao_unidade_orcamentaria,
            MAX(nome_municipio) AS nome_municipio,
            NOW() AS date_from,
            NULL AS date_to,
            1 AS version
        FROM (
            SELECT DISTINCT
                NULLIF(TRIM(ug.codigo_unidade_gestora), '') AS codigo_unidade_gestora,
                NULLIF(UPPER(TRIM(ug.descricao_unidade_gestora)), '') AS descricao_unidade_gestora,
                NULLIF(TRIM(uo.codigo_unidade_orcamentaria), '') AS codigo_unidade_orcamentaria,
                NULLIF(UPPER(TRIM(uo.descricao_unidade_orcamentaria)), '') AS descricao_unidade_orcamentaria,
                COALESCE(NULLIF(UPPER(TRIM(m.nome_municipio)), ''), 'NAO INFORMADO') AS nome_municipio
        FROM {SCHEMA_OLTP}.empenho e
        JOIN {SCHEMA_OLTP}.unidade_gestora       ug ON e.unidade_gestora_id      = ug.id_unidade_gestora
        JOIN {SCHEMA_OLTP}.unidade_orcamentaria  uo ON e.unidade_orcamentaria_id = uo.id_unidade_orcamentaria
            LEFT JOIN {SCHEMA_OLTP}.municipio m ON e.municipio_id = m.id_municipio
        ) base
        GROUP BY codigo_unidade_gestora, codigo_unidade_orcamentaria
    """
    executar_carga_sql(engine_dw, sql, "combinacoes UG x UO")


def carregar_dim_fornecedor(engine_dw):
    """Carrega fornecedores derivando o atributo tipo_pessoa (PF/PJ/ND)."""
    logging.info("Carregando dim_fornecedor (com derivacao de tipo_pessoa)...")
    sql = f"""
        INSERT INTO {SCHEMA_DW}.dim_fornecedor (cpf_cnpj, nome, tipo_pessoa, date_from, date_to, version)
        SELECT
            cpf_cnpj,
            MAX(nome) AS nome,
            CASE
                WHEN LENGTH(REGEXP_REPLACE(cpf_cnpj, '[^0-9]', '')) = 11 THEN 'PF'
                WHEN LENGTH(REGEXP_REPLACE(cpf_cnpj, '[^0-9]', '')) = 14 THEN 'PJ'
                ELSE 'ND'
            END AS tipo_pessoa,
            NOW() AS date_from,
            NULL AS date_to,
            1 AS version
        FROM (
            SELECT
                NULLIF(TRIM(cpf_cnpj), '') AS cpf_cnpj,
                NULLIF(UPPER(TRIM(nome)), '') AS nome
            FROM {SCHEMA_OLTP}.fornecedor
        ) f
        WHERE cpf_cnpj IS NOT NULL
          AND nome IS NOT NULL
        GROUP BY cpf_cnpj
    """
    executar_carga_sql(engine_dw, sql, "fornecedores")


def carregar_dim_programa_acao(engine_dw):
    logging.info("Carregando dim_programa_acao (denormalizada)...")
    sql = f"""
        INSERT INTO {SCHEMA_DW}.dim_programa_acao (
            codigo_programa,
            descricao_programa,
            codigo_acao,
            descricao_acao,
            date_from,
            date_to,
            version
        )
        SELECT
            codigo_programa,
            MAX(descricao_programa) AS descricao_programa,
            codigo_acao,
            MAX(descricao_acao) AS descricao_acao,
            NOW() AS date_from,
            NULL AS date_to,
            1 AS version
        FROM (
            SELECT
                NULLIF(TRIM(p.codigo_programa), '') AS codigo_programa,
                NULLIF(UPPER(TRIM(p.descricao_programa)), '') AS descricao_programa,
                NULLIF(TRIM(a.codigo_acao), '') AS codigo_acao,
                NULLIF(UPPER(TRIM(a.descricao_acao)), '') AS descricao_acao
            FROM {SCHEMA_OLTP}.acao a
            LEFT JOIN {SCHEMA_OLTP}.programa p ON a.programa_id = p.id_programa
            WHERE a.codigo_acao IS NOT NULL
               OR a.descricao_acao IS NOT NULL
        ) base
        WHERE codigo_programa IS NOT NULL
           OR codigo_acao IS NOT NULL
        GROUP BY codigo_programa, codigo_acao
    """
    executar_carga_sql(engine_dw, sql, "combinacoes Programa x Acao")


def carregar_dim_fonte_recurso(engine_dw):
    logging.info("Carregando dim_fonte_recurso...")
    sql = f"""
        INSERT INTO {SCHEMA_DW}.dim_fonte_recurso (
            codigo_fonte_recurso,
            descricao_fonte_recurso,
            ano_fonte,
            date_from,
            date_to,
            version
        )
        SELECT
            codigo_fonte_recurso,
            MAX(descricao_fonte_recurso) AS descricao_fonte_recurso,
            ano_fonte,
            NOW() AS date_from,
            NULL AS date_to,
            1 AS version
        FROM (
            SELECT
                NULLIF(TRIM(codigo_fonte_recurso), '') AS codigo_fonte_recurso,
                NULLIF(UPPER(TRIM(descricao_fonte_recurso)), '') AS descricao_fonte_recurso,
                NULLIF(TRIM(ano_fonte), '') AS ano_fonte
            FROM {SCHEMA_OLTP}.fonte_recurso
        ) base
        WHERE codigo_fonte_recurso IS NOT NULL
        GROUP BY codigo_fonte_recurso, ano_fonte
    """
    executar_carga_sql(engine_dw, sql, "fontes de recurso")


def carregar_dim_licitacao(engine_dw):
    """
    Carrega licitacoes do OLTP. O OLTP nao guardou a coluna `modalidade`, entao
    ela fica como 'NAO INFORMADO' (default). Use enriquecer_dim_licitacao_via_csv()
    se quiser popular modalidade lendo os arquivos licitacoes-*.csv.
    """
    logging.info("Carregando dim_licitacao...")
    sql = f"""
        INSERT INTO {SCHEMA_DW}.dim_licitacao (
            numero_licitacao,
            numero_protocolo_tce,
            ano_licitacao,
            objeto_licitacao,
            data_homologacao,
            date_from,
            date_to,
            version
        )
        SELECT
            numero_licitacao,
            numero_protocolo_tce,
            MAX(CAST(ano_licitacao AS UNSIGNED)) AS ano_licitacao,
            MAX(objeto_licitacao) AS objeto_licitacao,
            MAX(data_homologacao) AS data_homologacao,
            NOW() AS date_from,
            NULL AS date_to,
            1 AS version
        FROM (
            SELECT
                NULLIF(TRIM(numero_licitacao), '') AS numero_licitacao,
                NULLIF(TRIM(numero_protocolo_tce), '') AS numero_protocolo_tce,
                objeto_licitacao,
                data_homologacao,
                ano_licitacao
            FROM {SCHEMA_OLTP}.licitacao
        ) l
        WHERE numero_licitacao IS NOT NULL
           OR numero_protocolo_tce IS NOT NULL
        GROUP BY numero_licitacao, numero_protocolo_tce
    """
    executar_carga_sql(engine_dw, sql, "licitacoes")


def enriquecer_dim_licitacao_via_csv(engine_dw, diretorio_csv: str):
    """
    Opcional: le os CSVs licitacoes-*.csv e popula a coluna `modalidade` em
    dim_licitacao via UPDATE. Util porque o OLTP atual nao guardou essa coluna.
    """
    logging.info(f"Enriquecendo dim_licitacao.modalidade a partir dos CSVs em '{diretorio_csv}'...")
    arquivos = sorted(glob.glob(os.path.join(diretorio_csv, "licitacoes-*.csv")))
    if not arquivos:
        logging.warning(f"  Nenhum arquivo licitacoes-*.csv encontrado em '{diretorio_csv}'. Pulando.")
        return

    dfs = []
    for arq in arquivos:
        try:
            df = pd.read_csv(arq, sep=';', encoding='utf-8',
                             usecols=['numero_licitacao', 'numero_protocolo_tce', 'modalidade'],
                             low_memory=False)
        except UnicodeDecodeError:
            df = pd.read_csv(arq, sep=';', encoding='latin1',
                             usecols=['numero_licitacao', 'numero_protocolo_tce', 'modalidade'],
                             low_memory=False)
        dfs.append(df)
        logging.info(f"  Lido: {arq} ({len(df)} linhas)")

    df_mod = pd.concat(dfs, ignore_index=True).dropna(subset=['numero_licitacao', 'numero_protocolo_tce', 'modalidade'])
    df_mod['numero_licitacao'] = df_mod['numero_licitacao'].apply(padronizar_numero_licitacao)
    df_mod = df_mod.drop_duplicates(subset=['numero_licitacao', 'numero_protocolo_tce'])

    logging.info(f"  {len(df_mod)} pares unicos (licitacao, protocolo) com modalidade.")

    df_mod.to_sql('_tmp_modalidade', engine_dw, if_exists='replace', index=False, chunksize=5000)
    with engine_dw.begin() as conn:
        conn.execute(text("""
            UPDATE dim_licitacao dl
            JOIN _tmp_modalidade tmp
              ON dl.numero_licitacao      = tmp.numero_licitacao
             AND dl.numero_protocolo_tce  = tmp.numero_protocolo_tce
            SET dl.modalidade = tmp.modalidade
        """))
        conn.execute(text("DROP TABLE _tmp_modalidade"))
    logging.info("  dim_licitacao.modalidade enriquecida com sucesso.")

# =============================================================================
# CARGA DO FATO (INSERT INTO ... SELECT JOIN, executado dentro do MySQL)
# =============================================================================
def carregar_fato_empenho(engine_dw):
    """
    Carrega fato_empenho agregada por combinacao de SKs, conforme
    SCHEMA_DW_REVISION.sql. O grao deixa de ser 1 linha por empenho e passa a
    ser 1 linha por combinacao:
    tempo x estrutura x fornecedor x programa/acao x fonte x licitacao.
    """
    logging.info("Carregando fato_empenho via INSERT INTO ... SELECT JOIN...")
    logging.info("  (Esta etapa pode demorar varios minutos para milhoes de empenhos)")

    sql = f"""
    INSERT INTO {SCHEMA_DW}.fato_empenho (
        sk_tempo, sk_estrutura_admin, sk_fornecedor,
        sk_programa_acao, sk_fonte_recurso, sk_licitacao,
        valor_empenhado, valor_liquidado, valor_pago, saldo_a_pagar
    )
    SELECT
        sk_tempo,
        sk_estrutura_admin,
        sk_fornecedor,
        sk_programa_acao,
        sk_fonte_recurso,
        sk_licitacao,
        SUM(valor_empenhado) AS valor_empenhado,
        SUM(valor_liquidado) AS valor_liquidado,
        SUM(valor_pago) AS valor_pago,
        SUM(valor_empenhado) - SUM(valor_pago) AS saldo_a_pagar
    FROM (
        SELECT
            COALESCE(dt.sk_tempo, -1)            AS sk_tempo,
            COALESCE(de.sk_estrutura_admin, -1)  AS sk_estrutura_admin,
            COALESCE(dfo.sk_fornecedor, -1)      AS sk_fornecedor,
            COALESCE(dpa.sk_programa_acao, -1)   AS sk_programa_acao,
            COALESCE(dfr.sk_fonte_recurso, -1)   AS sk_fonte_recurso,
            COALESCE(dl.sk_licitacao, -1)        AS sk_licitacao,
            COALESCE(e.valor_empenhado, 0)       AS valor_empenhado,
            COALESCE(e.valor_liquidado, 0)       AS valor_liquidado,
            COALESCE(e.valor_pago, 0)            AS valor_pago
    FROM       {SCHEMA_OLTP}.empenho                        e
    LEFT JOIN  {SCHEMA_DW}.dim_tempo                        dt
            ON dt.data = e.data_empenho
    LEFT JOIN  {SCHEMA_OLTP}.unidade_gestora                ug
            ON e.unidade_gestora_id = ug.id_unidade_gestora
    LEFT JOIN  {SCHEMA_OLTP}.unidade_orcamentaria           uo
            ON e.unidade_orcamentaria_id = uo.id_unidade_orcamentaria
    LEFT JOIN  {SCHEMA_DW}.dim_estrutura_administrativa     de
            ON de.codigo_unidade_gestora      <=> NULLIF(TRIM(ug.codigo_unidade_gestora), '')
           AND de.codigo_unidade_orcamentaria <=> NULLIF(TRIM(uo.codigo_unidade_orcamentaria), '')
    LEFT JOIN  {SCHEMA_OLTP}.fornecedor                     f
            ON e.credor_id = f.id_fornecedor
    LEFT JOIN  {SCHEMA_DW}.dim_fornecedor                   dfo
            ON dfo.cpf_cnpj = NULLIF(TRIM(f.cpf_cnpj), '')
    LEFT JOIN  {SCHEMA_OLTP}.acao                           a
            ON e.acao_id = a.id_acao
    LEFT JOIN  {SCHEMA_OLTP}.programa                       p
            ON a.programa_id = p.id_programa
    LEFT JOIN  {SCHEMA_DW}.dim_programa_acao                dpa
            ON dpa.codigo_programa <=> NULLIF(TRIM(p.codigo_programa), '')
           AND dpa.codigo_acao     <=> NULLIF(TRIM(a.codigo_acao), '')
    LEFT JOIN  {SCHEMA_OLTP}.fonte_recurso                  fr
            ON e.fonte_recurso_id = fr.id_fonte_recurso
    LEFT JOIN  {SCHEMA_DW}.dim_fonte_recurso                dfr
            ON dfr.codigo_fonte_recurso <=> NULLIF(TRIM(fr.codigo_fonte_recurso), '')
           AND dfr.ano_fonte            <=> NULLIF(TRIM(fr.ano_fonte), '')
    LEFT JOIN  {SCHEMA_OLTP}.licitacao                      l
            ON e.licitacao_id = l.id_licitacao
    LEFT JOIN  {SCHEMA_DW}.dim_licitacao                    dl
            ON dl.numero_licitacao     <=> NULLIF(TRIM(l.numero_licitacao), '')
           AND dl.numero_protocolo_tce <=> NULLIF(TRIM(l.numero_protocolo_tce), '')
    ) base
    GROUP BY
        sk_tempo,
        sk_estrutura_admin,
        sk_fornecedor,
        sk_programa_acao,
        sk_fonte_recurso,
        sk_licitacao
    """

    with engine_dw.begin() as conn:
        resultado = conn.execute(text(sql))
    logging.info(f"  fato_empenho carregada: {resultado.rowcount if resultado.rowcount is not None else 'N/D'} linhas inseridas")


def validar_origem(engine_dw):
    logging.info("Validando schemas de origem e destino...")
    tabelas_oltp = [
        'municipio', 'unidade_gestora', 'licitacao', 'obra', 'programa',
        'acao', 'fonte_recurso', 'unidade_orcamentaria', 'fornecedor', 'empenho'
    ]
    tabelas_dw = [
        'dim_tempo', 'dim_estrutura_administrativa',
        'dim_fornecedor', 'dim_programa_acao', 'dim_fonte_recurso',
        'dim_licitacao', 'fato_empenho'
    ]
    sql = """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = :schema
          AND table_name = :tabela
    """
    with engine_dw.connect() as conn:
        ausentes = []
        for tabela in tabelas_oltp:
            existe = conn.execute(text(sql), {"schema": SCHEMA_OLTP, "tabela": tabela}).scalar()
            if not existe:
                ausentes.append(f"{SCHEMA_OLTP}.{tabela}")
        for tabela in tabelas_dw:
            existe = conn.execute(text(sql), {"schema": SCHEMA_DW, "tabela": tabela}).scalar()
            if not existe:
                ausentes.append(f"{SCHEMA_DW}.{tabela}")
        if ausentes:
            raise RuntimeError("Tabelas ausentes: " + ", ".join(ausentes))

        total_empenhos = conn.execute(text(f"SELECT COUNT(*) FROM {SCHEMA_OLTP}.empenho")).scalar()
        if not total_empenhos:
            raise RuntimeError(f"O schema {SCHEMA_OLTP} nao possui empenhos carregados.")
    logging.info("  schemas validados.")

# =============================================================================
# VALIDACAO
# =============================================================================
def imprimir_resumo(engine_dw):
    logging.info("=" * 70)
    logging.info("RESUMO DA CARGA DO DW")
    logging.info("=" * 70)

    tabelas = ['dim_tempo', 'dim_estrutura_administrativa',
               'dim_fornecedor', 'dim_programa_acao', 'dim_fonte_recurso',
               'dim_licitacao', 'fato_empenho']

    with engine_dw.connect() as conn:
        for tabela in tabelas:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {tabela}")).scalar()
            logging.info(f"  {tabela:.<42} {count:>15,} linhas")

        logging.info("-" * 70)
        row = conn.execute(text("""
            SELECT
              SUM(sk_tempo            = -1) AS sem_data,
              SUM(sk_estrutura_admin  = -1) AS sem_estrutura,
              SUM(sk_fornecedor       = -1) AS sem_fornecedor,
              SUM(sk_programa_acao    = -1) AS sem_prog_acao,
              SUM(sk_fonte_recurso    = -1) AS sem_fonte,
              SUM(sk_licitacao        = -1) AS sem_licitacao
            FROM fato_empenho
        """)).first()

        if row:
            logging.info("Registros do fato com FK = -1 (NAO INFORMADO/SEM LICITACAO):")
            logging.info(f"  sem data:        {int(row[0] or 0):>15,}")
            logging.info(f"  sem estrutura:   {int(row[1] or 0):>15,}")
            logging.info(f"  sem fornecedor:  {int(row[2] or 0):>15,}")
            logging.info(f"  sem prog/acao:   {int(row[3] or 0):>15,}")
            logging.info(f"  sem fonte:       {int(row[4] or 0):>15,}")
            logging.info(f"  sem licitacao:   {int(row[5] or 0):>15,}  (esperado: dispensas/inexigibilidades)")

        total = conn.execute(text("SELECT SUM(valor_empenhado) FROM fato_empenho")).scalar()
        logging.info("-" * 70)
        logging.info(f"  VALOR TOTAL EMPENHADO: R$ {float(total or 0):,.2f}")
        logging.info("=" * 70)

# =============================================================================
# ORQUESTRACAO
# =============================================================================
def executar_pipeline(enriquecer_modalidade: bool = False, diretorio_csv: str = None):
    logging.info("=== INICIANDO ETL: tce_pb (OLTP) -> tce_pb_dw (Star Schema) ===")

    try:
        senha = obter_senha_mysql()
        engine_dw = criar_engine_mysql(SCHEMA_DW, senha)
        with engine_dw.connect() as conn:
            conn.execute(text("SELECT 1"))
        logging.info("Conexao MySQL estabelecida.")
        validar_origem(engine_dw)
    except SQLAlchemyError as e:
        logging.critical(f"Falha ao conectar nos bancos: {e}")
        return
    except RuntimeError as e:
        logging.critical(f"Falha de validacao: {e}")
        return

    # 1. Limpar e re-inserir sentinel rows
    truncar_tabelas_dw(engine_dw)
    inserir_sentinel_rows(engine_dw)

    # 2. Dimensoes
    carregar_dim_tempo(engine_dw)
    carregar_dim_estrutura_administrativa(engine_dw)
    carregar_dim_fornecedor(engine_dw)
    carregar_dim_programa_acao(engine_dw)
    carregar_dim_fonte_recurso(engine_dw)
    carregar_dim_licitacao(engine_dw)

    # 3. (Opcional) Enriquecer modalidade lendo CSVs
    if enriquecer_modalidade and diretorio_csv:
        enriquecer_dim_licitacao_via_csv(engine_dw, diretorio_csv)

    # 4. Fato (operacao pesada — JOIN cross-schema dentro do MySQL)
    carregar_fato_empenho(engine_dw)

    # 5. Resumo
    imprimir_resumo(engine_dw)

    logging.info("=== ETL DW FINALIZADO COM SUCESSO ===")

# =============================================================================
# MAIN
# =============================================================================
def parse_args():
    parser = argparse.ArgumentParser(
        description="Carrega o Data Warehouse tce_pb_dw a partir do schema relacional tce_pb."
    )
    parser.add_argument(
        "--enriquecer-modalidade",
        action="store_true",
        help="Atualiza dim_licitacao.modalidade lendo arquivos licitacoes-*.csv.",
    )
    parser.add_argument(
        "--dir-csv",
        default="../cargas",
        help="Diretorio dos CSVs de licitacoes usado com --enriquecer-modalidade.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    enriquecer = args.enriquecer_modalidade
    diretorio_csv = args.dir_csv

    if enriquecer and not os.path.isdir(diretorio_csv):
        logging.warning(f"Diretorio '{diretorio_csv}' nao existe -- pulando enriquecimento.")
        enriquecer = False

    executar_pipeline(enriquecer_modalidade=enriquecer, diretorio_csv=diretorio_csv)
