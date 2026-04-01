# 📊 Data Modeling - TCE-PB

Repositório referente ao trabalho da disciplina de **Modelagem de Dados** (BSI - UFRPE).

---

## 📁 Sobre o Projeto

Este projeto tem como objetivo a modelagem de dados a partir de informações públicas do **Tribunal de Contas do Estado da Paraíba (TCE-PB)**, com foco nas seguintes categorias:

- Receitas
- Despesas
- Licitações

A base de dados utilizada é proveniente do portal de dados abertos do TCE-PB, contendo informações consolidadas dos municípios paraibanos :contentReference[oaicite:0]{index=0}.

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
- Receita  
- Fornecedor  
- Fonte de Recurso  
- Tipo de Receita  
- Modalidade de Licitação  

Foram removidas entidades não essenciais (como subfunção, natureza e proposta), visando simplificar o modelo e adequá-lo ao escopo do estudo.

---

## 📊 Características da Base

- 9 arquivos CSV analisados  
- Mais de **7,5 milhões de registros** no total :contentReference[oaicite:1]{index=1}  
- Dados reais da administração pública  

---

## 🚀 Como utilizar

1. Baixar o arquivo `.mwb`
2. Abrir no **MySQL Workbench**
3. Visualizar ou editar o DER

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
