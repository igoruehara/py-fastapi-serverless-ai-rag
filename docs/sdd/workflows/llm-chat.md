# Workflow: Chat com LLM

Este workflow documenta o fluxo real de chat direto com OpenAI ou Claude.

## Entrada HTTP

Endpoint:

```http
POST /api/llm/chat
```

Arquivo:

```text
app/api/routes/llm.py
```

O usuário escolhe:

```text
provider = openai | claude
model    = modelo desejado
```

Também é possível enviar:

```text
text
messages
systemPrompt
context
temperature
maxTokens
reasoningEffort
verbosity
```

## Fluxo interno

```text
ChatRequestBody
  -> ChatMessage
  -> ChatUseCase
  -> LlmProviderPort
  -> OpenAiLlmAdapter ou ClaudeLlmAdapter
```

Arquivos envolvidos:

```text
app/api/routes/llm.py
app/domain/entities/llm.py
app/domain/ports/llm.py
app/application/use_cases/chat.py
app/infrastructure/llm/openai_adapter.py
app/infrastructure/llm/anthropic_adapter.py
app/application/container.py
```

## OpenAI

Adapter:

```text
OpenAiLlmAdapter
```

Configuração:

```text
OPENAI_API_KEY
OPENAI_DEFAULT_MODEL
```

API usada no adapter:

```text
client.responses.create(...)
```

Quando `context` existe, ele é incluído nas instruções do modelo.

## Claude

Adapter:

```text
ClaudeLlmAdapter
```

Configuração:

```text
ANTHROPIC_API_KEY
ANTHROPIC_DEFAULT_MODEL
```

API usada no adapter:

```text
client.messages.create(...)
```

Mensagens `system` são convertidas para o campo `system` da API Claude.

## Seleção de modelo

O modelo pode vir do payload:

```json
{
  "provider": "openai",
  "model": "gpt-5.5"
}
```

Se `model` não vier, o caso de uso tenta usar o modelo padrão do provider configurado em `Settings`.

## Erros esperados

HTTP 400:

- Provider não suportado.
- Modelo ausente e sem default configurado.
- Nenhuma mensagem válida enviada.

HTTP 500:

- Chave do provider ausente.
- Erro de configuração do adapter.

## Validações

```powershell
py -3.13 -m compileall app
```

## Pontos de manutenção

- Para adicionar outro provider, crie um adapter que implemente `LlmProviderPort`.
- Registre o provider em `app/application/container.py`.
- Atualize `docs/sdd/api-contracts.md`.
- Não coloque lógica específica de provider dentro de `ChatUseCase`.
