# Métricas de Desempenho ETL

Esta pasta contém uma **variação instrumentada** do pipeline de ETL do projeto (módulo **Criação e Carga do Banco de Dados Relacional - MySQL**), criada **exclusivamente** para **medir o tempo de execução** das cargas de dados realizadas no MySQL.

Os códigos-fonte aqui presentes (**`etl_tce_pb_desempenho.py`** e **`SCHEMA_desempenho.sql`**) são **versões adaptadas** dos scripts originais do projeto. As modificações foram feitas **somente** com o objetivo de coletar métricas de tempo por tabela, usando a biblioteca `time` no Python e um **schema de teste** no MySQL.

---

## Arquivos da pasta

- **`SCHEMA_desempenho.sql`**
  - Cria o schema de teste **`tce_pb_teste`** com a mesma estrutura do schema original.
  - Serve para isolar testes de desempenho e evitar impacto no banco principal.

- **`etl_tce_pb_desempenho.py`**
  - Executa o ETL lendo os CSVs do TCE-PB (licitações e despesas).
  - Realiza transformações, carga de dimensões e carga das tabelas fato.
  - Mede o tempo de execução da carga de cada tabela (dimensões e fatos) usando `time`.

---

## Objetivo (por que este módulo existe?)

Este módulo existe para permitir:
- Medir o **tempo gasto na carga** de cada tabela do modelo.
- Comparar desempenho entre execuções (ex.: por ano, por máquina, por volume).
- Executar testes sem “sujar” o schema principal do projeto, utilizando o **schema `tce_pb_teste`**.

> Importante: estas versões não foram criadas para alterar regras de negócio ou transformar dados de forma diferente do pipeline original — apenas para **instrumentação e medição de performance**.

---

## Pré-requisitos

Antes de executar:

- Ter o **MySQL Server** instalado e rodando localmente (ex.: `localhost:3306`)
- Ter os **arquivos CSV** na pasta onde o script será executado (mesmo padrão do módulo relacional):
  - `licitacoes-2023.csv`, `licitacoes-2024.csv`, `licitacoes-2025.csv`
  - `despesas-2023.csv`, `despesas-2024.csv`, `despesas-2025.csv`

---

## Como executar

### 1) Criar o schema de teste no MySQL

Abra o MySQL Workbench (ou outro cliente) e execute o script:

- `SCHEMA_desempenho.sql`

Isso criará o schema:

- `tce_pb_teste`

---

### 2) Criar e ativar um ambiente virtual (venv) (recomendado)

Recomendado para isolar as dependências do projeto.

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

**Linux/macOS (bash/zsh):**
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

> Dica: depois de ativar, seu terminal geralmente mostra `(.venv)` no início da linha.

---

### 3) Instalar dependências

Com o terminal aberto **nesta pasta** (onde está o arquivo `requirements.txt`), instale as dependências com:

```bash
pip install -r requirements.txt
```

**Dependências utilizadas (resumo):**
- `pandas`: leitura/manipulação dos CSVs e transformações
- `SQLAlchemy`: conexão e escrita no MySQL
- `pymysql`: driver MySQL para o SQLAlchemy

> Observação: a biblioteca `time` usada para medir desempenho já faz parte da biblioteca padrão do Python, portanto **não precisa** estar no `requirements.txt`.

---

### 4) Executar o ETL com métricas

No terminal, entre na pasta **Métricas de Desempenho ETL** e execute:

```bash
python etl_tce_pb_desempenho.py
```

Ao iniciar, o script solicitará a senha do banco (caso não esteja em variável de ambiente).

Você também poderá escolher o escopo do processamento:

- **2023**, **2024**, **2025** ou **TODOS**

---

## O que é medido?

O arquivo `etl_tce_pb_desempenho.py` usa a biblioteca **`time`** para medir o tempo decorrido durante:

- Inserção de registros em **tabelas dimensão** (ex.: `municipio`, `unidade_gestora`, `fornecedor`, etc.)
- Carga das **tabelas fato**:
  - `licitacao`
  - `empenho`

As medições são exibidas no console junto aos logs do pipeline.

---

## Observações importantes

- Este módulo utiliza um schema separado (**`tce_pb_teste`**) para garantir um ambiente controlado e não interferir no banco principal.
- O foco é medir **tempo de carga**; os resultados podem variar conforme:
  - desempenho da máquina
  - volume de dados processado
  - configurações do MySQL
  - execução por ano vs. todos os anos

---

## Troubleshooting rápido

- **Erro ao conectar no MySQL**
  - Verifique se o MySQL está rodando em `localhost:3306`
  - Confira usuário/senha
  - Confirme se o schema `tce_pb_teste` foi criado com sucesso

- **Arquivos CSV não encontrados**
  - Garanta que os CSVs estão na mesma pasta em que você está executando o script
  - Verifique se os nomes seguem exatamente o padrão `prefixo-AAAA.csv`

- **Execução muito lenta**
  - É esperado em volumes grandes; prefira executar por ano para controlar e comparar tempos.
