# Workflow: Conversation + SQS

Este workflow documenta o fluxo real de recebimento de mensagens de conversa e publicação em SQS.

## Entrada HTTP

Endpoint:

```http
POST /api/conversation
```

Arquivo:

```text
app/api/routes/conversation.py
```

DTO de entrada:

```text
ConversationRequest
```

Campos aceitos:

```text
message
conversationId
context
agentId
requestId
timestamp
channel
convId
from
```

Campos extras são preservados em `ConversationMessage.extra`.

## Fluxo interno

```text
ConversationRequest
  -> ConversationMessage
  -> EnqueueConversationUseCase
  -> ConversationQueuePort
  -> SqsConversationQueueAdapter
  -> AWS SQS
```

Arquivos envolvidos:

```text
app/domain/entities/conversation.py
app/domain/ports/conversation_queue.py
app/application/use_cases/conversation.py
app/infrastructure/conversation/sqs_queue.py
app/application/container.py
```

## Publicação na fila

Adapter:

```text
SqsConversationQueueAdapter
```

Configuração necessária:

```text
NLP_CONVERSATION_QUEUE_URL
AWS_REGION
```

Em AWS, `NLP_CONVERSATION_QUEUE_URL` é preenchida pelo `serverless.yaml`.

Mensagem enviada:

```text
MessageBody = ConversationMessage.to_payload()
```

Atributos enviados:

```text
MessageType    = nlp-conversation
AgentId        = message.agent_id
ConversationId = message.conversation_id
```

## Processamento SQS

Entrada Lambda:

```text
app/lambda_handler.py
```

Handler SQS:

```text
app/handlers/sqs.py
```

Fluxo:

```text
SQS event
  -> handle_sqs_event
  -> process_record
  -> process_conversation_record
  -> conversation_from_payload
  -> ProcessConversationUseCase
```

O processamento atual registra os dados principais da conversa e mantém o ponto de extensão no caso de uso:

```text
app/application/use_cases/conversation.py
```

## Erros e retry

O handler retorna `batchItemFailures` para permitir retry item a item pelo SQS.

Se um item falhar:

```json
{
  "batchItemFailures": [
    {
      "itemIdentifier": "message-id"
    }
  ]
}
```

## Validações

```powershell
py -3.13 -m compileall app
npx serverless print --stage dev
```

## Pontos de manutenção

- Para alterar payload público, atualize `ConversationRequest` e `docs/sdd/api-contracts.md`.
- Para alterar regra do enfileiramento, atualize `EnqueueConversationUseCase`.
- Para trocar SQS por outro broker, crie outro adapter para `ConversationQueuePort`.
- Para processar a conversa com LLM/RAG, evolua `ProcessConversationUseCase`.
