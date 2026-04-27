import os
import glob
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# ==============================================================================
# CONFIGURAÇÕES E CONSTANTES
# ==============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "senha") # Substitua "senha" pela senha real do seu banco de dados
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "tce_pb")

DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
DATA_DIR = os.curdir

ANOS = [2023, 2024, 2025]

# ==============================================================================
# FUNÇÕES DE TRATAMENTO DE DADOS ESPECÍFICOS
# ==============================================================================
def padronizar_numero_licitacao(num):
    """
    Padroniza os formatos de licitação para XXXXX/AAAA.
    Ex: '92025' -> '00009/2025' | '00002/2025' -> '00002/2025' | '0' -> '0'
    """
    num = str(num).strip()
    
    # Valores nulos ou zero
    if num in ('0', 'nan', 'None', '', '0.0'):
        return '0'

    # Remove o ".0" caso o Pandas tenha lido como float
    num = num.replace('.0', '')

    # Se já tem barra (Ex: "2/2025" ou "00002/2025")
    if '/' in num:
        partes = num.split('/')
        if len(partes) == 2:
            numero = partes[0].zfill(5)  # Completa com zeros à esquerda até 5 posições
            ano = partes[1]
            return f"{numero}/{ano}"
            
    # Se não tem barra (Ex: "92025")
    else:
        # Pega os últimos 4 dígitos como ano, e o que sobrar vira o número
        if len(num) >= 5:
            ano = num[-4:]
            numero = num[:-4].zfill(5)
            return f"{numero}/{ano}"

    return num

# ==============================================================================
# FUNÇÕES DE EXTRAÇÃO (EXTRACT)
# ==============================================================================
def extrair_dados(prefixo: str) -> pd.DataFrame:
    logging.info(f"Iniciando extração para o domínio: {prefixo.upper()}")
    df_list = []
    
    for ano in ANOS:
        padrao_busca = os.path.join(DATA_DIR, f"{prefixo}-{ano}.csv")
        arquivos = glob.glob(padrao_busca)
        
        if not arquivos:
            logging.warning(f"Nenhum arquivo encontrado para {prefixo} no ano {ano}.")
            continue
            
        for arquivo in arquivos:
            try:
                df = pd.read_csv(arquivo, sep=';', encoding='utf-8', low_memory=False)
                df['ano_arquivo'] = ano
                df_list.append(df)
                logging.info(f"Arquivo lido com sucesso: {arquivo} ({len(df)} linhas)")
            except UnicodeDecodeError:
                df = pd.read_csv(arquivo, sep=';', encoding='latin1', low_memory=False)
                df['ano_arquivo'] = ano
                df_list.append(df)
                logging.info(f"Arquivo lido com sucesso (latin1): {arquivo} ({len(df)} linhas)")
            except Exception as e:
                logging.error(f"Erro ao ler o arquivo {arquivo}: {e}")

    if not df_list:
        return pd.DataFrame()
        
    df_consolidado = pd.concat(df_list, ignore_index=True)
    logging.info(f"Extração de {prefixo.upper()} finalizada. Total de linhas: {len(df_consolidado)}")
    return df_consolidado

# ==============================================================================
# FUNÇÕES AUXILIARES DE CARGA DE DIMENSÕES
# ==============================================================================
def carregar_dimensao_e_retornar_ids(engine, df: pd.DataFrame, table_name: str, 
                                     colunas_banco: list, chave_natural: str, id_col_name: str) -> dict:
    df_unique = df[colunas_banco].drop_duplicates().dropna(subset=[chave_natural])
    
    try:
        query = f"SELECT {id_col_name}, {chave_natural} FROM {table_name}"
        df_existente = pd.read_sql(query, engine)
    except Exception as e:
        df_existente = pd.DataFrame(columns=[id_col_name, chave_natural])
        
    if not df_existente.empty:
        novos_registros = df_unique[~df_unique[chave_natural].isin(df_existente[chave_natural])]
    else:
        novos_registros = df_unique
        
    if not novos_registros.empty:
        logging.info(f"Inserindo {len(novos_registros)} novos registros na tabela {table_name}...")
        novos_registros.to_sql(name=table_name, con=engine, if_exists='append', index=False)
        
        query = f"SELECT {id_col_name}, {chave_natural} FROM {table_name}"
        df_existente = pd.read_sql(query, engine)
        
    mapeamento = dict(zip(df_existente[chave_natural], df_existente[id_col_name]))
    return mapeamento

# ==============================================================================
# FUNÇÕES DE TRANSFORMAÇÃO E CARGA (TRANSFORM & LOAD)
# ==============================================================================

def processar_licitacoes(engine, df_licitacoes: pd.DataFrame):
    if df_licitacoes.empty: return
    logging.info("Iniciando transformação de LICITAÇÕES...")
    
    df = df_licitacoes.copy()
    df.dropna(how='all', inplace=True)
    
    # PADRONIZAÇÃO DE DATAS: Formato DD/MM/AAAA para AAAA-MM-DD
    df['data_homologacao'] = pd.to_datetime(df['data_homologacao'], format='%d/%m/%Y', errors='coerce').dt.strftime('%Y-%m-%d')

    # PADRONIZAÇÃO DO NÚMERO DA LICITAÇÃO
    df['numero_licitacao'] = df['numero_licitacao'].apply(padronizar_numero_licitacao)

    df['codigo_unidade_gestora'] = df['codigo_unidade_gestora'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    df['nome_municipio'] = df['nome_municipio'].astype(str).str.strip().str.upper()

    # 1. Município
    df_mun = df[['nome_municipio']].copy()
    map_mun = carregar_dimensao_e_retornar_ids(engine, df_mun, 'municipio', ['nome_municipio'], 'nome_municipio', 'id_municipio')
    df['municipio_id'] = df['nome_municipio'].map(map_mun)

    # 2. Unidade Gestora
    df_ug = df[df['codigo_unidade_gestora'] != 'nan'][['codigo_unidade_gestora', 'descricao_unidade_gestora', 'municipio_id']].copy()
    map_ug = carregar_dimensao_e_retornar_ids(engine, df_ug, 'unidade_gestora', 
                                              ['codigo_unidade_gestora', 'descricao_unidade_gestora', 'municipio_id'], 
                                              'codigo_unidade_gestora', 'id_unidade_gestora')
    df['unidade_gestora_id'] = df['codigo_unidade_gestora'].map(map_ug)

    # Tabela modalidade_licitacao removida

    colunas_fato_licitacao = [
        'numero_licitacao', 'numero_protocolo_tce', 'ano_licitacao', 
        'data_homologacao', 'objeto_licitacao', 
        'unidade_gestora_id', 'municipio_id'
    ]
    
    df_fato = df.dropna(subset=['unidade_gestora_id', 'municipio_id'])[colunas_fato_licitacao]
    df_fato = df_fato.drop_duplicates(subset=['numero_licitacao', 'numero_protocolo_tce'])
    
    logging.info("Carregando tabela fato: LICITAÇÃO...")
    df_fato.to_sql(name='licitacao', con=engine, if_exists='append', index=False, chunksize=10000)
    logging.info(f"Carga de {len(df_fato)} registros de LICITAÇÕES concluída.")


def processar_despesas(engine, df_despesas: pd.DataFrame):
    if df_despesas.empty: return
    logging.info("Iniciando transformação de DESPESAS (EMPENHO)...")
    
    df = df_despesas.copy()
    df.dropna(how='all', inplace=True)
    
    # Nomes fiéis ao cabeçalho do arquivo despesas.csv (Removida a Função)
    map_colunas = {
        'csv_municipio': 'municipio',
        'csv_codigo_ug': 'codigo_unidade_gestora',
        'csv_desc_ug': 'descricao_unidade_gestora',
        'csv_cpf_cnpj': 'cpf_cnpj',
        'csv_nome_fornecedor': 'nome_credor',
        'csv_cod_programa': 'codigo_programa',
        'csv_desc_programa': 'programa',   
        'csv_cod_acao': 'codigo_acao',
        'csv_desc_acao': 'acao',           
        'csv_num_obra': 'numero_obra',
        'csv_num_licitacao': 'numero_licitacao',
        'csv_num_empenho': 'numero_empenho',
        'csv_data_empenho': 'data_empenho',
        'csv_mes': 'mes',
        'csv_valor_empenhado': 'valor_empenhado',
        'csv_valor_liquidado': 'valor_liquidado',
        'csv_valor_pago': 'valor_pago',
        'csv_cod_fonte': 'codigo_fonte_recurso',
        'csv_desc_fonte': 'descricao_fonte_recurso',
        'csv_ano_fonte': 'ano_fonte',
        'csv_cod_uo': 'codigo_unidade_orcamentaria',
        'csv_desc_uo': 'descricao_unidade_orcamentaria'
    }

    # PADRONIZAÇÃO DE DATAS: Garante formato AAAA-MM-DD
    df['data_empenho'] = pd.to_datetime(df[map_colunas['csv_data_empenho']], format='%Y-%m-%d', errors='coerce').dt.strftime('%Y-%m-%d')
    
    # PADRONIZAÇÃO DO NÚMERO DA LICITAÇÃO
    if map_colunas['csv_num_licitacao'] in df.columns:
        df[map_colunas['csv_num_licitacao']] = df[map_colunas['csv_num_licitacao']].apply(padronizar_numero_licitacao)

    # PADRONIZAÇÃO DO MÊS: Mantém apenas números (Ex: "01-Janeiro" -> 1)
    if map_colunas['csv_mes'] in df.columns:
        df[map_colunas['csv_mes']] = df[map_colunas['csv_mes']].astype(str).str.extract(r'(\d+)')[0]
        df[map_colunas['csv_mes']] = pd.to_numeric(df[map_colunas['csv_mes']], errors='coerce').astype('Int64')

    for col_valor in [map_colunas['csv_valor_empenhado'], map_colunas['csv_valor_liquidado'], map_colunas['csv_valor_pago']]:
        if col_valor in df.columns:
            if df[col_valor].dtype == 'O':
                df[col_valor] = df[col_valor].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0.0)

    cols_para_string = [
        map_colunas['csv_municipio'], map_colunas['csv_codigo_ug'], map_colunas['csv_cpf_cnpj'],
        map_colunas['csv_cod_programa'], map_colunas['csv_cod_acao'],
        map_colunas['csv_num_obra'], map_colunas['csv_num_licitacao'], map_colunas['csv_num_empenho'],
        map_colunas['csv_cod_fonte'], map_colunas['csv_cod_uo']
    ]
    
    for col in cols_para_string:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

    colunas_descritivas = [
        map_colunas['csv_nome_fornecedor'], 
        map_colunas['csv_desc_programa'], 
        map_colunas['csv_desc_acao'],
        map_colunas['csv_desc_fonte'],
        map_colunas['csv_desc_uo']
    ]
    
    for col in colunas_descritivas:
        if col in df.columns:
            df[col] = df[col].fillna('NÃO INFORMADO').astype(str)
            df.loc[df[col].str.strip().isin(['nan', 'None', '']), col] = 'NÃO INFORMADO'

    logging.info("Carregando Dimensões para Empenhos (isso pode demorar devido ao volume)...")

    # 1. Município & UG
    df_mun = df[[map_colunas['csv_municipio']]].rename(columns={map_colunas['csv_municipio']: 'nome_municipio'})
    map_mun = carregar_dimensao_e_retornar_ids(engine, df_mun, 'municipio', ['nome_municipio'], 'nome_municipio', 'id_municipio')
    df['municipio_id'] = df[map_colunas['csv_municipio']].map(map_mun)

    df_ug = df[df[map_colunas['csv_codigo_ug']] != 'nan'][[map_colunas['csv_codigo_ug'], map_colunas['csv_desc_ug'], 'municipio_id']].rename(
        columns={map_colunas['csv_codigo_ug']: 'codigo_unidade_gestora', map_colunas['csv_desc_ug']: 'descricao_unidade_gestora'})
    map_ug = carregar_dimensao_e_retornar_ids(engine, df_ug, 'unidade_gestora', ['codigo_unidade_gestora', 'descricao_unidade_gestora', 'municipio_id'], 'codigo_unidade_gestora', 'id_unidade_gestora')
    df['unidade_gestora_id'] = df[map_colunas['csv_codigo_ug']].map(map_ug)

    # 2. Fornecedor
    df_forn = df[df[map_colunas['csv_cpf_cnpj']] != 'nan'][[map_colunas['csv_cpf_cnpj'], map_colunas['csv_nome_fornecedor']]].rename(
        columns={map_colunas['csv_cpf_cnpj']: 'cpf_cnpj', map_colunas['csv_nome_fornecedor']: 'nome'})
    map_forn = carregar_dimensao_e_retornar_ids(engine, df_forn, 'fornecedor', ['cpf_cnpj', 'nome'], 'cpf_cnpj', 'id_fornecedor')
    df['credor_id'] = df[map_colunas['csv_cpf_cnpj']].map(map_forn)

    # Tabela Função removida do processo

    # 3. Programa & Ação 
    df_prog = df[df[map_colunas['csv_cod_programa']] != 'nan'][[map_colunas['csv_cod_programa'], map_colunas['csv_desc_programa']]].rename(
        columns={map_colunas['csv_cod_programa']: 'codigo_programa', map_colunas['csv_desc_programa']: 'descricao_programa'})
    map_prog = carregar_dimensao_e_retornar_ids(engine, df_prog, 'programa', ['codigo_programa', 'descricao_programa'], 'codigo_programa', 'id_programa')
    df['programa_id'] = df[map_colunas['csv_cod_programa']].map(map_prog)

    df_acao = df[df[map_colunas['csv_cod_acao']] != 'nan'][[map_colunas['csv_cod_acao'], map_colunas['csv_desc_acao'], 'programa_id']].rename(
        columns={map_colunas['csv_cod_acao']: 'codigo_acao', map_colunas['csv_desc_acao']: 'descricao_acao'})
    map_acao = carregar_dimensao_e_retornar_ids(engine, df_acao, 'acao', ['codigo_acao', 'descricao_acao', 'programa_id'], 'codigo_acao', 'id_acao')
    df['acao_id'] = df[map_colunas['csv_cod_acao']].map(map_acao)

    # 4. Obra
    df_obra = df[df[map_colunas['csv_num_obra']] != 'nan'][[map_colunas['csv_num_obra']]].rename(columns={map_colunas['csv_num_obra']: 'numero_obra'})
    map_obra = carregar_dimensao_e_retornar_ids(engine, df_obra, 'obra', ['numero_obra'], 'numero_obra', 'id_obra')
    df['obra_id'] = df[map_colunas['csv_num_obra']].map(map_obra)

    # 5. Mapeamento de Licitação
    try:
        df_lic_bd = pd.read_sql("SELECT id_licitacao, numero_licitacao FROM licitacao", engine)
        map_lic = dict(zip(df_lic_bd['numero_licitacao'].astype(str), df_lic_bd['id_licitacao']))
        df['licitacao_id'] = df[map_colunas['csv_num_licitacao']].map(map_lic)
    except Exception as e:
        df['licitacao_id'] = None

    # 6. Fonte de Recurso
    df_fonte = df[df[map_colunas['csv_cod_fonte']] != 'nan'][[
        map_colunas['csv_cod_fonte'], map_colunas['csv_desc_fonte'], map_colunas['csv_ano_fonte']
    ]].rename(columns={
        map_colunas['csv_cod_fonte']: 'codigo_fonte_recurso', 
        map_colunas['csv_desc_fonte']: 'descricao_fonte_recurso', 
        map_colunas['csv_ano_fonte']: 'ano_fonte'
    })
    
    df_fonte['ano_fonte'] = df_fonte['ano_fonte'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    df_fonte.loc[df_fonte['ano_fonte'].isin(['nan', 'None', '']), 'ano_fonte'] = None

    map_fonte = carregar_dimensao_e_retornar_ids(engine, df_fonte, 'fonte_recurso', 
                                              ['codigo_fonte_recurso', 'descricao_fonte_recurso', 'ano_fonte'], 
                                              'codigo_fonte_recurso', 'id_fonte_recurso')
    df['fonte_recurso_id'] = df[map_colunas['csv_cod_fonte']].map(map_fonte)

    # 7. Unidade Orçamentária 
    df_uo = df[df[map_colunas['csv_cod_uo']] != 'nan'][[
        map_colunas['csv_cod_uo'], map_colunas['csv_desc_uo']
    ]].rename(columns={
        map_colunas['csv_cod_uo']: 'codigo_unidade_orcamentaria', 
        map_colunas['csv_desc_uo']: 'descricao_unidade_orcamentaria'
    })
    map_uo = carregar_dimensao_e_retornar_ids(engine, df_uo, 'unidade_orcamentaria', 
                                              ['codigo_unidade_orcamentaria', 'descricao_unidade_orcamentaria'], 
                                              'codigo_unidade_orcamentaria', 'id_unidade_orcamentaria')
    df['unidade_orcamentaria_id'] = df[map_colunas['csv_cod_uo']].map(map_uo)

    # --- CARGA DA TABELA FATO (empenho) ---
    colunas_finais = {
        map_colunas['csv_num_empenho']: 'numero_empenho',
        'data_empenho': 'data_empenho',
        map_colunas['csv_mes']: 'mes',
        'unidade_gestora_id': 'unidade_gestora_id',
        'municipio_id': 'municipio_id',
        'credor_id': 'credor_id',
        map_colunas['csv_valor_empenhado']: 'valor_empenhado',
        map_colunas['csv_valor_liquidado']: 'valor_liquidado',
        map_colunas['csv_valor_pago']: 'valor_pago',
        'licitacao_id': 'licitacao_id',
        'obra_id': 'obra_id',
        'acao_id': 'acao_id',
        'fonte_recurso_id': 'fonte_recurso_id',
        'unidade_orcamentaria_id': 'unidade_orcamentaria_id'
    }
    
    df_fato = df.rename(columns=colunas_finais)[list(colunas_finais.values())]
    df_fato = df_fato.dropna(subset=['unidade_gestora_id', 'municipio_id', 'fonte_recurso_id', 'unidade_orcamentaria_id'])
    
    logging.info("Carregando tabela fato: EMPENHO...")
    df_fato.to_sql(name='empenho', con=engine, if_exists='append', index=False, chunksize=50000)
    
    logging.info(f"Carga de {len(df_fato)} registros de DESPESAS (EMPENHOS) concluída.")

# ==============================================================================
# ORQUESTRAÇÃO DO PIPELINE
# ==============================================================================
def executar_pipeline():
    logging.info("=== INICIANDO PIPELINE DE ETL TCE-PB ===")
    
    try:
        engine = create_engine(DATABASE_URI, pool_recycle=3600)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            logging.info("Conexão com o banco de dados estabelecida com sucesso.")
            
    except SQLAlchemyError as e:
        logging.critical(f"Falha ao conectar no banco de dados: {e}")
        return

    df_licitacoes = extrair_dados("licitacoes")
    processar_licitacoes(engine, df_licitacoes)

    df_despesas = extrair_dados("despesas")
    processar_despesas(engine, df_despesas)

    logging.info("=== PIPELINE DE ETL FINALIZADO COM SUCESSO ===")

# ==============================================================================
# EXECUÇÃO PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    print("\n" + "="*55)
    print("=== MENU DE EXECUÇÃO DO PIPELINE ETL TCE-PB ===")
    print("="*55)
    print("Escolha o escopo de dados que deseja processar:")
    print("  [2023]  - Processar apenas os dados de 2023")
    print("  [2024]  - Processar apenas os dados de 2024")
    print("  [2025]  - Processar apenas os dados de 2025")
    print("  [TODOS] - Processar 2023, 2024 e 2025 de uma vez")
    print("="*55)
    
    opcao_ano = input("Digite a sua escolha: ").strip().upper()
    
    if opcao_ano in ['2023', '2024', '2025']:
        ANOS = [int(opcao_ano)]
        logging.info(f"Modo configurado para rodar APENAS o ano isolado: {opcao_ano}")
    elif opcao_ano == 'TODOS':
        logging.info("Modo configurado para rodar TODOS os anos disponíveis na pasta.")
    else:
        logging.error("Opção inválida. O script será encerrado.")
        exit()
        
    executar_pipeline()
