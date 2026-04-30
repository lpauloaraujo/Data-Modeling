# Carga do Banco de Dados Relacional - MySQL

Este módulo realiza o processo de ETL (Extract, Transform, Load) para população do banco de dados relacional com dados de licitações e despesas do TCE-PB.

## Pré-requisitos

### 1. Criar o Schema do Banco de Dados

Antes de executar este script de carga, é **obrigatório** criar o schema do banco de dados executando o script SQL de criação.

Para instruções detalhadas sobre como criar o schema, consulte o [README principal do repositório](<https://github.com/lpauloaraujo/Data-Modeling>).

### 2. Preparar os Arquivos de Dados

Os arquivos CSV com os dados de licitações e despesas devem estar localizados nesta mesma pasta (`Carga do Banco de Dados Relacional - MySQL/`).

#### Arquivos Necessários

- **Licitações**: `licitacoes-2023.csv`, `licitacoes-2024.csv`, `licitacoes-2025.csv`
- **Despesas**: `despesas-2023.csv`, `despesas-2024.csv`, `despesas-2025.csv`

Para baixar os arquivos CSV, acesse: [Link para download dos arquivos](<https://dados-abertos.tce.pb.gov.br/>)

## Guia de Instalação e Execução

### Passo 1: Instalar Dependências

Execute o comando abaixo para instalar todas as bibliotecas Python necessárias:

```bash
pip install -r requirements.txt
```

**Bibliotecas instaladas:**
- `pandas`: Manipulação e transformação de dados
- `SQLAlchemy`: ORM para conexão com banco de dados
- `pymysql`: Driver MySQL para Python

### Passo 2: Configurar Variáveis de Ambiente (Opcional)

O script suporta variáveis de ambiente para conexão com o banco de dados. Você pode definir:

**Windows (PowerShell):**
```powershell
$env:DB_USER="seu_usuario"
$env:DB_PASS="sua_senha"
$env:DB_HOST="seu_host"
$env:DB_PORT="3306"
$env:DB_NAME="tce_pb"
```

**Linux/macOS (bash/zsh):**
```bash
export DB_USER="seu_usuario"
export DB_PASS="sua_senha"
export DB_HOST="seu_host"
export DB_PORT="3306"
export DB_NAME="tce_pb"
```

Se as variáveis não forem definidas, o script solicitará a senha interativamente e usará os valores padrão:

- `DB_USER`: `root`
- `DB_HOST`: `localhost`
- `DB_PORT`: `3306`
- `DB_NAME`: `tce_pb`

### Passo 3: Executar o Script de Carga

Execute o script Python:

```bash
python etl_tce_pb.py
```

### Passo 4: Escolher o Escopo de Dados

Ao executar o script, será apresentado um menu com as seguintes opções:

```text
=== MENU DE EXECUÇÃO DO PIPELINE ETL TCE-PB ===

Escolha o escopo de dados que deseja processar:
  [2023]  - Processar apenas os dados de 2023
  [2024]  - Processar apenas os dados de 2024
  [2025]  - Processar apenas os dados de 2025
  [TODOS] - Processar 2023, 2024 e 2025 de uma vez
```

**Recomendação:** É altamente recomendado executar a carga ano a ano (opções 2023, 2024 ou 2025) em vez de processar todos os anos simultaneamente. Essa abordagem oferece:

- Melhor controle e monitoramento do processo
- Detecção mais rápida de erros específicos de cada período
- Menor consumo de memória
- Facilita ajustes corretivos se necessário

## O que o Script Faz

O script `etl_tce_pb.py` realiza as seguintes operações:

### Extração (Extract)
- Lê arquivos CSV de licitações e despesas
- Consolida dados de múltiplos anos em um único DataFrame

### Transformação (Transform)
- Padroniza formatos de datas (DD/MM/AAAA → AAAA-MM-DD)
- Padroniza números de licitação (XXXXX/AAAA)
- Normaliza valores monetários
- Converte textos para maiúsculas conforme necessário
- Trata valores nulos e inconsistências de dados

### Carga (Load)
- Popula dimensões (Município, Unidade Gestora, Fornecedor, Programa, Ação, etc.)
- Carrega tabelas de fatos (Licitação, Empenho)
- Mantém referências de integridade entre dimensões e fatos

## Monitoramento da Execução

Durante a execução, o script gera logs com informações sobre:

- Arquivos lidos e quantidade de registros
- Inserções em tabelas de dimensões
- Progresso de carga das tabelas de fatos
- Mensagens de erro ou aviso (se houver)

Os logs são exibidos no console com timestamp e nível de severidade.

## Troubleshooting

### Erro de Conexão com Banco de Dados
- Verifique se o MySQL está em execução
- Confirme que as credenciais (usuário e senha) estão corretas
- Valide que o host e porta estão acessíveis

### Erro de Arquivo Não Encontrado
- Confirme que os arquivos CSV estão na pasta `Carga do Banco de Dados Relacional - MySQL/`
- Verifique se os nomes dos arquivos seguem o padrão: `licitacoes-AAAA.csv` e `despesas-AAAA.csv`

### Erro de Codificação
- O script tenta ler arquivos em UTF-8 primeiro
- Se falhar, tenta codificação Latin-1 automaticamente
- Caso persista, verifique a codificação do arquivo CSV

### Erro de Memória
- Se receber erro de memória ao processar todos os anos, execute a carga ano a ano (veja a recomendação acima)

## Estrutura do Código

- **Configurações e Constantes:** Definições de variáveis de ambiente e parâmetros
- **Funções de Tratamento de Dados:** Lógica de padronização de dados
- **Funções de Extração:** Leitura dos arquivos CSV
- **Funções Auxiliares:** Carga de dimensões e mapeamento de IDs
- **Funções de Transformação e Carga:** Processamento específico de licitações e despesas
- **Orquestração:** Pipeline principal que coordena todas as etapas
- **Execução:** Menu interativo para o usuário escolher o escopo de dados

## Notas Importantes

- O script é idempotente para dimensões (não duplica registros já existentes)
- Pode ser executado múltiplas vezes sem prejudicar a integridade dos dados
- Dados duplicados em tabelas de fatos são removidos antes da carga
- O processamento usa chunks para otimizar consumo de memória
