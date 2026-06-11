# Workflow exemplo: consulta de agendamento

Este documento descreve um exemplo de evolução de negócio para demonstrar como adicionar um workflow usando a arquitetura atual.

Status: exemplo de design, não implementado.

## Objetivo

Permitir que um usuário consulte informações sobre agendamentos usando uma combinação de conversa, RAG e LLM.

Exemplo de pergunta:

```text
Quais documentos preciso levar para meu exame amanhã?
```

## Fluxo proposto

```text
Cliente
  -> POST /api/conversation
  -> SQS
  -> ProcessConversationUseCase
  -> RagUseCase.search_hybrid
  -> ChatUseCase
  -> Resposta por WebSocket ou outro canal
```

## Dados necessários

Documentos que poderiam ser ingeridos no RAG:

- Regras de preparo.
- Políticas de agendamento.
- Perguntas frequentes.
- Instruções por tipo de exame.
- Unidades e horários.

Campos sugeridos em `extraFields`:

```json
{
  "tipo": "preparo",
  "especialidade": "imagem",
  "exame": "ressonancia",
  "unidade": "pinheiros",
  "relevante": true
}
```

## Contrato de entrada

Reaproveita `POST /api/conversation`:

```json
{
  "message": "Quais documentos preciso levar?",
  "conversationId": "conv-123",
  "context": {
    "workflow": "consulta-agendamento",
    "appointmentId": "ag-456"
  },
  "agentId": "agent-agendamento",
  "requestId": "req-789",
  "timestamp": 1710000000000,
  "channel": "webchat"
}
```

## Caso de uso sugerido

Criar um novo caso de uso em:

```text
app/application/use_cases/consulta_agendamento.py
```

Responsabilidades:

- Validar dados mínimos da conversa.
- Buscar contexto no RAG por `agentId`.
- Montar prompt com dados do agendamento.
- Chamar `ChatUseCase`.
- Retornar resposta estruturada.

## Portas sugeridas

Se houver integração com sistema externo de agendamento:

```text
app/domain/ports/appointment_repository.py
```

Exemplo:

```python
class AppointmentRepositoryPort(Protocol):
    def get_by_id(self, appointment_id: str) -> Appointment | None:
        raise NotImplementedError
```

Adapter:

```text
app/infrastructure/appointments/
```

## Resposta esperada

```json
{
  "text": "Para este exame, leve documento com foto e pedido médico...",
  "confidence": "high",
  "sources": [
    {
      "embeddingName": "preparo-ressonancia",
      "score": 0.91
    }
  ]
}
```

## Regras para implementar

- Não colocar a regra de agendamento em `api/routes`.
- Criar entidades e portas no domínio.
- Criar caso de uso específico em `application/use_cases`.
- Usar adapters em `infrastructure`.
- Atualizar `docs/sdd/api-contracts.md` se criar novo endpoint.
- Criar testes unitários para o caso de uso.
