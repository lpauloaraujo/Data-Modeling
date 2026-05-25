# Data Warehouse - Star Schema (TCE-PB)

Modelagem dimensional dos dados do Tribunal de Contas do Estado da Paraiba
(TCE-PB), construida a partir do banco relacional OLTP (`tce_pb`) ja carregado
nas etapas anteriores do projeto.

## Visao geral

| Item | Valor |
|---|---|
| Schema alvo | `tce_pb_dw` |
| Schema fonte | `tce_pb` (OLTP) |
| Modelo | **Star Schema** |
| Tabelas | **1 fato + 7 dimensoes** |
| SGBD | MySQL 8.x |
| Tecnologia ETL | Python 3.10+ / pandas / SQLAlchemy / PyMySQL |

## Modelo dimensional

```
                       dim_tempo
                           |
       dim_fornecedor -----+----- dim_municipio
                           |
   dim_programa_acao ---- FATO ---- dim_estrutura_administrativa
                          EMPENHO          (UG + UO)
                           |
       dim_fonte_recurso --+-- dim_licitacao
```

### Dimensoes

| # | Dimensao | Conteudo | Origem |
|---|---|---|---|
| 1 | `dim_tempo` | data, ano, mes, trimestre, semestre, dia, dia_semana, fim_de_semana | gerada (calendario) |
| 2 | `dim_municipio` | nome_municipio | OLTP |
| 3 | `dim_estrutura_administrativa` | UG + UO denormalizadas | OLTP (JOIN via empenho) |
| 4 | `dim_fornecedor` | cpf_cnpj, nome, **tipo_pessoa (PF/PJ/ND)** | OLTP + derivacao |
| 5 | `dim_programa_acao` | Programa + Acao denormalizadas | OLTP (JOIN) |
| 6 | `dim_fonte_recurso` | codigo, descricao, ano_fonte | OLTP |
| 7 | `dim_licitacao` | numero, protocolo, ano, **modalidade**, objeto, data_homologacao | OLTP (+ CSV opcional) |

### Fato

`fato_empenho` — **grao: 1 linha por empenho**

- **Surrogate keys (7)**: `sk_tempo`, `sk_municipio`, `sk_estrutura_admin`,
  `sk_fornecedor`, `sk_programa_acao`, `sk_fonte_recurso`, `sk_licitacao`
- **Degenerate dimensions**: `numero_empenho`, `numero_obra`
  (atributos que ficam no fato sem virar dimensao propria — apenas 1 coluna cada)
- **Medidas**: `valor_empenhado`, `valor_liquidado`, `valor_pago`,
  `saldo_a_pagar` *(calculada: empenhado - pago)*

### Decisoes de modelagem

| Decisao | Justificativa |
|---|---|
| **Denormalizar UG + UO** em `dim_estrutura_administrativa` | UO e subdivisao orcamentaria da UG (LRF / Lei 4.320). Relacao hierarquica natural, sem risco de cartesian explosion (~2k combinacoes reais). |
| **Denormalizar Programa + Acao** | Sempre consultadas em conjunto. Snowflake aqui so atrapalha. |
| **Obra como degenerate dimension** | Tem apenas 1 atributo (`numero_obra`) - nao justifica tabela propria. |
| **Surrogate keys** (`sk_*`) | Desacopla DW de mudancas em chaves naturais do OLTP. Padrao Kimball. |
| **Sentinel rows (sk = -1)** | "NAO INFORMADO" / "SEM LICITACAO" - evita NULL em FK, garante integridade referencial. |
| **`dim_tempo` com PK = `YYYYMMDD`** | Smart surrogate key debugavel. Permite JOIN direto `dt.data = e.data_empenho`. |

## Como executar

### 1. Pre-requisitos

- MySQL 8.x rodando local
- Schema `tce_pb` ja carregado pelo ETL relacional original (`etl_tce_pb.py`)
- Python 3.10+

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Criar o DW (estrutura + sentinel rows)

Execute no MySQL Workbench (ou CLI) o arquivo `SCHEMA_DW.sql`. Ele:

- Cria o schema `tce_pb_dw`
- Cria as 8 tabelas (1 fato + 7 dims) com FKs e indices
- Insere as 7 sentinel rows (sk = -1)

### 4. Configurar credenciais (opcional)

Por padrao usa `root@localhost:3306` e pede a senha interativamente.
Pode sobrescrever via variaveis de ambiente:

```bash
export DB_USER=root
export DB_PASS=sua_senha
export DB_HOST=localhost
export DB_PORT=3306
```

### 5. Rodar o ETL

```bash
python etl_tce_pb_dw.py
```

O script pergunta se voce quer **enriquecer a `modalidade`** das licitacoes
lendo os CSVs originais (`licitacoes-*.csv`). Isso e necessario porque o ETL
relacional original descartou essa coluna ao carregar o OLTP.

- **`N` (padrao)**: usa apenas o OLTP, `modalidade` fica como `'NAO INFORMADO'`
- **`s`**: le os CSVs `licitacoes-*.csv` para popular `modalidade`

## Pipeline ETL

```
1.  Conecta OLTP e DW
2.  TRUNCATE em todas as tabelas do DW + SET FOREIGN_KEY_CHECKS=0
3.  Re-insere sentinel rows (sk = -1)
4.  Carrega dim_tempo       (gera calendario 2023-2025 = 1.096 linhas)
5.  Carrega dim_municipio
6.  Carrega dim_estrutura_administrativa (DISTINCT de UG x UO via empenho)
7.  Carrega dim_fornecedor                (deriva tipo_pessoa PF/PJ/ND)
8.  Carrega dim_programa_acao
9.  Carrega dim_fonte_recurso
10. Carrega dim_licitacao                 (modalidade = 'NAO INFORMADO')
11. [Opcional] Enriquece dim_licitacao.modalidade via CSV
12. Carrega fato_empenho via INSERT INTO ... SELECT JOIN cross-schema
13. Imprime resumo (linhas por tabela + valor total empenhado)
```

A carga do fato e feita por **um unico `INSERT INTO ... SELECT`** com JOINs
entre os schemas `tce_pb` e `tce_pb_dw`, o que evita trazer milhoes de linhas
ao Python e e bem mais rapido (executa dentro do engine MySQL).

## Queries analiticas de exemplo

### Top 10 municipios por valor empenhado em 2024

```sql
SELECT m.nome_municipio,
       SUM(f.valor_empenhado) AS total_empenhado
FROM   tce_pb_dw.fato_empenho f
JOIN   tce_pb_dw.dim_municipio m  ON f.sk_municipio = m.sk_municipio
JOIN   tce_pb_dw.dim_tempo     t  ON f.sk_tempo     = t.sk_tempo
WHERE  t.ano = 2024
GROUP BY m.nome_municipio
ORDER BY total_empenhado DESC
LIMIT 10;
```

### Gasto por modalidade de licitacao e trimestre

```sql
SELECT t.ano,
       t.nome_trimestre,
       l.modalidade,
       SUM(f.valor_pago) AS total_pago
FROM   tce_pb_dw.fato_empenho f
JOIN   tce_pb_dw.dim_tempo     t ON f.sk_tempo     = t.sk_tempo
JOIN   tce_pb_dw.dim_licitacao l ON f.sk_licitacao = l.sk_licitacao
GROUP BY t.ano, t.nome_trimestre, l.modalidade
ORDER BY t.ano, t.nome_trimestre, total_pago DESC;
```

### Top 20 fornecedores PJ por valor recebido

```sql
SELECT fo.nome,
       fo.cpf_cnpj,
       SUM(f.valor_pago) AS total_recebido,
       COUNT(*)          AS qtd_empenhos
FROM   tce_pb_dw.fato_empenho f
JOIN   tce_pb_dw.dim_fornecedor fo ON f.sk_fornecedor = fo.sk_fornecedor
WHERE  fo.tipo_pessoa = 'PJ'
GROUP BY fo.nome, fo.cpf_cnpj
ORDER BY total_recebido DESC
LIMIT 20;
```

### Saldo a pagar (resto a pagar) por UG

```sql
SELECT ea.descricao_unidade_gestora,
       SUM(f.saldo_a_pagar) AS resto_a_pagar
FROM   tce_pb_dw.fato_empenho f
JOIN   tce_pb_dw.dim_estrutura_administrativa ea
       ON f.sk_estrutura_admin = ea.sk_estrutura_admin
GROUP BY ea.descricao_unidade_gestora
HAVING resto_a_pagar > 0
ORDER BY resto_a_pagar DESC
LIMIT 50;
```

## Estrutura de arquivos

```
Data Warehouse - Star Schema/
├── README.md             (este arquivo)
├── SCHEMA_DW.sql         (DDL: schema + tabelas + sentinel rows)
├── etl_tce_pb_dw.py      (ETL OLTP -> DW)
└── requirements.txt      (dependencias Python)
```
