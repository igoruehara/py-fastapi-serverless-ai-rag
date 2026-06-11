# Arquitetura

Este documento descreve a arquitetura do projeto `py-fastapi-serverless-ai-rag`.

## Visão geral

O projeto é um backend FastAPI para aplicações de IA generativa, com deploy em AWS Lambda Container e suporte a RAG com Milvus.

Ele foi organizado com arquitetura hexagonal para separar:

- Entrada da aplicação.
- Casos de uso.
- Domínio.
- Contratos.
- Integrações externas.

## Diagrama lógico

```text
Clientes HTTP / WebSocket / Eventos SQS
  -> api/routes ou handlers
    -> application/use_cases
      -> domain/entities + domain/ports
        -> infrastructure/adapters
```

## Camadas

### API

Local:

```text
app/api/routes/
```

Responsabilidades:

- Expor endpoints FastAPI.
- Validar payloads HTTP com Pydantic.
- Converter DTOs para entidades de domínio.
- Traduzir exceções para respostas HTTP.

Não deve:

- Chamar boto3 diretamente.
- Chamar OpenAI/Claude diretamente.
- Chamar Milvus diretamente.
- Implementar regra de negócio.

### Handlers

Local:

```text
app/handlers/
```

Responsabilidades:

- Receber eventos Lambda que não passam pelo FastAPI.
- Mapear SQS, WebSocket e eventos diretos para casos de uso.

### Application

Local:

```text
app/application/
```

Responsabilidades:

- Orquestrar fluxos de negócio.
- Usar portas do domínio.
- Coordenar adapters por meio do container.
- Validar pré-condições do caso de uso.

Exemplos:

- `ChatUseCase`
- `RagUseCase`
- `EnqueueConversationUseCase`
- `ProcessConversationUseCase`

### Domain

Local:

```text
app/domain/
```

Responsabilidades:

- Entidades puras.
- Protocolos/ports.
- Tipos de domínio.

Não deve depender de frameworks ou SDKs externos.

### Infrastructure

Local:

```text
app/infrastructure/
```

Responsabilidades:

- Implementar adapters externos.
- Encapsular SDKs.
- Converter payloads de infraestrutura.

Adapters atuais:

- `OpenAiLlmAdapter`
- `OpenAiEmbeddingAdapter`
- `ClaudeLlmAdapter`
- `MilvusRagVectorStore`
- `SqsConversationQueueAdapter`

## Fluxos principais

### Conversation

```text
POST /api/conversation
  -> ConversationRequest
  -> ConversationMessage
  -> EnqueueConversationUseCase
  -> ConversationQueuePort
  -> SqsConversationQueueAdapter
  -> SQS
```

### Chat direto com LLM

```text
POST /api/llm/chat
  -> ChatUseCase
  -> LlmProviderPort
  -> OpenAiLlmAdapter ou ClaudeLlmAdapter
```

### RAG

```text
POST /api/rag/chat-llm-rag
  -> RagUseCase
  -> OpenAiEmbeddingAdapter
  -> MilvusRagVectorStore
  -> ChatUseCase
  -> OpenAI ou Claude
```

## Decisões arquiteturais

### Por que FastAPI?

FastAPI é leve, moderno, rápido e possui excelente integração com Pydantic e documentação OpenAPI.

### Por que Lambda Container?

O container facilita empacotar dependências de IA e SDKs que podem ser mais pesados que uma Lambda zip tradicional.

### Por que Serverless Framework?

O Serverless Framework simplifica o provisionamento de Lambda, API Gateway, SQS, DynamoDB, IAM e ECR.

### Por que SSM Parameter Store?

SSM evita segredos hardcoded e permite carregar configuração por stage.

### Por que arquitetura hexagonal?

Porque o projeto integra muitos sistemas externos. A arquitetura hexagonal mantém a regra de negócio isolada e facilita trocar adapters no futuro.

### Por que Milvus?

Milvus é um vector database robusto para RAG e suporta busca vetorial e busca híbrida com BM25/sparse vector.

## Como adicionar uma nova integração

1. Crie uma porta em `app/domain/ports`.
2. Crie um adapter em `app/infrastructure`.
3. Injete o adapter em `app/application/container.py`.
4. Use a porta no caso de uso.
5. Documente a decisão.

## Como adicionar uma nova rota

1. Crie DTOs Pydantic em `app/api/routes`.
2. Converta DTO para entidade de domínio.
3. Chame um caso de uso.
4. Retorne resposta serializável.
5. Documente em `docs/api-contracts.md`.
