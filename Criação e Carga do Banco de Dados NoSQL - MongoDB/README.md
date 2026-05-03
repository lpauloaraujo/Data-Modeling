# Criação e Carga do Banco de Dados NoSQL - MongoDB

Este módulo descreve o processo de migração do banco de dados relacional **MySQL** (já populado no módulo **"Criação e Carga do Banco de Dados Relacional - MySQL"**) para um banco **NoSQL MongoDB**.

A migração parte do schema e dados existentes no MySQL (`tce_pb`) e cria/abastece uma base MongoDB (ex.: `tce_pb_mongo`) no servidor local.

---

## Pré-requisitos

Antes de iniciar:

- Ter concluído a etapa anterior: **MySQL** `tce_pb` **criado e populado**
- Ter o **MySQL Server** rodando localmente (ex.: `localhost:3306`)
- Ter o **MongoDB** rodando localmente (ex.: `localhost:27017`)

---

## Ferramentas necessárias

### 1) MongoDB Compass
Interface gráfica para visualizar/validar as coleções e documentos no MongoDB.

Download (oficial):
https://www.mongodb.com/products/tools/compass

---

## Guia de Instalação e Execução

Siga o passo a passo abaixo para configurar o ambiente e executar a migração do banco relacional **MySQL (`tce_pb`)** para o banco **NoSQL MongoDB (`tce_pb_mongo`)**.

---

### Passo 1: Garantir que a etapa do MySQL foi concluída

Antes de iniciar a migração para o MongoDB, é **obrigatório** ter concluído a etapa anterior:

- O **MySQL Server** precisa estar rodando localmente (ex.: `localhost:3306`)
- O schema **`tce_pb`** deve estar **criado e populado** (tabelas e dados carregados pelo pipeline do módulo **Relacional - MySQL**)

> A migração deste módulo **não** lê CSVs diretamente — ela lê **do banco MySQL já populado**.

---

### Passo 2: Ter o MongoDB rodando localmente

Você precisa ter uma instância do **MongoDB** em execução, por padrão em:

- `mongodb://localhost:27017`

Você pode validar se o MongoDB está ativo abrindo o **MongoDB Compass** e tentando conectar na URI acima.

---

### Passo 3: Clonar ou baixar o repositório

Se ainda não tiver os arquivos na sua máquina, clone o repositório:

```bash
git clone https://github.com/lpauloaraujo/Data-Modeling.git
```

Ou baixe o projeto em ZIP pelo GitHub e extraia localmente.

---

### Passo 4: Entrar na pasta do módulo NoSQL (MongoDB)

No terminal, navegue até a pasta:

```bash
cd "Data-Modeling/Criação e Carga do Banco de Dados NoSQL - MongoDB"
```

---

### Passo 5: Criar e ativar um ambiente virtual (venv) (recomendado)

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

### Passo 6: Instalar dependências

Com o terminal na pasta do módulo, instale as bibliotecas necessárias:

```bash
pip install -r requirements.txt
```

**Bibliotecas instaladas:**
- `mysql-connector-python`: conexão e leitura do MySQL
- `pymongo`: conexão e escrita no MongoDB

---

### Passo 7: Conferir configurações de conexão (se necessário)

O script de migração (`migracao_tce_pb.py`) usa por padrão:

- **MySQL**
  - host: `localhost`
  - user: `root`
  - database: `tce_pb`
  - password: solicitada interativamente ao executar o script

- **MongoDB**
  - URI: `mongodb://localhost:27017`
  - database: `tce_pb_mongo`
  - collection: `empenhos`

Se o seu ambiente for diferente (host/porta/usuário), ajuste as constantes no início do arquivo `migracao_tce_pb.py`:

- `MYSQL_CONFIG`
- `MONGO_URI`
- `MONGO_DB_NAME`
- `MONGO_COLLECTION_NAME`

---

### Passo 8: Executar o script de migração

Execute o script:

```bash
python migracao_tce_pb.py
```

Ao iniciar, o programa irá solicitar a senha do MySQL de forma segura:

```text
Digite a senha do MySQL (root):
```

> A senha **não aparece** enquanto você digita (comportamento normal do `getpass`).

---

## Validação no MongoDB Compass (conferência final)

Após finalizar a migração:

1. Abra o **MongoDB Compass**
2. Conecte usando:

   `mongodb://localhost:27017`

3. Acesse o database **`tce_pb_mongo`**
4. Abra a collection **`empenhos`**
5. Verifique:
   - Quantidade de documentos
   - Estrutura dos subdocumentos (ex.: `fornecedor`, `unidadeGestora`, `acao.programa`)
   - Campos numéricos e datas (amostragem)

---

## O que o Script Faz

O script `migracao_tce_pb.py` realiza as seguintes operações:

1. Conecta ao **MySQL** e ao **MongoDB**
2. **Apaga** a collection de destino (`empenhos`) para evitar duplicidades
3. Executa uma query com `JOINs` para montar a visão completa do **Empenho**
4. Transforma os dados para o formato de documento:
   - Datas (`DATE`) → `datetime`
   - Decimais (`DECIMAL`) → `Decimal128`
   - Entidades relacionadas viram **subdocumentos** (ex.: `fornecedor`, `licitacao`, `acao.programa`)
5. Insere os documentos no MongoDB em **lotes** (chunks) para reduzir uso de memória
6. Exibe progresso e, ao final, total de documentos e tempo total

---

## Troubleshooting

### Erro ao conectar no MySQL
- Confirme que o MySQL está rodando e acessível em `localhost`
- Verifique usuário/senha
- Confirme se o database `tce_pb` existe e está populado

### Erro ao conectar no MongoDB
- Confirme que o serviço do MongoDB está em execução
- Valide a URI `mongodb://localhost:27017`
- Teste a conexão no MongoDB Compass

### Migração “demora para começar”
- É esperado que a query com `JOINs` leve algum tempo para iniciar a leitura, dependendo do volume de dados e performance do MySQL

### Dados duplicados no MongoDB
- O script já executa `drop()` na collection antes de inserir
- Se você removeu essa linha, volte a habilitá-la ou limpe a collection manualmente antes de reexecutar

---

## Diferença Arquitetural: Modelagem MySQL vs MongoDB

Durante o processo de migração, a estrutura do banco de dados sofreu uma grande transformação para se adequar ao paradigma NoSQL. É importante entender que **um banco de dados orientado a documentos (MongoDB) não deve ser um espelho de um banco relacional (MySQL)**.

Abaixo estão os principais conceitos aplicados nesta mudança estrutural:

### 1. De Normalização (MySQL) para Desnormalização (MongoDB)
* **No MySQL (Relacional):** Os dados são divididos em múltiplas tabelas (normalização) para evitar duplicação. Para visualizar as informações completas de um empenho, o banco de dados precisa realizar vários `JOINs` entre tabelas como `fornecedor`, `municipio`, `licitacao`, etc.
* **No MongoDB (NoSQL):** A regra de ouro é: *"dados que são acessados juntos, devem ser armazenados juntos"*. O objetivo é trazer a informação completa com uma única consulta, garantindo alta performance na leitura. Para isso, utilizamos a técnica de **Desnormalização por Documentos Embutidos (Embedding)**.

### 2. A Coleção Central (empenhos)
Analisando o domínio de negócio (TCE-PB), a entidade central é o **Empenho**. 
Em vez de criarmos 10 coleções diferentes no MongoDB e tentar relacioná-las depois, criamos uma única coleção principal chamada `empenhos`. 

Todas as outras tabelas que qualificam o empenho foram transformadas em **sub-documentos (objetos embutidos)** dentro do próprio documento do empenho.
* Entidades como `fornecedor`, `obra`, `fonte_recurso`, `municipio` e `unidade_gestora` agora residem dentro de cada empenho.
* Foi criada uma hierarquia de aninhamento no Nível 2: O `programa` foi embutido dentro da `acao`, e a `acao` foi embutida no `empenho`, respeitando a lógica orçamentária.

### 3. Remoção das Chaves Estrangeiras (Limpeza)
No mundo relacional, as Foreign Keys (IDs como `credor_id`, `municipio_id`) servem como "pontes" para buscar dados em outras tabelas. 
Como no MongoDB nós trouxemos o objeto completo (ex: o documento inteiro do fornecedor com CNPJ e Nome) para dentro do empenho, **essas chaves estrangeiras soltas na raiz perderam a utilidade**. Por isso, durante o *Fluxo 2*, nós removemos todos esses campos terminados em "Id" que ficavam sobrando, garantindo um documento JSON limpo, legível e otimizado para o consumo de APIs.
