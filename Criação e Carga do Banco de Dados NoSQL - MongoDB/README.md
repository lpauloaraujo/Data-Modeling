# Criação e Carga do Banco de Dados NoSQL - MongoDB

Este módulo descreve o processo de migração do banco de dados relacional **MySQL** (já populado no módulo **"Criação e Carga do Banco de Dados Relacional - MySQL"**) para um banco **NoSQL MongoDB**.

A migração parte do schema e dados existentes no MySQL (`tce_pb`) e cria/abastece uma base MongoDB (ex.: `tce_pb_mongo`) no servidor local.

---

## Pré-requisitos

Antes de iniciar:

- Ter concluído a etapa anterior: **MySQL** `tce_pb` **criado e populado**
- Ter o **MongoDB** rodando localmente (ex.: `localhost:27017`)

---

## Ferramentas necessárias

### 1) MongoDB Compass
Interface gráfica para visualizar/validar as coleções e documentos no MongoDB.

Download (oficial):
https://www.mongodb.com/products/tools/compass

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
