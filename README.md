# 📊 Data Modeling - TCE-PB

Repositório referente ao trabalho da disciplina de **Modelagem de Dados** (BSI - UFRPE).

---

## 📁 Sobre o Projeto

Este projeto tem como objetivo a modelagem de dados a partir de informações públicas do **Tribunal de Contas do Estado da Paraíba (TCE-PB)**, com foco nas seguintes categorias:

- Despesas
- Licitações

A base de dados utilizada é proveniente do portal de dados abertos do TCE-PB, contendo informações consolidadas dos municípios paraibanos: https://dados-abertos.tce.pb.gov.br/dados-consolidados

---

## 📅 Recorte Temporal

- Período analisado: **2023 a 2025**

---

## 🧠 Modelagem de Dados

O modelo foi estruturado com base nas entidades principais do domínio:

- Município  
- Unidade Gestora  
- Licitação  
- Empenho    
- Fornecedor  
- Fonte de Recurso
- Obra
- Programa
- Açao
- Unidade Orçamentária

Foram removidas entidades não essenciais (como subfunção, natureza e proposta), visando simplificar o modelo e adequá-lo ao escopo do estudo.

---

## 📊 Características da Base

- 6 arquivos CSV analisados  
- Mais de **7 milhões de registros** no total
- Dados reais da administração pública  

---

## 🗂️ Estrutura do Projeto

A organização do repositório segue uma separação por etapas/módulos do trabalho. A estrutura pode evoluir, mas em geral você encontrará algo próximo de:

```text
Data-Modeling/
├─ README.md
├─ (arquivo(s) do modelo) *.mwb
├─ Criação e Carga do Banco de Dados Relacional - MySQL/
│  ├─ README.md
│  ├─ SCHEMA.sql
│  ├─ requirements.txt
│  └─ etl_tce_pb.py
└─ Criação e Carga do Banco de Dados NoSQL - MongoDB/
   ├─ README.md
   ├─ requirements.txt
   └─ migracao_tce_pb.py
```

> Dica: caso você não encontre o arquivo `.mwb` na raiz, procure por ele nas pastas do projeto (ou utilize a busca do GitHub por `*.mwb`).

---

## 🚀 Como utilizar (tutorial rápido)

Abaixo está um passo a passo completo para você configurar o ambiente e visualizar/editar o **DER (Diagrama Entidade-Relacionamento)** no **MySQL Workbench**.

### 1) Baixar e instalar o MySQL Workbench (via MySQL Community)

O MySQL Workbench é a ferramenta oficial (gratuita) da Oracle/MySQL para modelagem (DER/EER), administração e consultas SQL.

1. Acesse a página oficial de downloads do MySQL:  
   https://www.mysql.com/downloads/

2. Procure por **MySQL Community Edition** (versão gratuita).  
   Dentro do ecossistema do MySQL Community você encontra:
   - **MySQL Server** (o SGBD em si, caso você queira rodar o banco localmente)
   - **MySQL Workbench** (interface para modelagem/DER, administração e queries)
   - **Conectores e ferramentas** (dependendo do sistema operacional/instalador)

3. Baixe e instale a opção recomendada para o seu sistema operacional.  
   Em muitos casos (principalmente no Windows), é comum existir um instalador que permite selecionar os componentes (incluindo o **Workbench**) e já configura o necessário para você trabalhar com o ecossistema MySQL.

> Observação: para **apenas abrir o arquivo `.mwb` e ver o DER**, normalmente basta o **MySQL Workbench**. O **MySQL Server** só é necessário se você quiser criar o banco e executar scripts localmente.

---

### 2) Clonar o repositório

Com o Git instalado, abra um terminal e execute:

```bash
git clone https://github.com/lpauloaraujo/Data-Modeling.git
```

Em seguida, entre na pasta do projeto:

```bash
cd Data-Modeling
```

> Alternativa: você também pode baixar como ZIP pela página do GitHub, extrair e abrir a pasta localmente.

---

### 3) Localizar o arquivo `.mwb` (modelo do Workbench)

O arquivo `.mwb` é o projeto do MySQL Workbench que contém o modelo/DER.

- Se o `.mwb` estiver na raiz, você o verá logo ao abrir a pasta.
- Se não estiver, procure nas subpastas do repositório.

Dica (opcional): você pode localizar via terminal (Linux/macOS/Git Bash):

```bash
find . -name "*.mwb"
```

---

### 4) Abrir o `.mwb` no MySQL Workbench

1. Abra o **MySQL Workbench**
2. Vá em **File > Open Model...** (ou equivalente)
3. Selecione o arquivo **`.mwb`** do projeto
4. Aguarde o carregamento do modelo

---

### 5) Visualizar ou editar o DER (EER Diagram)

Com o modelo aberto:

1. No painel do projeto, procure pela seção **EER Diagrams** (ou “Diagramas EER”)
2. Abra o diagrama (geralmente um “EER Diagram 1”)
3. A partir daí você pode:
   - Navegar pelas entidades e relacionamentos
   - Ajustar tabelas, atributos e chaves
   - Revisar cardinalidades e integridade
   - Exportar/imprimir o diagrama, se necessário

> Recomendação: ao editar, salve uma cópia do `.mwb` para evitar sobrescrever o arquivo original sem querer.

---

## 👥 Equipe

**Grupo 04**

- Tiago Garcia  
- Luiz Dutra  
- Lucas Paulo  
- Guilherme Silva  
- Diego Bernado  
- Marcos Vinícius  
- Yonara Silva  

---

## 📌 Observações

Este projeto utiliza dados públicos com finalidade acadêmica, voltados ao estudo de modelagem e organização de dados.
