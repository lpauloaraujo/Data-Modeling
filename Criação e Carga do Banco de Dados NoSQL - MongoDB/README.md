# Criação e Carga do Banco de Dados NoSQL - MongoDB

Este módulo descreve o processo de migração do banco de dados relacional **MySQL** (já populado no módulo **"Criação e Carga do Banco de Dados Relacional - MySQL"**) para um banco **NoSQL MongoDB**, utilizando a ferramenta **MongoDB Relational Migrator**.

A migração parte do schema e dados existentes no MySQL (`tce_pb`) e cria/abastece uma base MongoDB (ex.: `tce_pb_mongo`) no servidor local.

---

## Pré-requisitos

Antes de iniciar:

- Ter concluído a etapa anterior: **MySQL `tce_pb` criado e populado**
- Ter o **MySQL Server** rodando localmente (ex.: `localhost:3306`)
- Ter o **MongoDB** rodando localmente (ex.: `localhost:27017`)
- Ter o **MySQL Workbench** instalado (usado para configurar timezone e conferir tabelas)

---

## Ferramentas necessárias

### 1) MongoDB Relational Migrator
Ferramenta usada para conectar no MySQL e migrar schema/dados para o MongoDB.

Download (oficial):
https://www.mongodb.com/try/download/relational-migrator

### 2) MongoDB Compass
Interface gráfica para visualizar/validar as coleções e documentos no MongoDB.

Download (oficial):
https://www.mongodb.com/products/tools/compass

---

## Instalação (Relational Migrator e Compass)

Para **cada instalador**:

1. Baixe o instalador pelo link oficial
2. Execute o arquivo baixado
3. Aceite os termos (se solicitado)
4. Clique em **Install / Instalar**
5. Ao final, clique em **Finish / Finalizar**

---

## Abrindo o MongoDB Relational Migrator

Após instalar:

1. Pesquise no computador por **MongoDB Relational Migration** (ou **Relational Migrator**)
2. Abra o programa

---

## Fluxo 1 — Conectar o MySQL (fonte)

Ao abrir o Relational Migrator:

1. Feche a tela **Get Started** (se aparecer)
2. Clique em **Connect Database**
3. Clique em **Add a new connection**
4. Em **Database type**, selecione **MySQL**
5. Preencha:

   - **Host**: `localhost`
   - **Database**: `tce_pb`
   - **Username**: `root`
   - **Password**: *sua senha*

6. Clique em **Connect**
7. Selecione o banco **`tce_pb`**
8. Escolha a opção:

   **Start with a MongoDB schema that matches your relational schema**

9. Clique em **Next**
10. Em **Project name**, use: `tce_pb`
11. Clique em **Done**

---

## Se aparecer erro de driver JDBC do MySQL

Em alguns casos, ao tentar conectar no MySQL, pode aparecer:

> **JDBC driver for MySQL not found. Please download the JAR file, upload, and restart Relational Migrator.**

Quando isso acontecer, faça o seguinte:

### 1) Baixar o driver oficial do MySQL (Connector/J)

Baixe o driver oficial do MySQL (Connector/J) neste link:

https://dev.mysql.com/downloads/connector/j/

- **Windows:** selecione a opção **Platform Independent** (ela disponibiliza o arquivo `.jar` que o Relational Migrator precisa).

Nome esperado (exemplos):

- `mysql-connector-j-8.0.xx.jar`  
ou
- `mysql-connector-j-9.x.x.jar`

### 2) Fazer upload no Relational Migrator

Quando aparecer a mensagem solicitando o driver:

1. Clique em **Upload**
2. Selecione o arquivo `.jar` baixado
3. Reinicie o **Relational Migrator**

### 3) Tentar conectar novamente

Após reiniciar, repita o processo de conexão no MySQL.

---

## Configuração de Timezone (IMPORTANTE)

Antes de criar o **criar o job de migração para o MongoDB**, execute no **MySQL Workbench**:

```sql
SET GLOBAL time_zone = '-03:00';
SET time_zone = '-03:00';
```

Isso ajuda a evitar inconsistências relacionadas a datas/horários durante a migração.

---

## Fluxo 2 — Criar o Job de Migração para MongoDB (destino)

Agora vamos criar o job que migra os dados para o MongoDB:

1. Acesse a seção **Data Migration**
2. Clique em **Create migration job**
3. Clique em **Add a new connection**
4. Em **MongoDB connection string (URI)**, use:

   `mongodb://localhost:27017`

5. Informe (ou selecione) o banco de destino como:

   `tce_pb_mongo`

6. Clique em **Connect**
7. Revise o **Summary**
8. Clique em **Start**

---

## Validação no MongoDB Compass (conferência final)

Após finalizar a migração:

1. Abra o **MongoDB Compass**
2. Conecte usando a URI:

   `mongodb://localhost:27017`

3. Localize o banco **`tce_pb_mongo`**
4. Verifique as **collections** geradas e amostras de documentos
5. Confirme se a quantidade e conteúdo estão consistentes com o MySQL (amostragem)

---

## Observações

- Esta etapa **depende** do MySQL já estar **criado e populado** (módulo anterior).
- O padrão deste tutorial assume ambiente local:
  - MySQL em `localhost:3306`
  - MongoDB em `localhost:27017`
- O nome do banco de destino no MongoDB pode ser alterado, mas recomenda-se manter um nome claro (ex.: `tce_pb_mongo`) para evitar confusão com o schema relacional.
