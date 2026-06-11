# Skill: criar-testes

Use esta skill quando a tarefa for criar ou melhorar testes do projeto.

## Objetivo

Adicionar testes úteis sem acoplar a suíte a provedores externos como AWS, OpenAI, Claude ou Milvus.

## Antes de começar

Leia:

- `AGENTS.md`
- `docs/sdd/coding-standards.md`
- `docs/sdd/architecture.md`
- `docs/ai/rules.md`

## Estratégia

Priorize testes unitários em:

- `app/application/use_cases`
- `app/domain/entities`
- funções puras de `app/infrastructure/text`

Evite em teste unitário:

- Chamar OpenAI.
- Chamar Claude.
- Chamar Milvus.
- Chamar AWS.
- Subir Serverless.

Use fakes para ports.

## Estrutura sugerida

```text
tests/
  unit/
    application/
    domain/
    infrastructure/
  integration/
    infrastructure/
```

## Exemplos de testes úteis

### Conversation

- `EnqueueConversationUseCase` valida campos obrigatórios.
- `EnqueueConversationUseCase` chama a porta de fila.
- `conversation_from_payload` aceita camelCase e snake_case.

### LLM

- `ChatUseCase` exige provider suportado.
- `ChatUseCase` exige pelo menos uma mensagem.
- `ChatUseCase` usa modelo padrão quando permitido.

### RAG

- `TextChunker` respeita chunk size e overlap.
- `normalize_extra_fields` converte strings numéricas e booleanas.
- `RagUseCase.add_documents` cria chunks e chama embeddings/vector store.
- `rag_search_options_from_dict` respeita defaults.

## Boas práticas

- Teste comportamento, não implementação interna.
- Use nomes de teste descritivos.
- Mantenha fixtures simples.
- Use fakes explícitos em vez de mocks complexos quando possível.
- Não dependa da ordem de chaves JSON.

## Comandos

Instalar dependências de desenvolvimento:

```powershell
pip install -r requirements-dev.txt
```

Rodar testes:

```powershell
pytest
```

Rodar lint:

```powershell
ruff check .
```

Validação mínima:

```powershell
py -3.13 -m compileall app
```

## Critério de pronto

- Testes passam.
- Não há chamadas externas reais em testes unitários.
- Fakes estão pequenos e legíveis.
- Documentação é atualizada se um novo padrão de teste for introduzido.
