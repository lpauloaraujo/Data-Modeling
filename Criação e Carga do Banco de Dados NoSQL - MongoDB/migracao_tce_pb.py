import mysql.connector
from pymongo import MongoClient
from bson.decimal128 import Decimal128
from datetime import datetime, date
from decimal import Decimal
import time
import getpass

# ==========================================
# 1. CONFIGURAÇÕES DE CONEXÃO BASE
# ==========================================
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'database': 'tce_pb'
}

MONGO_URI = 'mongodb://localhost:27017'
MONGO_DB_NAME = 'tce_pb_mongo'
MONGO_COLLECTION_NAME = 'empenhos'

# ==========================================
# 2. FUNÇÕES DE TRANSFORMAÇÃO (HELPERS)
# ==========================================
def parse_decimal(value):
    """Converte Decimal do MySQL para Decimal128 do MongoDB"""
    if value is not None and isinstance(value, Decimal):
        return Decimal128(str(value))
    return None

def parse_date(value):
    """Converte Date do MySQL para Datetime do MongoDB"""
    if value is not None and isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    return None

# ==========================================
# 3. PROCESSO DE MIGRAÇÃO
# ==========================================
def migrate_data():
    print("="*50)
    print("MIGRAÇÃO DE DADOS: MySQL -> MongoDB")
    print("="*50)
    
    # Solicita a senha de forma segura (os caracteres não aparecem na tela)
    senha = getpass.getpass(prompt="Digite a senha do MySQL (root): ")
    MYSQL_CONFIG['password'] = senha
    
    tempo_inicio = time.time()
    
    print("\nConectando ao MySQL...")
    try:
        # O buffered=False é VITAL aqui para não estourar a RAM
        mysql_conn = mysql.connector.connect(**MYSQL_CONFIG)
        mysql_cursor = mysql_conn.cursor(dictionary=True, buffered=False)
    except mysql.connector.Error as err:
        print(f"❌ Erro ao conectar no MySQL: {err}")
        return
        
    print("Conectando ao MongoDB...")
    mongo_client = MongoClient(MONGO_URI)
    mongo_db = mongo_client[MONGO_DB_NAME]
    mongo_collection = mongo_db[MONGO_COLLECTION_NAME]
    
    # Limpa a coleção de destino
    print("Limpando coleção 'empenhos' antiga...")
    mongo_collection.drop()

    sql_query = """
        SELECT 
            e.id_empenho, e.numero_empenho, e.data_empenho, e.mes, 
            e.valor_empenhado, e.valor_liquidado, e.valor_pago,
            uo.id_unidade_orcamentaria, uo.codigo_unidade_orcamentaria, uo.descricao_unidade_orcamentaria,
            o.id_obra, o.numero_obra,
            f.id_fornecedor, f.cpf_cnpj, f.nome as nome_fornecedor,
            l.id_licitacao, l.numero_licitacao, l.numero_protocolo_tce, l.ano_licitacao, l.data_homologacao, l.objeto_licitacao,
            fr.id_fonte_recurso, fr.codigo_fonte_recurso, fr.descricao_fonte_recurso, fr.ano_fonte,
            a.id_acao, a.codigo_acao, a.descricao_acao,
            p.id_programa, p.codigo_programa, p.descricao_programa,
            m.id_municipio, m.nome_municipio,
            ug.id_unidade_gestora, ug.codigo_unidade_gestora, ug.descricao_unidade_gestora
        FROM empenho e
        LEFT JOIN unidade_orcamentaria uo ON e.unidade_orcamentaria_id = uo.id_unidade_orcamentaria
        LEFT JOIN obra o ON e.obra_id = o.id_obra
        LEFT JOIN fornecedor f ON e.credor_id = f.id_fornecedor
        LEFT JOIN licitacao l ON e.licitacao_id = l.id_licitacao
        LEFT JOIN fonte_recurso fr ON e.fonte_recurso_id = fr.id_fonte_recurso
        LEFT JOIN acao a ON e.acao_id = a.id_acao
        LEFT JOIN programa p ON a.programa_id = p.id_programa
        LEFT JOIN municipio m ON e.municipio_id = m.id_municipio
        LEFT JOIN unidade_gestora ug ON e.unidade_gestora_id = ug.id_unidade_gestora;
    """

    print("Executando query no MySQL (isso pode levar alguns minutos para iniciar a leitura)...")
    mysql_cursor.execute(sql_query)
    
    documentos_mongodb = []
    linhas_processadas = 0
    tamanho_do_lote = 5000 # Envia para o MongoDB de 5 em 5 mil
    
    print("\nIniciando transformação e carga (ETL)...")
    
    # fetchmany permite ler o banco em pedaços (chunks), economizando RAM
    while True:
        lote_mysql = mysql_cursor.fetchmany(tamanho_do_lote)
        if not lote_mysql:
            break # Sai do loop quando não houver mais linhas
            
        for row in lote_mysql:
            documento = {
                "idEmpenho": row['id_empenho'],
                "numeroEmpenho": row['numero_empenho'],
                "dataEmpenho": parse_date(row['data_empenho']),
                "mes": row['mes'],
                "valorEmpenhado": parse_decimal(row['valor_empenhado']),
                "valorLiquidado": parse_decimal(row['valor_liquidado']),
                "valorPago": parse_decimal(row['valor_pago']),
                
                "unidadeOrcamentaria": {
                    "idUnidadeOrcamentaria": row['id_unidade_orcamentaria'],
                    "codigoUnidadeOrcamentaria": row['codigo_unidade_orcamentaria'],
                    "descricaoUnidadeOrcamentaria": row['descricao_unidade_orcamentaria']
                } if row['id_unidade_orcamentaria'] else None,
                
                "obra": {
                    "idObra": row['id_obra'],
                    "numeroObra": row['numero_obra']
                } if row['id_obra'] else None,
                
                "fornecedor": {
                    "idFornecedor": row['id_fornecedor'],
                    "cpfCnpj": row['cpf_cnpj'],
                    "nome": row['nome_fornecedor']
                } if row['id_fornecedor'] else None,
                
                "licitacao": {
                    "idLicitacao": row['id_licitacao'],
                    "numeroLicitacao": row['numero_licitacao'],
                    "numeroProtocoloTce": row['numero_protocolo_tce'],
                    "anoLicitacao": row['ano_licitacao'],
                    "dataHomologacao": parse_date(row['data_homologacao']),
                    "objetoLicitacao": row['objeto_licitacao']
                } if row['id_licitacao'] else None,
                
                "fonteRecurso": {
                    "idFonteRecurso": row['id_fonte_recurso'],
                    "codigoFonteRecurso": row['codigo_fonte_recurso'],
                    "descricaoFonteRecurso": row['descricao_fonte_recurso'],
                    "anoFonte": row['ano_fonte']
                } if row['id_fonte_recurso'] else None,
                
                "acao": {
                    "idAcao": row['id_acao'],
                    "codigoAcao": row['codigo_acao'],
                    "descricaoAcao": row['descricao_acao'],
                    "programa": {
                        "idPrograma": row['id_programa'],
                        "codigoPrograma": row['codigo_programa'],
                        "descricaoPrograma": row['descricao_programa']
                    } if row['id_programa'] else None
                } if row['id_acao'] else None,
                
                "municipio": {
                    "idMunicipio": row['id_municipio'],
                    "nomeMunicipio": row['nome_municipio']
                } if row['id_municipio'] else None,
                
                "unidadeGestora": {
                    "idUnidadeGestora": row['id_unidade_gestora'],
                    "codigoUnidadeGestora": row['codigo_unidade_gestora'],
                    "descricaoUnidadeGestora": row['descricao_unidade_gestora']
                } if row['id_unidade_gestora'] else None
            }
            
            # Remove chaves nulas
            documento = {k: v for k, v in documento.items() if v is not None}
            documentos_mongodb.append(documento)
            linhas_processadas += 1

        # Insere o lote no MongoDB
        if documentos_mongodb:
            mongo_collection.insert_many(documentos_mongodb)
            documentos_mongodb = [] # Reseta o lote de inserção
            
        # Imprime o progresso a cada 100.000 linhas
        if linhas_processadas % 100000 == 0:
            print(f"Progresso: {linhas_processadas:,} documentos inseridos no MongoDB...")

    tempo_fim = time.time()
    minutos = (tempo_fim - tempo_inicio) / 60
    
    print("\n" + "="*50)
    print(f"✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print(f"Total de documentos inseridos: {linhas_processadas:,}")
    print(f"Tempo total: {minutos:.2f} minutos.")
    print("="*50)

    # Limpeza
    mysql_cursor.close()
    mysql_conn.close()
    mongo_client.close()

if __name__ == "__main__":
    migrate_data()