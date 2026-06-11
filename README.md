# py-fastapi-serverless-ai-rag

Backend em Python com FastAPI, arquitetura hexagonal, deploy serverless na AWS e integrações com LLMs e RAG.

Este projeto foi criado para demonstrar uma arquitetura moderna de backend para aplicações de IA: uma API HTTP/WebSocket/SQS rodando em AWS Lambda Container, com deploy via Serverless Framework, CI/CD pelo GitHub Actions, configuração por SSM Parameter Store, integração com OpenAI, Claude e busca RAG com Milvus.

## Objetivo

A aplicação funciona como uma base de orquestração para sistemas conversacionais e fluxos de IA.

Ela permite:

- Receber mensagens por HTTP e enfileirar processamento em SQS.
- Processar eventos de SQS e WebSocket dentro da mesma Lambda.
- Consultar modelos da OpenAI e da Anthropic/Claude escolhendo o modelo por API.
- Criar embeddings com OpenAI.
- Ingerir documentos, vetorizar chunks e salvar no Milvus.
- Executar busca híbrida com dense vector + BM25 sparse.
- Fazer chat com RAG usando contexto recuperado do Milvus.
- Fazer deploy em AWS usando Docker, ECR, Lambda, API Gateway, SQS, DynamoDB e Serverless Framework.

## Stack

- Python 3.14
- FastAPI
- Mangum
- Pydantic Settings
- OpenAI Python SDK
- Anthropic Python SDK
- PyMilvus
- AWS Lambda Container Image
- AWS ECR
- API Gateway HTTP API
- API Gateway WebSocket
- SQS + DLQ
- DynamoDB
- AWS Systems Manager Parameter Store
- Serverless Framework v4
- GitHub Actions com OIDC
- Docker

## Arquitetura

O projeto usa arquitetura hexagonal para separar regra de negócio, contratos e infraestrutura.

```text
app/
  api/
    routes/                 # Entrada HTTP: FastAPI

  domain/
    entities/               # Entidades puras de domínio
    ports/                  # Contratos: LLM, embeddings, vector store, fila

  application/
    use_cases/              # Casos de uso da aplicação
    container.py            # Composição dos adapters concretos

  infrastructure/
    conversation/           # Adapter SQS e mapeamento de payload
    llm/                    # Adapters OpenAI e Claude
    rag/                    # Adapter Milvus
    text/                   # Chunking e normalização de metadados

  handlers/                 # Entradas Lambda fora do HTTP: SQS e WebSocket
  core/                     # Configuração e logging
```

Fluxo principal:

```text
FastAPI / Lambda / SQS / WebSocket
  -> application/use_cases
    -> domain/ports
      -> infrastructure/adapters
```

Com isso, a regra central não depende diretamente de FastAPI, boto3, OpenAI, Claude ou Milvus.

## Continuidade com IA

O repositório também foi preparado para ser evoluído por pessoas usando agentes de IA como Codex, Cursor, Claude Code ou Copilot.

Arquivos principais:

```text
AGENTS.md                          # Instruções globais para agentes de IA
docs/sdd/architecture.md           # Arquitetura e decisões
docs/sdd/api-contracts.md          # Contratos dos endpoints
docs/sdd/coding-standards.md       # Padrões de código
docs/sdd/workflows/                # Workflows de negócio ou exemplos
docs/ai/rules.md                   # Regras técnicas para pessoas e agentes
docs/ai/continuation.md            # Guia de continuidade assistida por IA
docs/ai/skills/                    # Skills locais para tarefas recorrentes
```

Skills disponíveis:

```text
docs/ai/skills/criar-skill-api.md
docs/ai/skills/revisar-arquitetura.md
docs/ai/skills/criar-testes.md
```

A intenção é reduzir ambiguidade para quem baixar o projeto e quiser continuar usando IA, mantendo o padrão hexagonal, os contratos de API, as regras de deploy e o isolamento entre domínio e infraestrutura.

## Funcionalidades

### Conversation + SQS

Endpoint:

```http
POST /api/conversation
```

Recebe uma mensagem de conversa e publica na fila SQS criada pela stack.

Exemplo:

```json
{
  "message": "Olá, preciso de ajuda",
  "conversationId": "conv-1",
  "context": {},
  "agentId": "agent-1",
  "requestId": "req-1",
  "timestamp": 1710000000000,
  "channel": "webchat",
  "convId": "conv-1"
}
```

### Chat com LLM

Endpoint:

```http
POST /api/llm/chat
```

Exemplo com OpenAI:

```json
{
  "provider": "openai",
  "model": "gpt-5.5",
  "text": "Explique RAG em uma frase",
  "systemPrompt": "Responda em português claro"
}
```

Exemplo com Claude:

```json
{
  "provider": "claude",
  "model": "seu-modelo-claude",
  "text": "Explique arquitetura hexagonal em uma frase"
}
```

### RAG com Milvus

Endpoints:

```text
POST /api/rag/create-collection
POST /api/rag/create-index
POST /api/rag/add-documents
POST /api/rag/embedding-create
POST /api/rag/search-hybrid
POST /api/rag/chat-llm-rag
```

A collection do Milvus usa:

- `dense`: vetor denso com dimensão 3072.
- `sparse`: vetor sparse gerado por BM25.
- `text`: campo textual com analyzer.
- `extraFields`: metadados em JSON.
- `agentId`: isolamento por agente.
- `embeddingName` e `embeddingId`: rastreabilidade do documento.

A busca híbrida combina:

- Similaridade vetorial densa.
- Busca sparse/BM25.
- Fusão por RRF ou score ponderado.
- Boost por `extraFields.relevante = true`.
- Limite opcional de chunks por documento.

Exemplo de ingestão:

```json
{
  "collectionName": "rag_documents",
  "chunkSize": 512,
  "chunkOverlap": 70,
  "deduplicate": true,
  "documents": [
    {
      "text": "Conteúdo do documento...",
      "agentId": "agent-1",
      "embeddingName": "politica-comercial",
      "extraFields": {
        "origem": "manual",
        "relevante": true
      }
    }
  ]
}
```

Exemplo de chat com RAG:

```json
{
  "provider": "openai",
  "model": "gpt-5.5",
  "text": "Qual é a política comercial?",
  "agentId": "agent-1",
  "params": {
    "k": 15,
    "denseWeight": 0.7,
    "sparseWeight": 0.3,
    "fusionStrategy": "rrf"
  }
}
```

## Rodando localmente

Crie o ambiente virtual:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```powershell
pip install -r requirements-dev.txt
```

Crie o arquivo `.env`:

```powershell
copy .env.example .env
```

Suba a API:

```powershell
uvicorn app.main:app --reload --port 8000
```

URLs locais:

```text
GET  http://localhost:8000/health
GET  http://localhost:8000/docs
POST http://localhost:8000/api/conversation
POST http://localhost:8000/api/llm/chat
POST http://localhost:8000/api/rag/search-hybrid
POST http://localhost:8000/api/rag/chat-llm-rag
```

## Configuração

Em ambiente local, use `.env`.

Em AWS, a aplicação carrega parâmetros do AWS Systems Manager Parameter Store quando:

```text
APP_CONFIG_SOURCE=ssm
APP_SSM_PREFIX=/<service>/<stage>
```

Variáveis principais:

```text
OPENAI_API_KEY
OPENAI_DEFAULT_MODEL
OPENAI_EMBEDDING_MODEL
ANTHROPIC_API_KEY
ANTHROPIC_DEFAULT_MODEL
MILVUS_URI
MILVUS_TOKEN
MILVUS_USERNAME
MILVUS_PASSWORD
MILVUS_COLLECTION_NAME
MILVUS_EMBEDDING_DIM
```

Exemplo de parâmetro no SSM:

```text
/dev-fastapi-serverless/dev/OPENAI_API_KEY
```

Esse parâmetro vira:

```text
os.environ["OPENAI_API_KEY"]
```

## Deploy

Instale as dependências Node:

```powershell
npm install
```

Valide a configuração:

```powershell
npx serverless print --stage dev
```

Faça deploy manual:

```powershell
npx serverless deploy --stage dev
```

## CI/CD

O projeto possui workflow em:

```text
.github/workflows/aws.yml
```

O deploy usa GitHub Actions com OIDC para assumir uma IAM Role na AWS sem salvar `AWS_ACCESS_KEY_ID` e `AWS_SECRET_ACCESS_KEY` no GitHub.

Branches:

```text
main    -> dev
homolog -> hml
prd     -> prd
```

Secrets necessários:

```text
AWS_DEPLOY_ROLE_ARN
SERVERLESS_ACCESS_KEY
```

Variável opcional:

```text
AWS_REGION
```

## Serverless

A stack cria:

- Lambda com imagem Docker.
- Repositório ECR gerenciado pelo Serverless.
- HTTP API.
- WebSocket API.
- SQS principal.
- SQS DLQ.
- DynamoDB para conexões WebSocket.
- Permissões IAM para SQS, DynamoDB, WebSocket Management API e SSM.

## Observações

Este projeto é uma base arquitetural para portfólio e evolução prática. Em produção, eu adicionaria autenticação, rate limiting, observabilidade com tracing, testes de integração com LocalStack/Milvus e política de custos para uso de LLMs.
