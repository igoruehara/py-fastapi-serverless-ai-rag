# Contratos de API

Este documento descreve os principais contratos HTTP do projeto.

Base local:

```text
http://localhost:8000
```

## Health

### `GET /health`

Verifica se a aplicação está respondendo.

Resposta esperada:

```json
{
  "status": "ok"
}
```

## Conversation

### `POST /api/conversation`

Recebe uma mensagem de conversa e envia para SQS.

Payload:

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

Resposta:

```json
{
  "queued": true,
  "messageId": "sqs-message-id"
}
```

## LLM

### `GET /api/llm/models`

Retorna modelos padrão configurados por provider.

Resposta:

```json
{
  "providers": {
    "openai": {
      "defaultModel": "gpt-5.5",
      "embeddingModel": "text-embedding-3-large"
    },
    "claude": {
      "defaultModel": null
    }
  }
}
```

### `POST /api/llm/chat`

Executa chat direto com um provider LLM.

Payload com `text`:

```json
{
  "provider": "openai",
  "model": "gpt-5.5",
  "text": "Explique RAG em uma frase",
  "systemPrompt": "Responda em português claro",
  "temperature": 0.2,
  "maxTokens": 500
}
```

Payload com `messages`:

```json
{
  "provider": "claude",
  "model": "seu-modelo-claude",
  "messages": [
    {
      "role": "system",
      "content": "Responda em português claro"
    },
    {
      "role": "user",
      "content": "Explique arquitetura hexagonal"
    }
  ]
}
```

Resposta:

```json
{
  "provider": "openai",
  "model": "gpt-5.5",
  "text": "Resposta gerada pelo modelo.",
  "usage": {},
  "raw": {}
}
```

## RAG

### `POST /api/rag/create-collection`

Cria a collection no Milvus.

Payload:

```json
{
  "collectionName": "rag_documents",
  "embeddingDim": 3072
}
```

Resposta:

```json
{
  "collectionName": "rag_documents",
  "created": true
}
```

### `POST /api/rag/create-index`

Cria índices no Milvus.

Payload:

```json
{
  "collectionName": "rag_documents"
}
```

Resposta:

```json
{
  "collectionName": "rag_documents",
  "indexed": true
}
```

### `POST /api/rag/embedding-create`

Cria embedding para um texto.

Payload:

```json
{
  "text": "Texto que será vetorizado"
}
```

Resposta:

```json
{
  "embedding": [0.1, 0.2, 0.3],
  "dimension": 3072
}
```

### `POST /api/rag/add-documents`

Ingere documentos no RAG.

Payload:

```json
{
  "collectionName": "rag_documents",
  "chunkSize": 512,
  "chunkOverlap": 70,
  "batchSize": 100,
  "deduplicate": true,
  "noSplit": false,
  "noHeader": false,
  "documents": [
    {
      "text": "Conteúdo do documento...",
      "agentId": "agent-1",
      "embeddingName": "manual-comercial",
      "embeddingId": "doc-1",
      "extraFields": {
        "origem": "manual",
        "relevante": true
      }
    }
  ]
}
```

Resposta:

```json
{
  "collectionName": "rag_documents",
  "documents": 1,
  "chunks": 3,
  "inserted": 3,
  "skippedDuplicates": 0
}
```

### `POST /api/rag/search-hybrid`

Executa busca híbrida no Milvus.

Payload:

```json
{
  "query": "Qual é a política comercial?",
  "agentId": "agent-1",
  "collectionName": "rag_documents",
  "extraFields": {
    "origem": "manual"
  },
  "k": 15,
  "denseWeight": 0.7,
  "sparseWeight": 0.3,
  "useHybrid": true,
  "relevanceBoost": 1.5,
  "fusionStrategy": "rrf"
}
```

Resposta:

```json
{
  "results": [
    {
      "id": "123",
      "score": 0.98,
      "text": "Trecho recuperado...",
      "agentId": "agent-1",
      "embeddingName": "manual-comercial",
      "embeddingId": "doc-1",
      "extraFields": {},
      "denseScore": 0.92,
      "sparseScore": 0.81
    }
  ]
}
```

### `POST /api/rag/chat-llm-rag`

Executa busca RAG e envia o contexto recuperado para um LLM.

Payload:

```json
{
  "provider": "openai",
  "model": "gpt-5.5",
  "text": "Qual é a política comercial?",
  "agentId": "agent-1",
  "collectionName": "rag_documents",
  "systemPrompt": "Responda com base no contexto quando possível.",
  "params": {
    "k": 15,
    "denseWeight": 0.7,
    "sparseWeight": 0.3,
    "fusionStrategy": "rrf"
  }
}
```

Resposta:

```json
{
  "text": "Resposta gerada pelo LLM.",
  "provider": "openai",
  "model": "gpt-5.5",
  "usage": {},
  "rag": {
    "enabled": true,
    "collectionName": "rag_documents",
    "documents": []
  }
}
```
